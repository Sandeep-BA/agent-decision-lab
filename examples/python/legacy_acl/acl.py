"""Author: Sandeep Belgavi. An anti-corruption layer between agent tools and a legacy returns back office.

Companion to "An Anti-Corruption Layer for Agent Tools Over a Legacy System" (aicassindra.com). The legacy
client is a fake with the quirks the article describes: one-letter status codes where R means refunded or
rejected depending on an era flag, store-credit amounts in points, a reserve/post/release refund sequence,
and errors returned as codes. The layer exposes one view type and one idempotent refund operation.
No real system, model or network is used.
"""
from dataclasses import dataclass

POINTS_PER_POUND = 200          # store credit: 200 points per pound
PENCE_PER_POUND = 100
PRE_2019_ERA = 'A'
STATUS = {'O': 'open', 'H': 'held', 'X': 'closed'}
RETRYABLE = {'ERR-1042'}        # back office busy


@dataclass(frozen=True)
class ReturnView:
    case_id: str
    status: str
    paid_pence: int
    refunded_pence: int


class UnknownCode(ValueError):
    pass


class RefundRejected(Exception):
    pass


class LegacyError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code
        self.retryable = code in RETRYABLE


def to_view(hdr, era_flag):
    code = hdr['STS']
    if code == 'R':
        status = 'rejected' if era_flag == PRE_2019_ERA else 'refunded'
    elif code in STATUS:
        status = STATUS[code]
    else:
        raise UnknownCode(code)             # never default an unknown code
    refunded = hdr['RFD_AMT']
    if hdr['RFD_MTH'] == 'SC':
        refunded = refunded * PENCE_PER_POUND // POINTS_PER_POUND
    return ReturnView(hdr['CASE'], status, hdr['PAID_AMT'], refunded)


class FakeBackOffice:
    """The legacy system. Postings carry a caller reference; post can time out after recording."""

    def __init__(self):
        self.rows = {}
        self.era = {}
        self.holds = {}
        self.postings = []
        self.fail_post_after_record = False
        self.next_hold = 1

    def add(self, case, sts, paid, refunded=0, method='CARD', era='B'):
        self.rows[case] = dict(CASE=case, STS=sts, PAID_AMT=paid, RFD_AMT=refunded, RFD_MTH=method)
        self.era[case] = era

    def read(self, case):
        if case not in self.rows:
            raise LegacyError('ERR-2001')
        return dict(self.rows[case]), self.era[case]

    def reserve(self, case, amount, ref):
        hold = 'H%d' % self.next_hold
        self.next_hold += 1
        self.holds[hold] = (case, amount, ref)
        return hold

    def post(self, hold, ref):
        if hold not in self.holds:
            raise LegacyError('ERR-3007')    # post without reserve
        case, amount, _ = self.holds[hold]
        posting = dict(case=case, amount=amount, ref=ref, id='P%d' % (len(self.postings) + 1))
        self.postings.append(posting)
        self.rows[case]['RFD_AMT'] += amount
        if self.fail_post_after_record:
            self.fail_post_after_record = False
            raise TimeoutError('post timed out after recording')
        return posting

    def release(self, hold):
        self.holds.pop(hold, None)

    def find_posting(self, ref):
        return next((p for p in self.postings if p['ref'] == ref), None)


class ReturnsLayer:
    """What agent tools call. Translates in both directions and enforces the unwritten invariants."""

    def __init__(self, legacy):
        self.legacy = legacy

    def get_return(self, case_id):
        try:
            hdr, era = self.legacy.read(case_id)
        except LegacyError as e:
            return dict(error='not_found' if e.code == 'ERR-2001' else 'legacy_error', retryable=e.retryable)
        return to_view(hdr, era)

    def refund(self, case_id, amount_pence, key):
        view = self.get_return(case_id)
        if isinstance(view, dict):
            raise RefundRejected(view['error'])
        earlier = self.legacy.find_posting(key)
        if earlier:
            return earlier                        # a retried call that already worked
        if view.status != 'open':
            raise RefundRejected('return is %s, not open' % view.status)
        if amount_pence <= 0 or view.refunded_pence + amount_pence > view.paid_pence:
            raise RefundRejected('refund would exceed the amount paid')
        hold = self.legacy.reserve(case_id, amount_pence, ref=key)
        try:
            return self.legacy.post(hold, ref=key)
        finally:
            self.legacy.release(hold)


def naive_status(hdr):
    """What an agent reading raw codes from a tool description tends to do."""
    return {'O': 'open', 'H': 'held', 'X': 'closed', 'R': 'rejected'}[hdr['STS']]


def demo():
    bo = FakeBackOffice()
    bo.add('CASE-7001', 'R', 2499, 2499, era='B')          # refunded, post-2019
    bo.add('CASE-7002', 'R', 1500, 0, era='A')             # rejected, pre-2019
    bo.add('CASE-7003', 'O', 3000, 0)
    bo.add('CASE-7004', 'H', 1200, 0)
    bo.add('CASE-7005', 'X', 800, 1600, method='SC')        # 1600 points = 800 pence
    layer = ReturnsLayer(bo)
    out = []
    hdr, _ = bo.read('CASE-7001')
    out.append(('naive_7001', naive_status(hdr)))
    out.append(('layer_7001', layer.get_return('CASE-7001').status))
    out.append(('layer_7002', layer.get_return('CASE-7002').status))
    out.append(('store_credit_pence_7005', layer.get_return('CASE-7005').refunded_pence))
    bo.fail_post_after_record = True
    try:
        layer.refund('CASE-7003', 1000, key='CASE-7003:refund:1')
    except TimeoutError:
        out.append(('first_call', 'timeout after recording'))
    again = layer.refund('CASE-7003', 1000, key='CASE-7003:refund:1')
    out.append(('retry_returns', again['id']))
    out.append(('postings_for_7003', sum(1 for p in bo.postings if p['case'] == 'CASE-7003')))
    for case, amount in (('CASE-7004', 500), ('CASE-7003', 2500)):
        try:
            layer.refund(case, amount, key='%s:refund:2' % case)
        except RefundRejected as e:
            out.append(('rejected_' + case, str(e)))
    out.append(('missing_case', layer.get_return('CASE-9999')['error']))
    return out


if __name__ == '__main__':
    for name, value in demo():
        print('%-26s %s' % (name, value))
