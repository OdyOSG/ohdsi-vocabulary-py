"""Tests for ConceptSetExpressionQueryBuilder."""

import pytest
from ohdsi_vocabulary import (
    Concept,
    ConceptSetExpression,
    ConceptSetItem,
    ConceptSetExpressionQueryBuilder,
)


class TestConceptSetExpressionQueryBuilder:
    """Test cases for ConceptSetExpressionQueryBuilder."""

    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = ConceptSetExpressionQueryBuilder()
        assert builder.MAX_IN_LENGTH == 1000

    def test_build_simple_expression_query(self):
        """Test building a simple concept set expression query."""
        builder = ConceptSetExpressionQueryBuilder()
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept)
        expression = ConceptSetExpression(items=[item])
        
        sql = builder.build_expression_query(expression)
        
        assert "select concept_id" in sql.lower()
        assert "@vocabulary_database_schema" in sql
        assert "CONCEPT" in sql

    def test_build_expression_with_descendants(self):
        """Test building expression query with descendants."""
        builder = ConceptSetExpressionQueryBuilder()
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept, include_descendants=True)
        expression = ConceptSetExpression(items=[item])
        
        sql = builder.build_expression_query(expression)
        
        assert "CONCEPT_ANCESTOR" in sql
        assert "descendant_concept_id" in sql.lower()
        assert "ancestor_concept_id" in sql.lower()

    def test_build_expression_with_mapped(self):
        """Test building expression query with mapped concepts."""
        builder = ConceptSetExpressionQueryBuilder()
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept, include_mapped=True)
        expression = ConceptSetExpression(items=[item])
        
        sql = builder.build_expression_query(expression)
        
        assert "concept_relationship" in sql.lower()
        assert "Maps to" in sql or "relationship_id" in sql.lower()

    def test_build_expression_with_excluded(self):
        """Test building expression query with excluded concepts."""
        builder = ConceptSetExpressionQueryBuilder()
        concept1 = Concept(concept_id=140168)
        concept2 = Concept(concept_id=140169)
        
        item1 = ConceptSetItem(concept=concept1, is_excluded=False)
        item2 = ConceptSetItem(concept=concept2, is_excluded=True)
        
        expression = ConceptSetExpression(items=[item1, item2])
        
        sql = builder.build_expression_query(expression)
        
        assert "LEFT JOIN" in sql or "EXCLUDE" in sql.upper()
        assert "WHERE" in sql.upper()

    def test_build_expression_empty(self):
        """Test building expression query with empty expression."""
        builder = ConceptSetExpressionQueryBuilder()
        expression = ConceptSetExpression(items=[])
        
        sql = builder.build_expression_query(expression)
        
        assert "0=1" in sql or "where 0=1" in sql.lower()

    def test_build_expression_multiple_concepts(self):
        """Test building expression query with multiple concepts."""
        builder = ConceptSetExpressionQueryBuilder()
        concept1 = Concept(concept_id=140168)
        concept2 = Concept(concept_id=140169)
        
        item1 = ConceptSetItem(concept=concept1)
        item2 = ConceptSetItem(concept=concept2)
        
        expression = ConceptSetExpression(items=[item1, item2])
        
        sql = builder.build_expression_query(expression)
        
        assert "UNION" in sql or "in (" in sql.lower()

    def test_get_concept_ids(self):
        """Test _get_concept_ids method."""
        builder = ConceptSetExpressionQueryBuilder()
        concepts = [
            Concept(concept_id=140168),
            Concept(concept_id=140169),
            Concept(concept_id=None),  # Should be filtered out
        ]
        
        concept_ids = builder._get_concept_ids(concepts)
        
        assert len(concept_ids) == 2
        assert 140168 in concept_ids
        assert 140169 in concept_ids
        assert None not in concept_ids

    def test_split_in_clause(self):
        """Test _split_in_clause method."""
        builder = ConceptSetExpressionQueryBuilder()
        
        # Test with values under limit
        values = [1, 2, 3]
        result = builder._split_in_clause("concept_id", values, 1000)
        assert "concept_id in (1,2,3)" in result
        
        # Test with empty values
        result = builder._split_in_clause("concept_id", [], 1000)
        assert result == ""
