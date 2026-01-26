"""
VocabularyService for resolving concept set expressions and looking up concepts.
"""

from typing import List, Optional, Tuple, Union

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.pool import NullPool

from .concept import Concept
from .concept_set_expression import ConceptSetExpression
from .concept_set_expression_query_builder import ConceptSetExpressionQueryBuilder


class VocabularyService:
    """
    Service for vocabulary operations including resolving concept set expressions
    and looking up concepts.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        engine: Optional[Engine] = None,
        vocabulary_schema: str = "vocab",
        connection: Optional[Connection] = None,
        # Table names
        table_concept: str = "concept",
        table_concept_ancestor: str = "concept_ancestor",
        table_concept_relationship: str = "concept_relationship",
        # Concept table columns
        col_concept_id: str = "concept_id",
        col_concept_name: str = "concept_name",
        col_standard_concept: str = "standard_concept",
        col_invalid_reason: str = "invalid_reason",
        col_concept_code: str = "concept_code",
        col_domain_id: str = "domain_id",
        col_vocabulary_id: str = "vocabulary_id",
        col_concept_class_id: str = "concept_class_id",
        # Concept ancestor table columns
        col_ancestor_concept_id: str = "ancestor_concept_id",
        col_descendant_concept_id: str = "descendant_concept_id",
        # Concept relationship table columns
        col_concept_id_1: str = "concept_id_1",
        col_concept_id_2: str = "concept_id_2",
        col_relationship_id: str = "relationship_id",
    ):
        """
        Initialize VocabularyService.

        Args:
            connection_string: SQLAlchemy connection string (e.g., "postgresql://user:pass@host/db")
            engine: SQLAlchemy Engine instance (alternative to connection_string)
            vocabulary_schema: Schema name where vocabulary tables are located
            connection: SQLAlchemy Connection instance (alternative to connection_string/engine)
            table_concept: Name of the concept table (default: "concept")
            table_concept_ancestor: Name of the concept_ancestor table (default: "concept_ancestor")
            table_concept_relationship: Name of the concept_relationship table (default: "concept_relationship")
            col_concept_id: Column name for concept_id (default: "concept_id")
            col_concept_name: Column name for concept_name (default: "concept_name")
            col_standard_concept: Column name for standard_concept (default: "standard_concept")
            col_invalid_reason: Column name for invalid_reason (default: "invalid_reason")
            col_concept_code: Column name for concept_code (default: "concept_code")
            col_domain_id: Column name for domain_id (default: "domain_id")
            col_vocabulary_id: Column name for vocabulary_id (default: "vocabulary_id")
            col_concept_class_id: Column name for concept_class_id (default: "concept_class_id")
            col_ancestor_concept_id: Column name for ancestor_concept_id (default: "ancestor_concept_id")
            col_descendant_concept_id: Column name for descendant_concept_id (default: "descendant_concept_id")
            col_concept_id_1: Column name for concept_id_1 (default: "concept_id_1")
            col_concept_id_2: Column name for concept_id_2 (default: "concept_id_2")
            col_relationship_id: Column name for relationship_id (default: "relationship_id")
        """
        if connection is not None:
            self._connection = connection
            self._own_connection = False
        elif engine is not None:
            self._connection = engine.connect()
            self._own_connection = True
        elif connection_string is not None:
            engine = create_engine(connection_string, poolclass=NullPool)
            self._connection = engine.connect()
            self._own_connection = True
        else:
            raise ValueError(
                "Must provide one of: connection_string, engine, or connection"
            )

        self.vocabulary_schema = vocabulary_schema

        # Store table names
        self.table_concept = table_concept
        self.table_concept_ancestor = table_concept_ancestor
        self.table_concept_relationship = table_concept_relationship

        # Store column names
        self.col_concept_id = col_concept_id
        self.col_concept_name = col_concept_name
        self.col_standard_concept = col_standard_concept
        self.col_invalid_reason = col_invalid_reason
        self.col_concept_code = col_concept_code
        self.col_domain_id = col_domain_id
        self.col_vocabulary_id = col_vocabulary_id
        self.col_concept_class_id = col_concept_class_id
        self.col_ancestor_concept_id = col_ancestor_concept_id
        self.col_descendant_concept_id = col_descendant_concept_id
        self.col_concept_id_1 = col_concept_id_1
        self.col_concept_id_2 = col_concept_id_2
        self.col_relationship_id = col_relationship_id

        self.query_builder = ConceptSetExpressionQueryBuilder()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection if we own it."""
        if self._own_connection:
            self._connection.close()

    def close(self):
        """Close the database connection if we own it."""
        if self._own_connection:
            self._connection.close()

    def get_raw_sql_from_builder(self, expression: ConceptSetExpression) -> str:
        """
        Get the raw SQL from the query builder before any replacements.
        Useful for debugging.
        """
        return self.query_builder.build_expression_query(expression)

    def build_sql_for_expression(self, expression: ConceptSetExpression) -> str:
        """
        Build the SQL query for a concept set expression (for debugging).

        Args:
            expression: The ConceptSetExpression to build SQL for

        Returns:
            The generated SQL query string
        """
        # Build the SQL query using the query builder
        sql = self.query_builder.build_expression_query(expression)

        # Replace table names - handle both with and without schema prefix
        # IMPORTANT: Replace longer patterns first to avoid partial matches

        # First, replace full patterns with schema (before schema replacement)
        sql = sql.replace(
            "@vocabulary_database_schema.CONCEPT_ANCESTOR",
            f"{self.vocabulary_schema}.{self.table_concept_ancestor}",
        )
        sql = sql.replace(
            "@vocabulary_database_schema.CONCEPT",
            f"{self.vocabulary_schema}.{self.table_concept}",
        )
        sql = sql.replace(
            "@vocabulary_database_schema.concept_relationship",
            f"{self.vocabulary_schema}.{self.table_concept_relationship}",
        )

        # Replace the schema placeholder (for any remaining occurrences)
        sql = sql.replace("@vocabulary_database_schema", self.vocabulary_schema)

        # Now handle table names that might have schema already replaced
        # Replace longer patterns first (CONCEPT_ANCESTOR before CONCEPT)
        # This handles cases like "public.CONCEPT_ANCESTOR" -> "public.ancestors"
        schema_prefix = f"{self.vocabulary_schema}."
        sql = sql.replace(
            f"{schema_prefix}CONCEPT_ANCESTOR",
            f"{schema_prefix}{self.table_concept_ancestor}",
        )
        sql = sql.replace(
            f"{schema_prefix}CONCEPT", f"{schema_prefix}{self.table_concept}"
        )

        # Handle any remaining standalone table references (without schema)
        sql = sql.replace("CONCEPT_ANCESTOR", self.table_concept_ancestor)
        sql = sql.replace("CONCEPT", self.table_concept)
        sql = sql.replace("concept_relationship", self.table_concept_relationship)

        # Replace column names - order matters! Replace specific patterns first
        # Relationship table columns
        sql = sql.replace("cr.concept_id_1", f"cr.{self.col_concept_id_1}")
        sql = sql.replace("cr.concept_id_2", f"cr.{self.col_concept_id_2}")
        sql = sql.replace("cr.relationship_id", f"cr.{self.col_relationship_id}")
        # Note: relationship table doesn't have invalid_reason column
        # Ancestor table columns - use temporary placeholders to avoid substring replacement issues
        # Replace with placeholders first
        sql = sql.replace(
            "ca.descendant_concept_id", "ca.__TEMP_DESCENDANT_CONCEPT_ID__"
        )
        sql = sql.replace("ca.ancestor_concept_id", "ca.__TEMP_ANCESTOR_CONCEPT_ID__")
        # Concept table columns (aliased)
        sql = sql.replace("c.concept_id", f"c.{self.col_concept_id}")
        sql = sql.replace("c.invalid_reason", f"c.{self.col_invalid_reason}")
        # Subquery aliases
        sql = sql.replace("I.concept_id", f"I.{self.col_concept_id}")
        sql = sql.replace("E.concept_id", f"E.{self.col_concept_id}")
        sql = sql.replace("C.concept_id", f"C.{self.col_concept_id}")
        sql = sql.replace("C.invalid_reason", f"C.{self.col_invalid_reason}")
        # Standalone invalid_reason (must be after all specific patterns)
        sql = sql.replace("invalid_reason", self.col_invalid_reason)
        # Standalone concept_id (must be last to avoid replacing parts of other column names)
        sql = sql.replace("concept_id", self.col_concept_id)
        # Now restore the ancestor table columns from placeholders
        sql = sql.replace(
            "ca.__TEMP_DESCENDANT_CONCEPT_ID__", f"ca.{self.col_descendant_concept_id}"
        )
        sql = sql.replace(
            "ca.__TEMP_ANCESTOR_CONCEPT_ID__", f"ca.{self.col_ancestor_concept_id}"
        )

        return sql

    def resolve_concept_set_expression(
        self, expression: ConceptSetExpression
    ) -> List[int]:
        """
        Resolve a concept set expression to a list of included concept IDs.

        This method:
        - Includes concepts specified in the expression
        - Expands descendants if includeDescendants is true
        - Includes mapped concepts if includeMapped is true
        - Excludes concepts marked as excluded

        Args:
            expression: The ConceptSetExpression to resolve

        Returns:
            List of concept IDs (integers) that are included in the resolved concept set
        """
        # Build and prepare the SQL query
        sql = self.build_sql_for_expression(expression)

        # Validate SQL contains expected elements (for debugging)
        # Only check for ancestors table if descendants are actually being used
        uses_descendants = any(
            item.include_descendants
            for item in expression.items
            if not item.is_excluded
        )

        if uses_descendants and self.table_concept_ancestor not in sql.lower():
            raise ValueError(
                f"Generated SQL should contain ancestors table '{self.table_concept_ancestor}' when descendants are used. SQL: {sql[:500]}"
            )

        # Execute the query
        result = self._connection.execute(text(sql))

        # Consume all results - in SQLAlchemy 2.0, we can use scalars() for single column
        # or iterate directly. Try multiple approaches to ensure we get all rows.
        try:
            # Try scalars() first (most efficient for single column)
            concept_ids = list(result.scalars().all())
        except (AttributeError, TypeError):
            # Fallback: iterate over rows
            try:
                # Try fetchall() if available
                rows = result.fetchall()
                concept_ids = [row[0] for row in rows]
            except AttributeError:
                # Final fallback: iterate directly
                concept_ids = [row[0] for row in result]

        return concept_ids

    def lookup_concepts(self, concept_ids: List[int]) -> List[Concept]:
        """
        Look up full concept details for a list of concept IDs.

        This is equivalent to executeIdentifierLookup in WebAPI VocabularyService.

        Args:
            concept_ids: List of concept IDs to look up

        Returns:
            List of Concept objects with full details
        """
        if not concept_ids:
            return []

        # Build query with IN clause, handling Oracle limitation
        # Split into chunks of 1000 if needed
        all_concepts = []
        chunk_size = 1000

        for i in range(0, len(concept_ids), chunk_size):
            chunk = concept_ids[i : i + chunk_size]
            # Use tuple for IN clause - SQLAlchemy will handle parameterization
            placeholders = ",".join([":id" + str(j) for j in range(len(chunk))])

            sql = text(
                f"""
                SELECT 
                    {self.col_concept_id},
                    {self.col_concept_name},
                    {self.col_standard_concept},
                    {self.col_invalid_reason},
                    {self.col_concept_code},
                    {self.col_domain_id},
                    {self.col_vocabulary_id},
                    {self.col_concept_class_id}
                FROM {self.vocabulary_schema}.{self.table_concept}
                WHERE {self.col_concept_id} IN ({placeholders})
            """
            )

            # Create parameter dict
            params = {f"id{j}": chunk[j] for j in range(len(chunk))}

            result = self._connection.execute(sql, params)

            for row in result:
                concept = Concept(
                    concept_id=row[0],
                    concept_name=row[1],
                    standard_concept=row[2],
                    invalid_reason=row[3],
                    concept_code=row[4],
                    domain_id=row[5],
                    vocabulary_id=row[6],
                    concept_class_id=row[7],
                )
                all_concepts.append(concept)

        return all_concepts

    def lookup_mapped_concepts(self, concept_ids: List[int], debug: bool = False) -> List[Concept]:
        """
        Look up source concepts that map to the given concept IDs.
        
        This implements the same logic as WebAPI's executeMappedLookup (getMappedSourcecodes.sql).
        It returns a UNION of:
        1. The concepts themselves (from the identifiers)
        2. Source concepts that map to them (via concept_relationship where relationship_id = 'Maps to')
        3. Source codes from SOURCE_TO_CONCEPT_MAP (skipped for now as table may not exist)
        
        This is equivalent to executeMappedLookup in WebAPI VocabularyService.

        Args:
            concept_ids: List of concept IDs to find mapped source concepts for
            debug: If True, print intermediate steps and debugging information (default: False)

        Returns:
            List of Concept objects representing:
            - The input concepts themselves
            - All source concepts that map to them via 'Maps to' relationship
        """
        if not concept_ids:
            return []

        # Build query matching WebAPI's getMappedSourcecodes.sql
        # It does a UNION of:
        # 1. The concepts themselves (from identifiers)
        # 2. Source concepts that map to them (via concept_relationship)
        # 3. Source codes from SOURCE_TO_CONCEPT_MAP (we'll skip for now)
        all_concepts = []
        chunk_size = 1000
        seen_concept_ids = set()  # To deduplicate across UNION parts

        for i in range(0, len(concept_ids), chunk_size):
            chunk = concept_ids[i : i + chunk_size]
            placeholders = ",".join([":id" + str(j) for j in range(len(chunk))])

            # Match WebAPI's getMappedSourcecodes.sql structure
            # Note: Column order must match Concept model: concept_id, concept_name, standard_concept, invalid_reason, concept_code, domain_id, vocabulary_id, concept_class_id
            # Note: Keep NULL values as NULL (no COALESCE) to preserve actual database values
            sql = text(
                f"""
                -- Part 1: Get the concepts themselves
                SELECT DISTINCT
                    {self.col_concept_id},
                    {self.col_concept_name},
                    {self.col_standard_concept},
                    {self.col_invalid_reason},
                    {self.col_concept_code},
                    {self.col_domain_id},
                    {self.col_vocabulary_id},
                    {self.col_concept_class_id}
                FROM {self.vocabulary_schema}.{self.table_concept}
                WHERE {self.col_concept_id} IN ({placeholders})
                
                UNION
                
                -- Part 2: Get source concepts that map to the provided concepts
                SELECT DISTINCT
                    c1.{self.col_concept_id},
                    c1.{self.col_concept_name},
                    c1.{self.col_standard_concept},
                    c1.{self.col_invalid_reason},
                    c1.{self.col_concept_code},
                    c1.{self.col_domain_id},
                    c1.{self.col_vocabulary_id},
                    c1.{self.col_concept_class_id}
                FROM {self.vocabulary_schema}.{self.table_concept_relationship} cr
                JOIN {self.vocabulary_schema}.{self.table_concept} c1 ON cr.{self.col_concept_id_1} = c1.{self.col_concept_id}
                WHERE cr.{self.col_concept_id_2} IN ({placeholders})
                    AND cr.{self.col_relationship_id} = 'Maps to'
                    AND cr.{self.col_invalid_reason} IS NULL
            """
            )

            # Create parameter dict
            params = {f"id{j}": chunk[j] for j in range(len(chunk))}

            # Debug: print SQL for first chunk
            if debug and i == 0:
                print("=" * 80)
                print("LOOKUP_MAPPED_CONCEPTS SQL (first chunk):")
                print("=" * 80)
                print(sql)
                print(f"Parameters: {params}")
                print("=" * 80)
                print()

            result = self._connection.execute(sql, params)

            chunk_count = 0
            for row in result:
                concept_id = row[0]
                # Deduplicate by concept_id across chunks and UNION parts
                if concept_id not in seen_concept_ids:
                    seen_concept_ids.add(concept_id)
                    # invalid_reason is returned as-is (NULL for valid concepts)
                    concept = Concept(
                        concept_id=concept_id,
                        concept_name=row[1],
                        standard_concept=row[2],
                        invalid_reason=row[3],  # NULL for valid, 'U'/'D' etc for invalid
                        concept_code=row[4],
                        concept_class_id=row[5],
                        domain_id=row[6],
                        vocabulary_id=row[7],
                    )
                    all_concepts.append(concept)
                    chunk_count += 1

            # Debug: print count for each chunk
            if debug and i == 0:
                print(f"First chunk returned {chunk_count} concepts")
                print()

        if debug:
            print(f"Total mapped concepts found (before filtering): {len(all_concepts)}")
            
            # Count invalid_reason values for debugging
            invalid_reason_counts = {}
            for concept in all_concepts:
                ir = concept.invalid_reason if concept.invalid_reason is not None else 'NULL'
                invalid_reason_counts[ir] = invalid_reason_counts.get(ir, 0) + 1
            print(f"Invalid_reason distribution: {invalid_reason_counts}")
        
        # Filter out invalid concepts (invalid_reason IS NOT NULL)
        # In the new database, valid concepts have invalid_reason IS NULL
        valid_concepts = [
            concept for concept in all_concepts 
            if concept.invalid_reason is None
        ]
        
        if debug:
            print(f"Total valid concepts (after filtering invalid_reason IS NULL): {len(valid_concepts)}")
            print()
        return valid_concepts

    def get_included_source_codes(self, concept_ids: List[int], debug: bool = False) -> List[str]:
        """
        Get all source codes (concept_code) that map to the included concept IDs.

        This finds all source concepts (via 'Maps to' relationship) that map to the
        included concepts, and returns their concept_code values.
        
        Behavior:
        - When include_mapped=True: The mapped concepts are already in concept_ids,
          so we get source codes from both the included concepts AND their mappings
        - When include_mapped=False: We find all source concepts that map to the
          included (standard) concepts
        
        For example:
        - If include_mapped=True and include_descendants=False: 
          concept_ids includes mapped concepts, so we get their codes directly
        - If include_descendants=True and include_mapped=False:
          concept_ids has 82 standard concepts, we find ~347 source codes that map to them

        Args:
            concept_ids: List of included concept IDs (from resolve_concept_set_expression)
            debug: If True, print intermediate steps and debugging information (default: False)

        Returns:
            List of source code strings (concept_code values) that map to the included concepts
        """
        if not concept_ids:
            return []

        # Find all source concepts that map to the included concepts
        # This will find source codes for both:
        # 1. The included concepts themselves (if they're source concepts)
        # 2. Other source concepts that map to the included concepts
        mapped_concepts = self.lookup_mapped_concepts(concept_ids, debug=debug)

        if debug:
            print(f"get_included_source_codes: Received {len(mapped_concepts)} mapped concepts")
        
        # Extract source codes (concept_code values) - one per concept, no deduplication
        source_codes = [
            concept.concept_code for concept in mapped_concepts if concept.concept_code
        ]
        
        if debug:
            concepts_without_code = [
                concept.concept_id for concept in mapped_concepts if not concept.concept_code
            ]
            if concepts_without_code:
                print(f"  Warning: {len(concepts_without_code)} concepts have no concept_code: {concepts_without_code[:10]}")
            
            print(f"  Source codes extracted: {len(source_codes)} (one per concept, no deduplication)")
            print()
        
        # Return all source codes (one per concept, preserving order)
        return source_codes

    def get_included_source_codes_with_details(
        self, concept_ids: List[int]
    ) -> List[dict]:
        """
        Get all source codes with full details that map to the included concept IDs.

        This finds all source concepts (via 'Maps to' relationship) that map to the
        included concepts, and returns their details.

        Args:
            concept_ids: List of included concept IDs (from resolve_concept_set_expression)

        Returns:
            List of dictionaries with source code details:
            {
                "concept_id": int,
                "concept_code": str,
                "vocabulary_id": str,
                "concept_name": str,
                "standard_concept": str,
            }
        """
        if not concept_ids:
            return []

        # Find all source concepts that map to the included concepts
        mapped_concepts = self.lookup_mapped_concepts(concept_ids)

        # Extract source codes with ALL details - one per concept, no deduplication
        source_codes = [
            {
                "concept_id": concept.concept_id,
                "concept_name": concept.concept_name,
                "standard_concept": concept.standard_concept,
                "invalid_reason": concept.invalid_reason,
                "concept_code": concept.concept_code,
                "domain_id": concept.domain_id,
                "vocabulary_id": concept.vocabulary_id,
                "concept_class_id": concept.concept_class_id,
            }
            for concept in mapped_concepts
            if concept.concept_code
        ]

        # Return all source codes (one per concept, no deduplication by concept_code)
        return source_codes

    def get_included_concepts_and_source_codes(
        self, expression: ConceptSetExpression, debug: bool = False
    ) -> Tuple[List[Concept], List[Concept]]:
        """
        Get both included concepts and included source codes as separate lists.
        
        This method:
        1. Resolves the concept set expression to get included concept IDs
        2. Looks up full concept details for the included concepts
        3. Looks up mapped source concepts (source codes) for the included concepts
        4. Returns both as separate lists
        
        Args:
            expression: The ConceptSetExpression to resolve
            debug: If True, print intermediate steps and debugging information (default: False)
            
        Returns:
            Tuple of (included_concepts, included_source_codes) where:
            - included_concepts: List of Concept objects from resolving the expression
            - included_source_codes: List of Concept objects representing mapped source codes
        """
        if debug:
            print("=" * 80)
            print("GET_INCLUDED_CONCEPTS_AND_SOURCE_CODES")
            print("=" * 80)
            print(f"Expression items: {len(expression.items)}")
            for idx, item in enumerate(expression.items):
                print(f"  Item {idx + 1}: concept_id={item.concept.concept_id}, "
                      f"include_descendants={item.include_descendants}, "
                      f"include_mapped={item.include_mapped}, "
                      f"is_excluded={item.is_excluded}")
            print()
        
        # Step 1: Resolve the concept set expression to get included concept IDs
        if debug:
            print("Step 1: Resolving concept set expression...")
        
        included_concept_ids = self.resolve_concept_set_expression(expression)
        
        if debug:
            print(f"  Found {len(included_concept_ids)} included concept IDs")
            if included_concept_ids:
                print(f"  First 10 IDs: {included_concept_ids[:10]}")
            print()
        
        if not included_concept_ids:
            if debug:
                print("  No included concepts found, returning empty lists")
                print()
            return [], []
        
        # Check if include_mapped is True in the expression
        has_include_mapped = any(
            item.include_mapped and not item.is_excluded
            for item in expression.items
        )
        
        if debug:
            print(f"Expression has include_mapped=True: {has_include_mapped}")
            print()
        
        # Step 2: Look up full concept details for the included concepts
        if debug:
            print("Step 2: Looking up full concept details for included concepts...")
        
        included_concepts_raw = self.lookup_concepts(included_concept_ids)
        
        if debug:
            print(f"  Retrieved {len(included_concepts_raw)} included concept objects (before filtering)")
            # Count invalid_reason distribution
            invalid_reason_counts = {}
            for concept in included_concepts_raw:
                ir = concept.invalid_reason if concept.invalid_reason is not None else 'NULL'
                invalid_reason_counts[ir] = invalid_reason_counts.get(ir, 0) + 1
            print(f"  Invalid_reason distribution: {invalid_reason_counts}")
        
        # Filter out invalid concepts (invalid_reason IS NOT NULL)
        # This matches the behavior of lookup_mapped_concepts
        included_concepts = [
            concept for concept in included_concepts_raw
            if concept.invalid_reason is None
        ]
        
        if debug:
            print(f"  After filtering invalid_reason IS NULL: {len(included_concepts)} valid concepts")
            if included_concepts:
                print(f"  First concept: {included_concepts[0].concept_id} - {included_concepts[0].concept_name}")
            print()
        
        # Step 3: Look up mapped source concepts (source codes) for the included concepts
        if debug:
            print("Step 3: Looking up mapped source concepts (source codes)...")
            if has_include_mapped:
                print("  Note: include_mapped=True, so resolved concepts already include mapped concepts")
                print("  We'll find source codes for the resolved concepts (which may include both original and mapped)")
            print()
        
        included_source_codes = self.lookup_mapped_concepts(included_concept_ids, debug=debug)
        
        if debug:
            print(f"  Found {len(included_source_codes)} mapped source concepts")
            if included_source_codes:
                print(f"  First mapped concept: {included_source_codes[0].concept_id} - {included_source_codes[0].concept_name} ({included_source_codes[0].concept_code})")
            
            # Debug: Check overlap between included_concepts and included_source_codes
            included_concept_ids_set = {c.concept_id for c in included_concepts}
            source_code_ids_set = {c.concept_id for c in included_source_codes}
            overlap = included_concept_ids_set & source_code_ids_set
            only_in_included = included_concept_ids_set - source_code_ids_set
            only_in_source_codes = source_code_ids_set - included_concept_ids_set
            
            print(f"  Overlap analysis:")
            print(f"    Concepts in both: {len(overlap)}")
            print(f"    Only in included_concepts: {len(only_in_included)}")
            print(f"    Only in included_source_codes: {len(only_in_source_codes)}")
            if only_in_included:
                print(f"    Example IDs only in included: {list(only_in_included)[:10]}")
            if only_in_source_codes:
                print(f"    Example IDs only in source codes: {list(only_in_source_codes)[:10]}")
            print()
        
        if debug:
            print("=" * 80)
            print("FINAL RESULT:")
            print(f"  Included concepts: {len(included_concepts)}")
            print(f"  Included source codes: {len(included_source_codes)}")
            print("=" * 80)
            print()
        
        return included_concepts, included_source_codes
