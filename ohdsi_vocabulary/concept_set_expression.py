"""
ConceptSetExpression model for concept set definitions.
"""

import json
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .concept import Concept


def _one_based_item_error_locations(error: ValidationError) -> ValidationError:
    """Return a validation error with item indexes shifted for display."""
    errors = []
    for item in error.errors():
        loc = item.get("loc")
        if isinstance(loc, tuple):
            loc = tuple(
                part + 1
                if isinstance(part, int) and index > 0 and loc[index - 1] == "items"
                else part
                for index, part in enumerate(loc)
            )
            item = {**item, "loc": loc}
        errors.append(item)

    return ValidationError.from_exception_data(error.title, errors)


class ConceptSetItem(BaseModel):
    """Represents an item in a concept set expression."""

    model_config = ConfigDict(populate_by_name=True)

    concept: Concept
    is_excluded: bool = Field(False, alias="isExcluded")
    include_descendants: bool = Field(False, alias="includeDescendants")
    include_mapped: bool = Field(False, alias="includeMapped")
    
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

    model_config = ConfigDict(populate_by_name=True)

    items: List[ConceptSetItem] = Field(default_factory=list)

    def __init__(self, **data: Any):
        try:
            super().__init__(**data)
        except ValidationError as error:
            raise _one_based_item_error_locations(error) from None

    @classmethod
    def from_json(cls, json_str: str) -> "ConceptSetExpression":
        """Create ConceptSetExpression from JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, ConceptSetExpression):
            return False
        return self.items == other.items

    def __hash__(self):
        """Generate hash."""
        return hash(tuple(self.items))
