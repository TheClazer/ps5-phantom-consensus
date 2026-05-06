"""Representative data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Representative:
    """Represents a representative in the consensus system."""
    id: str
    name: str
    faction: str
    influence: float
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Representative):
            return False
        return self.id == other.id
