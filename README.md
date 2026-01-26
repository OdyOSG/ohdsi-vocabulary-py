# OHDSI Vocabulary

A Python library for resolving OHDSI concept set expressions and retrieving included concepts and source codes from OMOP CDM vocabulary tables.

## Features

- **Concept Set Expression Resolution**: Resolve concept set expressions to get included concept IDs, supporting:
  - Direct concept inclusion
  - Descendant expansion (`include_descendants`)
  - Mapped concept inclusion (`include_mapped`)
  - Concept exclusion
  
- **Concept Lookup**: Retrieve full concept details from vocabulary tables

- **Source Code Retrieval**: Get source codes (concept codes) that map to included concepts via 'Maps to' relationships

- **Flexible Configuration**: Configurable table and column names to support different database schemas

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/YOUR_USERNAME/ohdsi-vocabulary.git
```

Or clone and install:

```bash
git clone https://github.com/YOUR_USERNAME/ohdsi-vocabulary.git
cd ohdsi-vocabulary
pip install .
```

## Requirements

- Python 3.8+
- SQLAlchemy 2.0+
- Pydantic 2.0+
- A database connection to an OMOP CDM database with vocabulary tables

## Quick Start

```python
from ohdsi_vocabulary import Concept, ConceptSetExpression, ConceptSetItem, VocabularyService

# Initialize the service with your database connection
with VocabularyService(
    connection_string="postgresql://user:password@host:port/database",
    vocabulary_schema="vocab",  # or "public" depending on your schema
    table_concept="concept",
    table_concept_ancestor="concept_ancestor",
    table_concept_relationship="concept_relationship",
) as vocab_service:
    
    # Create a concept set expression
    expression = ConceptSetExpression(
        items=[
            ConceptSetItem(
                concept=Concept(
                    concept_id=140168,  # Example: Psoriasis
                    concept_name="Psoriasis",
                    standard_concept="S",
                    concept_code="9014002",
                    domain_id="Condition",
                    vocabulary_id="SNOMED",
                    concept_class_id="Clinical Finding",
                ),
                include_descendants=True,
                include_mapped=False,
                is_excluded=False,
            )
        ]
    )
    
    # Get both included concepts and source codes
    included_concepts, included_source_codes = vocab_service.get_included_concepts_and_source_codes(
        expression,
        debug=False  # Set to True for detailed debugging output
    )
    
    print(f"Found {len(included_concepts)} included concepts")
    print(f"Found {len(included_source_codes)} source codes")
