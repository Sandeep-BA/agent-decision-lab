"""TCP retransmission timeout per RFC 6298. Author: Sandeep Belgavi.

Implements sections 2, 3 and 5 of RFC 6298: the initial RTO of 1 second, the
first-sample and subsequent-sample updates (RTTVAR before SRTT, alpha 1/8,
beta 1/4, K 4), the clock-granularity term G, the 1 second floor (a SHOULD),
the optional maximum of at least 60 seconds, doubling on timer expiry, the
3 second re-initialisation after a lost SYN (rule 5.7) and Karn's rule. The
`floor` argument exists only to show what the formulas do without the floor;
RFC 6298 recommends 1 second. Times are seconds; the RTT series is synthetic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json

ALPHA, BETA, K = 1 / 8, 1 / 4, 4


@dataclass
class RtoEstimator:
    granularity: float = 0.001        # G: assume a 1 ms clock
    floor: float = 1.0                # rule 2.4
    ceiling: float = 60.0             # rule 2.5 allows any maximum >= 60 s
    srtt: float | None = None
    rttvar: float | None = None
    rto: float = 1.0                  # rule 2.1
    log: list = field(default_factory=list)

    def _clamp(self, value: float) -> float:
        return min(self.ceiling, max(self.floor, value))

    def sample(self, r: float, retransmitted: bool = False, timestamps: bool = False) -> bool:
        """Feed one RTT measurement; returns False when Karn's rule discards it."""
        if retransmitted and not timestamps:
            self.log.append(f'discard {r:.3f}s: segment was retransmitted (Karn)')
            return False
        if self.srtt is None:
            self.srtt, self.rttvar = r, r / 2                                   # rule 2.2
        else:
            self.rttvar = (1 - BETA) * self.rttvar + BETA * abs(self.srtt - r)  # rule 2.3, first
            self.srtt = (1 - ALPHA) * self.srtt + ALPHA * r                    # then SRTT
        raw = self.srtt + max(self.granularity, K * self.rttvar)
        self.rto = self._clamp(raw)
        self.log.append(f'sample {r:.3f}s -> SRTT {self.srtt:.4f} RTTVAR {self.rttvar:.4f} raw {raw:.4f} RTO {self.rto:.3f}')
        return True

    def expire(self) -> float:
        """Timer expired: retransmit and back off (rule 5.5)."""
        self.rto = min(self.ceiling, self.rto * 2)
        self.log.append(f'timeout -> RTO {self.rto:.3f}')
        return self.rto

    def syn_timed_out_then_established(self) -> None:
        """Rule 5.7: after a lost SYN, start data transfer with RTO of at least 3 s."""
        if self.rto < 3.0:
            self.rto = 3.0
        self.log.append(f'SYN was retransmitted -> RTO {self.rto:.3f} for data')


SERIES = [0.100] * 8 + [0.400, 0.420, 0.380] + [0.100] * 6      # short path with a spike
SERIES_LONG = [0.300] * 8 + [0.900, 0.950, 0.850] + [0.300] * 6  # longer path with a spike


def trace(floor: float, series: list[float] = SERIES) -> list[tuple[float, float]]:
    est = RtoEstimator(floor=floor)
    out = []
    for r in series:
        est.sample(r)
        out.append((r, round(est.rto, 4)))
    return out


def karn_demo() -> dict:
    """Original send at t=0, ACK arrives at 1.25 s, but the segment was retransmitted at t=1.0."""
    careful, naive = RtoEstimator(floor=0.2), RtoEstimator(floor=0.2)
    for est in (careful, naive):
        est.sample(0.100)
        est.expire()
    careful.sample(0.25, retransmitted=True)    # ambiguous: from the original (1.25 s) or the copy (0.25 s)?
    naive.sample(0.25)                          # assumes the copy was acknowledged
    return {'careful_rto': round(careful.rto, 4), 'naive_srtt': round(naive.srtt, 4), 'naive_rto': round(naive.rto, 4)}


def run() -> dict:
    est = RtoEstimator()
    backoff = [est.rto] + [est.expire() for _ in range(7)]
    return {'rfc_floor_1s': trace(1.0), 'no_floor_0_2s': trace(0.2), 'long_path_rfc_floor': trace(1.0, SERIES_LONG),
            'backoff_from_initial': backoff,
            'karn': karn_demo()}


if __name__ == '__main__':
    print(json.dumps(run(), indent=1))
