"""Tests for VocabularyService (mocked database)."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from ohdsi_vocabulary import (
    Concept,
    ConceptSetExpression,
    ConceptSetItem,
    VocabularyService,
)


class TestVocabularyService:
    """Test cases for VocabularyService."""

    def test_vocabulary_service_initialization_with_connection_string(self):
        """Test VocabularyService initialization with connection string."""
        with patch('ohdsi_vocabulary.vocabulary_service.create_engine') as mock_engine:
            mock_engine_instance = MagicMock()
            mock_connection = MagicMock()
            mock_engine_instance.connect.return_value = mock_connection
            mock_engine.return_value = mock_engine_instance
            
            service = VocabularyService(
                connection_string="postgresql://user:pass@host/db",
                vocabulary_schema="vocab"
            )
            
            assert service.vocabulary_schema == "vocab"
            assert service.table_concept == "concept"
            service.close()

    def test_vocabulary_service_initialization_with_engine(self):
        """Test VocabularyService initialization with engine."""
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value = mock_connection
        
        service = VocabularyService(engine=mock_engine, vocabulary_schema="vocab")
        
        assert service.vocabulary_schema == "vocab"
        service.close()

    def test_vocabulary_service_initialization_with_connection(self):
        """Test VocabularyService initialization with connection."""
        mock_connection = MagicMock()
        
        service = VocabularyService(connection=mock_connection, vocabulary_schema="vocab")
        
        assert service.vocabulary_schema == "vocab"
        assert service._connection == mock_connection
        assert service._own_connection is False

    def test_vocabulary_service_initialization_error(self):
        """Test VocabularyService initialization without connection."""
        with pytest.raises(ValueError, match="Must provide one of"):
            VocabularyService(vocabulary_schema="vocab")

    def test_vocabulary_service_context_manager(self):
        """Test VocabularyService as context manager."""
        with patch('ohdsi_vocabulary.vocabulary_service.create_engine') as mock_engine:
            mock_engine_instance = MagicMock()
            mock_connection = MagicMock()
            mock_engine_instance.connect.return_value = mock_connection
            mock_engine.return_value = mock_engine_instance
            
            with VocabularyService(
                connection_string="postgresql://user:pass@host/db"
            ) as service:
                assert service is not None
            
            # Connection should be closed
            mock_connection.close.assert_called_once()

    def test_build_sql_for_expression(self):
        """Test build_sql_for_expression method."""
        mock_connection = MagicMock()
        service = VocabularyService(
            connection=mock_connection,
            vocabulary_schema="vocab",
            table_concept="concept",
            table_concept_ancestor="concept_ancestor",
            table_concept_relationship="concept_relationship",
        )
        
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept)
        expression = ConceptSetExpression(items=[item])
        
        sql = service.build_sql_for_expression(expression)
        
        assert "vocab.concept" in sql.lower()
        assert "@vocabulary_database_schema" not in sql

    def test_get_raw_sql_from_builder(self):
        """Test get_raw_sql_from_builder method."""
        mock_connection = MagicMock()
        service = VocabularyService(connection=mock_connection)
        
        concept = Concept(concept_id=140168)
        item = ConceptSetItem(concept=concept)
        expression = ConceptSetExpression(items=[item])
        
        sql = service.get_raw_sql_from_builder(expression)
        
        assert "@vocabulary_database_schema" in sql
        assert "CONCEPT" in sql

    def test_custom_table_names(self):
        """Test VocabularyService with custom table names."""
        mock_connection = MagicMock()
        service = VocabularyService(
            connection=mock_connection,
            vocabulary_schema="public",
            table_concept="concepts",
            table_concept_ancestor="ancestors",
            table_concept_relationship="relations",
        )
        
        assert service.table_concept == "concepts"
        assert service.table_concept_ancestor == "ancestors"
        assert service.table_concept_relationship == "relations"

    def test_custom_column_names(self):
        """Test VocabularyService with custom column names."""
        mock_connection = MagicMock()
        service = VocabularyService(
            connection=mock_connection,
            col_concept_id="concept_id_custom",
            col_concept_name="concept_name_custom",
        )
        
        assert service.col_concept_id == "concept_id_custom"
        assert service.col_concept_name == "concept_name_custom"