```

## API Reference

### VocabularyService

Main service class for vocabulary operations.

#### Initialization

```python
VocabularyService(
    connection_string: Optional[str] = None,
    engine: Optional[Engine] = None,
    vocabulary_schema: str = "vocab",
    connection: Optional[Connection] = None,
    # Table names (all configurable)
    table_concept: str = "concept",
    table_concept_ancestor: str = "concept_ancestor",
    table_concept_relationship: str = "concept_relationship",
    # Column names (all configurable)
    col_concept_id: str = "concept_id",
    # ... (see full documentation for all column options)
)
```

#### Methods

##### `resolve_concept_set_expression(expression: ConceptSetExpression) -> List[int]`

Resolve a concept set expression to a list of included concept IDs.

**Parameters:**
- `expression`: The ConceptSetExpression to resolve

**Returns:**
- List of concept IDs (integers) that are included in the resolved concept set

##### `lookup_concepts(concept_ids: List[int]) -> List[Concept]`

Look up full concept details for a list of concept IDs.

**Parameters:**
- `concept_ids`: List of concept IDs to look up

**Returns:**
- List of Concept objects with full details

##### `lookup_mapped_concepts(concept_ids: List[int], debug: bool = False) -> List[Concept]`

Look up source concepts that map to the given concept IDs via 'Maps to' relationships.

**Parameters:**
- `concept_ids`: List of concept IDs to find mapped source concepts for
- `debug`: If True, print intermediate steps and debugging information

**Returns:**
- List of Concept objects representing the input concepts and all source concepts that map to them

##### `get_included_source_codes(concept_ids: List[int], debug: bool = False) -> List[str]`

Get all source codes (concept_code) that map to the included concept IDs.

**Parameters:**
- `concept_ids`: List of included concept IDs (from resolve_concept_set_expression)
- `debug`: If True, print intermediate steps and debugging information

**Returns:**
- List of source code strings (concept_code values) that map to the included concepts

##### `get_included_source_codes_with_details(concept_ids: List[int]) -> List[dict]`

Get all source codes with full details that map to the included concept IDs.

**Parameters:**
- `concept_ids`: List of included concept IDs (from resolve_concept_set_expression)

**Returns:**
- List of dictionaries with source code details (all Concept fields)

##### `get_included_concepts_and_source_codes(expression: ConceptSetExpression, debug: bool = False) -> Tuple[List[Concept], List[Concept]]`

Get both included concepts and included source codes as separate lists in a single call.

**Parameters:**
- `expression`: The ConceptSetExpression to resolve
- `debug`: If True, print intermediate steps and debugging information

**Returns:**
- Tuple of (included_concepts, included_source_codes) where:
  - `included_concepts`: List of Concept objects from resolving the expression
  - `included_source_codes`: List of Concept objects representing mapped source codes

### Models

#### Concept

Represents a vocabulary concept with the following fields:
- `concept_id`: Optional[int]
- `concept_name`: Optional[str]
- `standard_concept`: Optional[str]
- `invalid_reason`: Optional[str]
- `concept_code`: Optional[str]
- `domain_id`: Optional[str]
- `vocabulary_id`: Optional[str]
- `concept_class_id`: Optional[str]

#### ConceptSetExpression

Represents a concept set expression with:
- `items`: List[ConceptSetItem]

#### ConceptSetItem

Represents an item in a concept set expression with:
- `concept`: Concept
- `is_excluded`: bool (default: False)
- `include_descendants`: bool (default: False)
- `include_mapped`: bool (default: False)

## Examples

### Example 1: Resolve concept set with descendants

```python
expression = ConceptSetExpression(
    items=[
        ConceptSetItem(
            concept=Concept(concept_id=140168, ...),
            include_descendants=True,
            include_mapped=False,
            is_excluded=False,
        )
    ]
)

concept_ids = vocab_service.resolve_concept_set_expression(expression)
concepts = vocab_service.lookup_concepts(concept_ids)
```

### Example 2: Get source codes for included concepts

```python
concept_ids = vocab_service.resolve_concept_set_expression(expression)
source_codes = vocab_service.get_included_source_codes(concept_ids)
```

### Example 3: Get both concepts and source codes

```python
included_concepts, included_source_codes = vocab_service.get_included_concepts_and_source_codes(
    expression,
    debug=True  # Enable debug output
)
```

## Database Configuration

The library supports flexible table and column naming. If your database uses different names, configure them during initialization:

```python
vocab_service = VocabularyService(
    connection_string="...",
    vocabulary_schema="public",
    table_concept="concepts",  # Custom table name
    table_concept_ancestor="ancestors",
    table_concept_relationship="relations",
    col_concept_id="concept_id",  # Custom column names if needed
    # ... other column configurations
)
```

## Notes

- The library filters out invalid concepts (`invalid_reason IS NULL`) from results
- When `include_mapped=True`, the resolved concept IDs already include mapped concepts
- The library handles Oracle's IN clause limitation (1000 items) by chunking queries
- All methods support context manager usage (`with` statement) for automatic connection cleanup

## License

[Specify your license here]

## Contributing

[Add contribution guidelines if applicable]

## References

- [OHDSI](https://www.ohdsi.org/)
- [OMOP Common Data Model](https://www.ohdsi.org/data-standardization/the-common-data-model/)
