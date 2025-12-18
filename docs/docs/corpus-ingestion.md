---
sidebar_position: 3
---

# Corpus Ingestion

After completing the installation, you need to ingest a corpus of tables to build the semantic join database. The corpus provides the statistical foundation for semantic joins.

**Prerequisites:** You must complete the [Installation](./installation) step before running corpus ingestion.

## What is a Corpus?

A corpus is a collection of tables from your data domain that serves as the statistical foundation for semantic joins. Project SEMA-JOIN analyzes this corpus to discover which values co-occur frequently across tables.

The key insight from the Microsoft Research SEMA-JOIN paper is that values appearing together in the same table often have semantic relationships. For example, if "California" and "Los Angeles" frequently appear in the same rows across many tables, they likely have a geographic relationship.

## Corpus Data

Project SEMA-JOIN includes sample corpus data in JSON format. This data contains tables that will be analyzed to build the semantic index.
Currently supported corpus formats are:
- JSON files containing arrays of tables in Wikitable or WDC format

## Ingestion Process

The ingestion process reads corpus JSON files and stores co-occurrence data in the database:

**What Gets Stored:**
- Table metadata (table IDs, row IDs, column IDs)
- Cell values with their positions (which table, row, and column they appear in)
- Co-occurrence patterns (which values appear together in the same tables)

## Running Ingestion

**Important:** Before running ingestion, ensure you have installed the corpus dependencies (this is done automatically in the installation guide, but mentioned here for reference):

```bash
cd corpus
uv sync
cd ..
```

Use the make command to run the corpus ingestion process:

```bash
# Run from project root (sema-join/)
make ingest
```

This will execute the ingestion process:

- Read all JSON corpus files from `corpus/data/`
- Extract and normalize table values
- Store table structure (table IDs, row IDs, column IDs)
- Store cell values with their positions
- Record co-occurrence patterns (which values appear in same tables/rows/columns)
- Create database indexes for fast querying
- Generate the `corpus.db` file in the project root

## Database Location

The corpus database is created in the project root directory. This database contains all the statistical information needed for semantic joins.

## Verifying Ingestion

After ingestion completes, verify the database was created successfully:

```bash
ls -lh corpus.db
```

You should see a database file with size information indicating successful creation.

## Re-running Ingestion

If you need to re-ingest the corpus, first remove the existing database:

```bash
# Run from project root (sema-join/)
rm corpus.db
```

Then run the ingestion process again:

```bash
# Run from project root (sema-join/)
make ingest
```

This is useful when updating the corpus with new tables or correcting data issues.


## Next Steps

With corpus ingestion complete, you are ready to start using Project SEMA-JOIN.
