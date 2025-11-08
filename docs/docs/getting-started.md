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

## How It Works

Project SEMA-JOIN operates in two stages:

**Stage 1: Corpus Preparation**  
The system ingests a corpus of tables and calculates PMI scores for all value pairs that co-occur. This creates a statistical foundation capturing semantic relationships present in your data domain.

**Stage 2: Table Joining**  
When joining two tables, Project SEMA-JOIN uses the pre-computed PMI scores to identify which rows have strong semantic relationships, even when values don't match exactly.

## System Components

**Backend Service**  
Implements the semantic join algorithms, manages the corpus database, and calculates PMI scores.

**Web Interface**  
Provides an intuitive interface for uploading tables and executing joins.

## Relationship to the Research Paper

This implementation is based on the Microsoft Research SEMA-JOIN paper and implements the core algorithms:

- CS-JP-LP for optimal join quality
- RS-JP for efficient performance
- PMI-based semantic relationship discovery
- Bridge table discovery for multi-hop joins

This implementation extends the research with additional features:

- Web-based user interface for accessibility
- AI-powered column matching to address the future work identified in the paper

## Next Steps

Start by setting up your environment configuration, then proceed with installation.

