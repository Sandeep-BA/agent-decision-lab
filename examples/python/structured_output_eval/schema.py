"""The extraction schema and a small validator for exactly this schema. Author: Sandeep Belgavi."""
import re

CASE_TYPES = ['return', 'refund', 'late_delivery', 'damaged_item', 'address_change', 'other']
SCHEMA = {
    'type': 'object',
    'properties': {
        'case_type': {'type': 'string', 'enum': CASE_TYPES},
        'order_id': {'type': ['string', 'null'], 'pattern': '^BK-[0-9]{5}$'},
        'amount_inr': {'type': ['number', 'null']},
        'wants_person': {'type': 'boolean'},
    },
    'required': ['case_type', 'order_id', 'amount_inr', 'wants_person'],
    'additionalProperties': False,
}
FIELDS = SCHEMA['required']


def problems(obj):
    """Schema violations as short strings; an empty list means valid."""
    if not isinstance(obj, dict):
        return ['not an object']
    out = ['missing ' + f for f in FIELDS if f not in obj]
    out += ['extra ' + k for k in obj if k not in SCHEMA['properties']]
    if 'case_type' in obj and obj['case_type'] not in CASE_TYPES:
        out.append('case_type not in enum')
    oid = obj.get('order_id', None)
    if 'order_id' in obj and oid is not None and not (isinstance(oid, str) and re.fullmatch(r'BK-[0-9]{5}', oid)):
        out.append('order_id pattern')
    amt = obj.get('amount_inr', None)
    if 'amount_inr' in obj and amt is not None and (isinstance(amt, bool) or not isinstance(amt, (int, float))):
        out.append('amount_inr type')
    if 'wants_person' in obj and not isinstance(obj['wants_person'], bool):
        out.append('wants_person type')
    return out
