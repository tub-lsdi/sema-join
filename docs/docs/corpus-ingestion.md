---
sidebar_position: 4
---

# Corpus Ingestion

After completing the installation, you need to ingest a corpus of tables to build the semantic join database. The corpus provides the statistical foundation for semantic joins.

**Prerequisites:** You must complete the [Installation](./installation) step before running corpus ingestion.

## What is a Corpus?

A corpus is a collection of tables from your data domain that serves as the statistical foundation for semantic joins. Project SEMA-JOIN analyzes this corpus to discover which values co-occur frequently across tables.

The key insight from the Microsoft Research SEMA-JOIN paper is that values appearing together in the same table often have semantic relationships. For example, if "California" and "Los Angeles" frequently appear in the same rows across many tables, they likely have a geographic relationship.

By calculating Pointwise Mutual Information (PMI) scores across the corpus, Project SEMA-JOIN quantifies the strength of these relationships. These pre-computed PMI scores are then used during the join phase to match rows based on semantic similarity rather than exact matches.

## Corpus Data

Project SEMA-JOIN includes sample corpus data in JSON format. This data contains tables that will be analyzed to build the semantic index.
Currently supported corpus formats are:
- JSON files containing arrays of tables in Wikitable or WDC format

## Ingestion Process

The ingestion process consists of two main steps:

### Step 1: Ingest Corpus Tables

The first step reads the corpus JSON files and stores table metadata and cell values in the database. This creates the foundation for semantic analysis.

### Step 2: Calculate Statistics

The second step calculates Pointwise Mutual Information (PMI) scores for value pairs based on their co-occurrence patterns.

PMI measures how much more likely two values are to appear together than would be expected by chance. High PMI scores indicate strong semantic relationships. The system also computes value frequencies and co-occurrence counts to support the join algorithms.

This statistical analysis is the core of Project SEMA-JOIN's ability to understand semantic relationships without manual rule definition.

## Running Ingestion

Use the management script to run the complete database setup process:

```bash
./sema-join.sh db
```

This will execute both ingestion steps in sequence:

- Read all corpus files
- Extract and normalize table values
- Calculate value frequencies
- Compute co-occurrence statistics
- Generate NPMI scores
- Create database indexes

Use the `--large` flag if you are using a large corpus:
This will use temporary files to handle larger datasets without running out of memory as well ase optimizing some steps for speed.

```bash./sema-join.sh db --large
```

## Database Location

The corpus database is created in the project root directory. This database contains all the statistical information needed for semantic joins.

## Ingestion Time

Ingestion time depends on corpus size:

- Small corpus: 1-5 minutes
- Large corpus: 10-30 minutes

## Verifying Ingestion

After ingestion completes, verify the database was created successfully:

```bash
ls -lh corpus.db
```

You should see a database file with size information indicating successful creation.

## Alternative Commands (Without sema-join.sh)

If you prefer not to use the management script, run the ingestion scripts directly.

Note: These commands require that you've already completed the installation step, which created the `.venv` directory.

```bash
# Activate virtual environment (created during installation)
source .venv/bin/activate

# Step 1: Ingest corpus data
python corpus/setup_db/01_ingest_corpus.py

# Step 2: Calculate PMI statistics
python corpus/setup_db/02_calculate_stats.py
```

## Re-running Ingestion

If you need to re-ingest the corpus, first remove the existing database:

```bash
rm corpus.db
```

Then run the ingestion process again:

```bash
./sema-join.sh db
```

Or using direct commands:

```bash
source .venv/bin/activate
python corpus/setup_db/01_ingest_corpus.py
python corpus/setup_db/02_calculate_stats.py
```

This is useful when updating the corpus with new tables or correcting data issues.

## Custom Corpus

To use your own corpus data, place JSON files in the corpus data directory. Each file should contain tables in the expected format.

The quality of semantic joins depends heavily on corpus coverage. Your corpus should contain representative tables from your data domain. The more tables with relevant value co-occurrences, the better Project SEMA-JOIN can discover semantic relationships.

For example, if you are joining geographic data, your corpus should contain tables with geographic entities. If you are joining product data, include tables with product names, manufacturers, and categories.

## Next Steps

With corpus ingestion complete, you are ready to start using Project SEMA-JOIN.

