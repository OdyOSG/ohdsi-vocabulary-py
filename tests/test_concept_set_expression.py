"""Tests for ConceptSetExpression and ConceptSetItem models."""

import pytest
from pydantic import ValidationError
from ohdsi_vocabulary import Concept, ConceptSetExpression, ConceptSetItem


class TestConceptSetItem:
    """Test cases for ConceptSetItem model."""

    def test_concept_set_item_creation(self):
        """Test creating a ConceptSetItem."""
        concept = Concept(concept_id=140168, concept_name="Psoriasis")
        item = ConceptSetItem(
            concept=concept,
            is_excluded=False,
            include_descendants=True,
            include_mapped=False,
        )
        
        assert item.concept == concept
        assert item.is_excluded is False
        assert item.include_descendants is True
        assert item.include_mapped is False

    def test_concept_set_item_defaults(self):
        """Test ConceptSetItem default values."""
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept)
        
        assert item.is_excluded is False
        assert item.include_descendants is False
        assert item.include_mapped is False

    def test_concept_set_item_equality(self):
        """Test ConceptSetItem equality."""
        concept = Concept(concept_id=140168)
        item1 = ConceptSetItem(concept=concept, include_descendants=True)
        item2 = ConceptSetItem(concept=concept, include_descendants=True)
        item3 = ConceptSetItem(concept=concept, include_descendants=False)
        
        assert item1 == item2
        assert item1 != item3

    def test_concept_set_item_hash(self):
        """Test ConceptSetItem hashing."""
        concept = Concept(concept_id=140168)
        item1 = ConceptSetItem(concept=concept, include_descendants=True)
        item2 = ConceptSetItem(concept=concept, include_descendants=True)
        item3 = ConceptSetItem(concept=concept, include_descendants=False)
        
        assert hash(item1) == hash(item2)
        assert hash(item1) != hash(item3)


class TestConceptSetExpression:
    """Test cases for ConceptSetExpression model."""

    def test_concept_set_expression_creation(self):
        """Test creating a ConceptSetExpression."""
        concept = Concept(concept_id=140168, concept_name="Psoriasis")
        item = ConceptSetItem(concept=concept, include_descendants=True)
        expression = ConceptSetExpression(items=[item])
        
        assert len(expression.items) == 1
        assert expression.items[0] == item

    def test_concept_set_expression_empty(self):
        """Test creating an empty ConceptSetExpression."""
        expression = ConceptSetExpression()
        
        assert len(expression.items) == 0

    def test_concept_set_expression_from_json(self):
        """Test creating ConceptSetExpression from JSON."""
        json_str = """
        {
            "items": [
                {
                    "concept": {
                        "CONCEPT_ID": 140168,
                        "CONCEPT_NAME": "Psoriasis",
                        "DOMAIN_ID": "Condition",
                        "VOCABULARY_ID": "SNOMED"
                    },
                    "isExcluded": false,
                    "includeDescendants": true,
                    "includeMapped": false
                }
            ]
        }
        """
        
        expression = ConceptSetExpression.from_json(json_str)
        
        assert len(expression.items) == 1
        assert expression.items[0].concept.concept_id == 140168
        assert expression.items[0].include_descendants is True

    def test_concept_set_expression_from_json_defaults_missing_item_flags(self):
        """Test missing item flags default to False."""
        json_str = """
        {
            "items": [
                {
                    "concept": {
                        "CONCEPT_ID": 140168,
                        "CONCEPT_NAME": "Psoriasis",
                        "DOMAIN_ID": "Condition",
                        "VOCABULARY_ID": "SNOMED"
                    }
                }
            ]
        }
        """

        expression = ConceptSetExpression.from_json(json_str)

        assert len(expression.items) == 1
        assert expression.items[0].is_excluded is False
        assert expression.items[0].include_descendants is False
        assert expression.items[0].include_mapped is False

    def test_concept_set_expression_validation_errors_use_one_based_item_indexes(self):
        """Test validation error item indexes are displayed starting from 1."""
        with pytest.raises(ValidationError) as error:
            ConceptSetExpression(items=[{}])

        assert error.value.errors()[0]["loc"] == ("items", 1, "concept")
        assert "items.1.concept" in str(error.value)

    def test_concept_set_expression_from_json_errors_use_one_based_item_indexes(self):
        """Test JSON validation error item indexes are displayed starting from 1."""
        json_str = """
        {
            "items": [
                {
                    "concept": {
                        "CONCEPT_ID": 140168
                    }
                },
                {}
            ]
        }
        """

        with pytest.raises(ValidationError) as error:
            ConceptSetExpression.from_json(json_str)

        assert error.value.errors()[0]["loc"] == ("items", 2, "concept")
        assert "items.2.concept" in str(error.value)

    def test_concept_set_expression_equality(self):
        """Test ConceptSetExpression equality."""
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept)
        
        expression1 = ConceptSetExpression(items=[item])
        expression2 = ConceptSetExpression(items=[item])
        expression3 = ConceptSetExpression(items=[])
        
        assert expression1 == expression2
        assert expression1 != expression3

    def test_concept_set_expression_hash(self):
        """Test ConceptSetExpression hashing."""
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept)
        
        expression1 = ConceptSetExpression(items=[item])
        expression2 = ConceptSetExpression(items=[item])
        expression3 = ConceptSetExpression(items=[])
        
        assert hash(expression1) == hash(expression2)
        assert hash(expression1) != hash(expression3)
