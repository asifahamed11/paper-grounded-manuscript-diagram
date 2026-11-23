# Hybrid passage retrieval for a research archive

## Abstract

This worked example demonstrates how a keyword ranking and a vector ranking can be combined to retrieve passages from a research archive. A fixed collection, two queries and their relevance grades make the workflow runnable with only the Python standard library. The example illustrates the method and the role of relevance judgments in evaluation.

## Methods

### 1. Passages and queries

The demonstration provides eight short passages and two evaluation queries. Each passage and query has text and a fixed synthetic vector. Both retrieval branches use the same passage collection and query. The vectors are supplied with the example.

### 2. Parallel retrieval

The lexical branch tokenizes the text and ranks passages by BM25. The dense branch ranks the supplied vectors by cosine similarity. Each branch returns five passage IDs in rank order. Ties are resolved by passage ID.

### 3. Rank fusion

Reciprocal rank fusion adds a contribution of `1 / (60 + rank)` for each appearance in the two input lists, using one-based ranks. The fused output keeps the five best-scoring passage IDs.

### 4. Evaluation

The evaluator compares the fused list for each query with its fixed graded relevance judgments. Grades enter only at this stage and have no effect on retrieval or fusion. nDCG@5 uses the full grades, and Recall@5 treats every positive grade as relevant.

## Scope

The passages, vectors and judgments are illustrative fixtures. Metrics on this small example demonstrate the evaluation calculation. The design makes no claim about retrieval performance on a broader research archive.
