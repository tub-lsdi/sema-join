---
sidebar_position: 1
slug: /
---

# Getting Started

Project SEMA-JOIN is a semantic table joining system developed based on Microsoft Research's SEMA-JOIN paper. Unlike traditional joins that require exact matches, Project SEMA-JOIN discovers and leverages semantic relationships between values to intelligently join tables.

## What is Project SEMA-JOIN?

Traditional database joins and even fuzzy joins are limited to exact or syntactically similar matches. Project SEMA-JOIN goes beyond this by understanding semantic relationships that exist in your data.

Project SEMA-JOIN automatically discovers these relationships by analyzing statistical co-occurrence patterns across a corpus of tables. When two values frequently appear together in tables, they likely have a semantic relationship.

For example, Project SEMA-JOIN can discover relationships such as:

- Entity variations: "USA" and "United States" 
- Hierarchical relationships: Cities to their states
- Brand relationships: "iPhone" to "Apple"
- Code mappings: Country codes to country names

These relationships are quantified using Pointwise Mutual Information (PMI) scores calculated from the corpus.

## System Components

**Backend Service (Python/FastAPI)**
The core orchestration service that coordinates all join operations. It implements the CS-JP-LP and RS-JP algorithms, manages the application database (MySQL), handles table uploads and storage, processes bridge table creation, and calls the Go service for PMI calculations. The backend also manages the Linear Programming solver for CS-JP-LP optimization. Runs on port 8000.

**Go Service**
High-performance PMI calculation engine that processes co-occurrence statistics from the corpus database. Uses optimized bitmap operations for fast computation of both row-level PMI scores (for RS-JP) and column-level quad scores (for CS-JP-LP). Runs on port 8080.

**Web Interface (Next.js)**
Provides an intuitive React-based interface for uploading tables, selecting join columns, configuring algorithms, and viewing results. Runs on port 3000.

## How It Works

Project SEMA-JOIN operates in two stages:

**Stage 1: Corpus Preparation**
The system ingests a corpus of tables and stores the values with additional metadata (e.g., tableID, rowID, columnID) in order to caluculate the co-occurrence statistics later on. For now, the data is just structured and stored.

**Stage 2: Table Joining**
When joining two tables, the backend service coordinates the process: it extracts values from selected columns, calls the Go service to calculate PMI scores on-demand for those specific values, then applies the chosen algorithm (RS-JP or CS-JP-LP) to determine the optimal join mappings. The Go service queries the corpus database for specific tables and uses optimized bitmap operations to compute PMI scores in real-time. This allows the system to identify which rows have strong semantic relationships, even when values don't match exactly.

## Relationship to the Research Paper

This implementation is based on the Microsoft Research SEMA-JOIN paper and implements the core algorithms:

- **CS-JP-LP (Column Score Join Prediction with Linear Programming)** - Uses column-level semantic compatibility scores with LP optimization to find the optimal join mapping that maximizes aggregate pairwise correlation. Provides the highest quality results (F-score) with a 2-approximation guarantee.
- **RS-JP (Row Score Join Prediction)** - A simplified variant that uses row-level PMI scores for greedy matching. Optimizes each join decision individually and provides high performance, but is suseptible to missing global context.
- **PMI-based semantic relationship discovery** - Uses Pointwise Mutual Information (PMI) scores calculated from statistical co-occurrence in a large table corpus (100M+ tables) to quantify semantic relationships at both row-level and column-level.
- **Automatic bridge table creation** - Creates bridge tables that map semantically related values even when they don't match exactly (e.g., country codes to country names, stock tickers to company names).

This implementation extends the research with additional features:

- Web-based user interface for accessibility
- AI-powered column matching to address the future work identified in the paper

## Next Steps

Follow the [Installation](./installation) guide to set up Project SEMA-JOIN and build your semantic relationship database.
