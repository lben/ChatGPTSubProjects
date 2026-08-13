---
name: reconcile-data
description: Investigate source files, identify likely primary or business keys, discover database candidates, run bounded matching experiments, and validate a mapping with holdout evidence. Use for data reconciliation and lineage research.
argument-hint: '[source file and reconciliation objective]'
---

# Reconcile data

## 1. Establish the contract

Record the objective, source artifact, expected population, acceptable exclusions, required match quality, and proof in local task state. Do not copy company-specific information into tracked files.

## 2. Profile locally

For each source column and plausible combination, measure without exposing sample values:

- row and non-null count;
- null rate;
- distinct count and uniqueness;
- inferred type;
- minimum and maximum length;
- stable format or character shape;
- duplicate distribution;
- relationship to known business meaning.

Rank candidate keys. Do not assume a field named `id` is correct.

## 3. Discover database candidates

Use metadata first:

- column and table names;
- data types and lengths;
- primary-key and unique constraints;
- indexes;
- comments or catalog descriptions;
- approximate cardinality when permitted.

Rank candidates. Do not scan unrelated schemas.

## 4. Run controlled experiments

Create one request under `.agent/local/db-requests/` per hypothesis. Change one material factor at a time.

Possible transformations include exact comparison, trim, case normalization, numeric conversion, date normalization, leading-zero handling, punctuation removal, prefix or suffix logic, substring, mapping table, concatenation, and composite keys.

Every request must have a purpose, one bounded read-only statement, timeout, row limit, deterministic sample definition, and compact expected output. Use DB Scout and the `run-db-query` skill.

## 5. Measure correctly

Record:

- tested source rows;
- source coverage;
- unique matches;
- ambiguous matches;
- unmatched rows;
- source null loss;
- target duplicates;
- transformation complexity;
- query duration;
- sample definition.

A high match percentage is insufficient when matches are ambiguous or exclusions are biased.

## 6. Validate holdout

Freeze the candidate and transformation. Test a deterministic population not used to select or tune it. Compare sample and holdout metrics. Investigate material degradation.

## 7. Conclude

Accept only with reproducible evidence. Record exact source key, target columns, transformation, metrics, exceptions, and remaining risk in the local ledger. Otherwise state what remains unresolved and the next highest-value experiment.
