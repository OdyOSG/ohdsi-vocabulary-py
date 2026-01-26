"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_concept():
    """Create a sample Concept for testing."""
    from ohdsi_vocabulary import Concept
    
    return Concept(
        concept_id=140168,
        concept_name="Psoriasis",
        standard_concept="S",
        invalid_reason=None,
        concept_code="9014002",
        domain_id="Condition",
        vocabulary_id="SNOMED",
        concept_class_id="Clinical Finding",
    )


@pytest.fixture
def sample_concept_set_expression(sample_concept):
    """Create a sample ConceptSetExpression for testing."""
    from ohdsi_vocabulary import ConceptSetExpression, ConceptSetItem
    
    return ConceptSetExpression(
        items=[
            ConceptSetItem(
                concept=sample_concept,
                include_descendants=False,
                include_mapped=False,
                is_excluded=False,
            )
        ]
    )
