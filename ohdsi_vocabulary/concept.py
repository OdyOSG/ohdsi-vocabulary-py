"""
Concept model representing a vocabulary concept.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Concept(BaseModel):
    """Represents a vocabulary concept."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        json_encoders={
            int: lambda v: v if v is not None else None,
        }
    )

    concept_id: Optional[int] = Field(None, alias="CONCEPT_ID")
    concept_name: Optional[str] = Field(None, alias="CONCEPT_NAME")
    standard_concept: Optional[str] = Field(None, alias="STANDARD_CONCEPT")
    invalid_reason: Optional[str] = Field(None, alias="INVALID_REASON")
    concept_code: Optional[str] = Field(None, alias="CONCEPT_CODE")
    domain_id: Optional[str] = Field(None, alias="DOMAIN_ID")
    vocabulary_id: Optional[str] = Field(None, alias="VOCABULARY_ID")
    concept_class_id: Optional[str] = Field(None, alias="CONCEPT_CLASS_ID")

    def get_standard_concept(self) -> str:
        """Get standard concept caption."""
        if self.standard_concept is None:
            return "Unknown"
        
        mapping = {
            "N": "Non-Standard",
            "S": "Standard",
            "C": "Classification"
        }
        return mapping.get(self.standard_concept, "Unknown")

    def get_invalid_reason(self) -> str:
        """Get invalid reason caption."""
        if self.invalid_reason is None:
            return "Unknown"
        
        mapping = {
            "V": "Valid",
            "D": "Invalid",
            "U": "Invalid"
        }
        return mapping.get(self.invalid_reason, "Unknown")
    
    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, Concept):
            return False
        return self.concept_id == other.concept_id

    def __hash__(self):
        """Generate hash."""
        return hash(self.concept_id) if self.concept_id is not None else 0
