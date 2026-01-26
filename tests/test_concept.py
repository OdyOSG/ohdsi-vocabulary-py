"""Tests for Concept model."""

import pytest
from ohdsi_vocabulary import Concept


class TestConcept:
    """Test cases for Concept model."""

    def test_concept_creation(self):
        """Test creating a Concept with all fields."""
        concept = Concept(
            concept_id=140168,
            concept_name="Psoriasis",
            standard_concept="S",
            invalid_reason=None,
            concept_code="9014002",
            domain_id="Condition",
            vocabulary_id="SNOMED",
            concept_class_id="Clinical Finding",
        )
        
        assert concept.concept_id == 140168
        assert concept.concept_name == "Psoriasis"
        assert concept.standard_concept == "S"
        assert concept.invalid_reason is None
        assert concept.concept_code == "9014002"
        assert concept.domain_id == "Condition"
        assert concept.vocabulary_id == "SNOMED"
        assert concept.concept_class_id == "Clinical Finding"

    def test_concept_creation_minimal(self):
        """Test creating a Concept with minimal fields."""
        concept = Concept(concept_id=140168)
        
        assert concept.concept_id == 140168
        assert concept.concept_name is None

    def test_concept_equality(self):
        """Test concept equality."""
        concept1 = Concept(concept_id=140168, concept_name="Psoriasis")
        concept2 = Concept(concept_id=140168, concept_name="Psoriasis")
        concept3 = Concept(concept_id=140169, concept_name="Psoriasis")
        
        assert concept1 == concept2
        assert concept1 != concept3

    def test_concept_hash(self):
        """Test concept hashing."""
        concept1 = Concept(concept_id=140168)
        concept2 = Concept(concept_id=140168)
        concept3 = Concept(concept_id=140169)
        
        assert hash(concept1) == hash(concept2)
        assert hash(concept1) != hash(concept3)

    def test_concept_get_standard_concept(self):
        """Test get_standard_concept method."""
        concept_s = Concept(standard_concept="S")
        concept_n = Concept(standard_concept="N")
        concept_c = Concept(standard_concept="C")
        concept_none = Concept(standard_concept=None)
        concept_unknown = Concept(standard_concept="X")
        
        assert concept_s.get_standard_concept() == "Standard"
        assert concept_n.get_standard_concept() == "Non-Standard"
        assert concept_c.get_standard_concept() == "Classification"
        assert concept_none.get_standard_concept() == "Unknown"
        assert concept_unknown.get_standard_concept() == "Unknown"

    def test_concept_get_invalid_reason(self):
        """Test get_invalid_reason method."""
        concept_v = Concept(invalid_reason="V")
        concept_d = Concept(invalid_reason="D")
        concept_u = Concept(invalid_reason="U")
        concept_none = Concept(invalid_reason=None)
        concept_unknown = Concept(invalid_reason="X")
        
        assert concept_v.get_invalid_reason() == "Valid"
        assert concept_d.get_invalid_reason() == "Invalid"
        assert concept_u.get_invalid_reason() == "Invalid"
        assert concept_none.get_invalid_reason() == "Unknown"
        assert concept_unknown.get_invalid_reason() == "Unknown"

    def test_concept_frozen(self):
        """Test that Concept is frozen (immutable)."""
        concept = Concept(concept_id=140168)
        
        with pytest.raises(Exception):  # Pydantic validation error
            concept.concept_id = 140169
