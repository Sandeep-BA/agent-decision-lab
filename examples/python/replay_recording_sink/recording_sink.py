# Author: Sandeep Belgavi. Small offline recording boundary.
from dataclasses import dataclass

@dataclass(frozen=True)
class Proposal:
    case_id: str
    expected_revision: int
    new_value: str

class RecordingSink:
    def __init__(self):
        self.proposals = []

    def submit(self, proposal):
        if not isinstance(proposal, Proposal):
            raise TypeError("typed proposal required")
        if proposal.expected_revision < 0:
            raise ValueError("revision must be nonnegative")
        self.proposals.append(proposal)
        return {"recorded": True, "executed": False}
