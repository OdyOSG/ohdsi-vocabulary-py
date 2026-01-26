"""
ConceptSetExpression model for concept set definitions.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
import json

from .concept import Concept


class ConceptSetItem(BaseModel):
    """Represents an item in a concept set expression."""

    concept: Concept
    is_excluded: bool = Field(False, alias="isExcluded")
    include_descendants: bool = Field(False, alias="includeDescendants")
    include_mapped: bool = Field(False, alias="includeMapped")

    class Config:
        populate_by_name = True
    
    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, ConceptSetItem):
            return False
        return (
            self.concept == other.concept
            and self.is_excluded == other.is_excluded
            and self.include_descendants == other.include_descendants
            and self.include_mapped == other.include_mapped
        )

    def __hash__(self):
        """Generate hash."""
        return hash(
            (
                self.concept,
                self.is_excluded,
                self.include_descendants,
                self.include_mapped,
            )
        )


class ConceptSetExpression(BaseModel):
    """Represents a concept set expression."""

    items: List[ConceptSetItem] = Field(default_factory=list)

    @classmethod
    def from_json(cls, json_str: str) -> "ConceptSetExpression":
        """Create ConceptSetExpression from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    class Config:
        populate_by_name = True
    
    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, ConceptSetExpression):
            return False
        return self.items == other.items

    def __hash__(self):
        """Generate hash."""
        return hash(tuple(self.items))
