"""
Builder for generating SQL queries from ConceptSetExpression.
"""

from typing import List

from .concept import Concept
from .concept_set_expression import ConceptSetExpression, ConceptSetItem


class ConceptSetExpressionQueryBuilder:
    """Builds SQL queries from ConceptSetExpression."""

    MAX_IN_LENGTH = 1000  # Oracle limitation

    # SQL templates - matching Java implementation
    CONCEPT_SET_QUERY_TEMPLATE = (
        "select concept_id from @vocabulary_database_schema.CONCEPT where {}"
    )

    CONCEPT_SET_QUERY_WITH_INVALID_REASON_TEMPLATE = "select concept_id,invalid_reason from @vocabulary_database_schema.CONCEPT where {}"

    CONCEPT_SET_DESCENDANTS_TEMPLATE = (
        "select c.concept_id\n"
        "from @vocabulary_database_schema.CONCEPT c\n"
        "join @vocabulary_database_schema.CONCEPT_ANCESTOR ca on c.concept_id = ca.descendant_concept_id\n"
        # "WHERE c.invalid_reason = 'V'\n"
        "WHERE c.invalid_reason is NULL\n"
        "and {}"
    )

    CONCEPT_SET_MAPPED_TEMPLATE = (
        "select distinct cr.concept_id_1 as concept_id\n"
        "FROM\n"
        "(\n"
        "{}\n"
        ") C\n"
        "join @vocabulary_database_schema.concept_relationship cr on C.concept_id = cr.concept_id_2 "
        # "and cr.relationship_id = 'Maps to' and C.invalid_reason = 'V'"
        "and cr.relationship_id = 'Maps to' and C.invalid_reason is NULL"
    )

    CONCEPT_SET_INCLUDE_TEMPLATE = (
        "select distinct I.concept_id FROM\n" "(\n" "{}\n" ") I"
    )

    CONCEPT_SET_EXCLUDE_TEMPLATE = (
        "LEFT JOIN\n"
        "(\n"
        "{}\n"
        ") E ON I.concept_id = E.concept_id\n"
        "WHERE E.concept_id is null"
    )

    def _get_concept_ids(self, concepts: List[Concept]) -> List[int]:
        """Extract concept IDs from concept list."""
        return [c.concept_id for c in concepts if c.concept_id is not None]

    def _split_in_clause(self, column: str, values: List[int], group_size: int) -> str:
        """Split values into groups for IN clauses (Oracle limitation)."""
        if not values:
            return ""

        groups = []
        for i in range(0, len(values), group_size):
            end_index = min(i + group_size, len(values))
            group = values[i:end_index]
            groups.append(f"{column} in ({','.join(map(str, group))})")

        if len(groups) == 1:
            return groups[0]
        else:
            return f"({' or '.join(groups)})"

    def _build_concept_set_sub_query(
        self, concepts: List[Concept], descendant_concepts: List[Concept]
    ) -> str:
        """Build sub-query for concepts and descendants."""
        queries = []

        if concepts:
            concept_ids = self._get_concept_ids(concepts)
            in_clause = self._split_in_clause(
                "concept_id", concept_ids, self.MAX_IN_LENGTH
            )
            queries.append(self.CONCEPT_SET_QUERY_TEMPLATE.format(in_clause))

        if descendant_concepts:
            descendant_ids = self._get_concept_ids(descendant_concepts)
            in_clause = self._split_in_clause(
                "ca.ancestor_concept_id", descendant_ids, self.MAX_IN_LENGTH
            )
            queries.append(self.CONCEPT_SET_DESCENDANTS_TEMPLATE.format(in_clause))

        return " UNION ".join(queries) if queries else ""

    def _build_concept_set_sub_query_with_invalid_reason(
        self, concepts: List[Concept], descendant_concepts: List[Concept]
    ) -> str:
        """Build sub-query for concepts and descendants, including invalid_reason column for mapped queries."""
        queries = []

        if concepts:
            concept_ids = self._get_concept_ids(concepts)
            in_clause = self._split_in_clause(
                "concept_id", concept_ids, self.MAX_IN_LENGTH
            )
            queries.append(
                self.CONCEPT_SET_QUERY_WITH_INVALID_REASON_TEMPLATE.format(in_clause)
            )

        if descendant_concepts:
            # For descendants, we still need invalid_reason in the SELECT
            # The descendants template already filters on invalid_reason, but we need it in SELECT for the mapped query
            descendant_ids = self._get_concept_ids(descendant_concepts)
            in_clause = self._split_in_clause(
                "ca.ancestor_concept_id", descendant_ids, self.MAX_IN_LENGTH
            )
            # Modify the descendants query to include invalid_reason in SELECT
            descendants_query = (
                "select c.concept_id, c.invalid_reason\n"
                "from @vocabulary_database_schema.CONCEPT c\n"
                "join @vocabulary_database_schema.CONCEPT_ANCESTOR ca on c.concept_id = ca.descendant_concept_id\n"
                # "WHERE c.invalid_reason = 'V'\n"
                "WHERE c.invalid_reason is NULL\n"
                f"and {in_clause}"
            )
            queries.append(descendants_query)

        return " UNION ".join(queries) if queries else ""

    def _build_concept_set_mapped_query(
        self, mapped_concepts: List[Concept], mapped_descendant_concepts: List[Concept]
    ) -> str:
        """Build query for mapped concepts."""
        # Use the version that includes invalid_reason in the subquery
        concept_set_query = self._build_concept_set_sub_query_with_invalid_reason(
            mapped_concepts, mapped_descendant_concepts
        )
        if not concept_set_query:
            return ""

        # Wrap the concept set query in the mapped template
        return self.CONCEPT_SET_MAPPED_TEMPLATE.format(concept_set_query)

    def _build_concept_set_query(
        self,
        concepts: List[Concept],
        descendant_concepts: List[Concept],
        mapped_concepts: List[Concept],
        mapped_descendant_concepts: List[Concept],
    ) -> str:
        """Build the main concept set query."""
        if not concepts and not descendant_concepts:
            return (
                "select concept_id from @vocabulary_database_schema.CONCEPT where 0=1"
            )

        concept_set_query = self._build_concept_set_sub_query(
            concepts, descendant_concepts
        )

        if mapped_concepts or mapped_descendant_concepts:
            mapped_query = self._build_concept_set_mapped_query(
                mapped_concepts, mapped_descendant_concepts
            )
            if mapped_query:
                concept_set_query += " UNION\n" + mapped_query

        return concept_set_query

    def build_expression_query(self, expression: ConceptSetExpression) -> str:
        """Build SQL query from ConceptSetExpression."""
        # Separate concepts by inclusion/exclusion and flags
        include_concepts: List[Concept] = []
        include_descendant_concepts: List[Concept] = []
        include_mapped_concepts: List[Concept] = []
        include_mapped_descendant_concepts: List[Concept] = []

        exclude_concepts: List[Concept] = []
        exclude_descendant_concepts: List[Concept] = []
        exclude_mapped_concepts: List[Concept] = []
        exclude_mapped_descendant_concepts: List[Concept] = []

        # Populate each sub-set of concepts from the flags set in each concept set item
        for item in expression.items:
            if not item.is_excluded:
                include_concepts.append(item.concept)

                if item.include_descendants:
                    include_descendant_concepts.append(item.concept)

                if item.include_mapped:
                    include_mapped_concepts.append(item.concept)
                    if item.include_descendants:
                        include_mapped_descendant_concepts.append(item.concept)
            else:
                exclude_concepts.append(item.concept)
                if item.include_descendants:
                    exclude_descendant_concepts.append(item.concept)
                if item.include_mapped:
                    exclude_mapped_concepts.append(item.concept)
                    if item.include_descendants:
                        exclude_mapped_descendant_concepts.append(item.concept)

        # Build include query
        include_query = self._build_concept_set_query(
            include_concepts,
            include_descendant_concepts,
            include_mapped_concepts,
            include_mapped_descendant_concepts,
        )
        concept_set_query = self.CONCEPT_SET_INCLUDE_TEMPLATE.format(include_query)

        # Build exclude query if needed
        if (
            exclude_concepts
            or exclude_descendant_concepts
            or exclude_mapped_concepts
            or exclude_mapped_descendant_concepts
        ):
            exclude_query = self._build_concept_set_query(
                exclude_concepts,
                exclude_descendant_concepts,
                exclude_mapped_concepts,
                exclude_mapped_descendant_concepts,
            )
            exclude_clause = self.CONCEPT_SET_EXCLUDE_TEMPLATE.format(exclude_query)
            concept_set_query += "\n" + exclude_clause

        return concept_set_query
