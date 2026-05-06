"""Proposal data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Proposal:
    """Represents a proposal in the consensus system."""
    id: str
    title: str
    sponsor_id: str
    priority: float
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Proposal):
            return False
        return self.id == other.id
