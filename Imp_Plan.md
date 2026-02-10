# Implementation Checklist & Task Plan

## Phase 1: Project Setup

* [/] Decide input type (single file vs small project) **Small Project**
* [ ] Choose LLM access method (API / local model) **Hybrid**
* [ ] Set up Git repository 
* [ ] Create  Environment 
* [ ] Define project folder structure
* [ ] Choose 3–5 Python files as test inputs
* [ ] Decide JSON interaction input and output 

## Phase 2: Data & Input Handling

* [ ] Collect example Python files
* [ ] Implement code loader (read `.py` files)
* [ ] Implement code splitter (functions/classes)
* [ ] Extract comments and docstrings
* [ ] Add basic input validation

## Phase 3: Review Role Design

* [ ] Define reviewer roles (bugs, style, security, etc.)
* [ ] Write system prompts for each role
* [ ] Define strict JSON output schema
* [ ] Test prompts on small code snippets

## Phase 4: Hybrid Review Logic

* [ ] Implement basic rule-based checks 
* [ ] Connect LLM calls to reviewer roles 
* [ ] Run reviewers in parallel or sequence
* [ ] Validate and parse JSON responses

## Phase 5: Aggregation

* [ ] Merge reviewer outputs
* [ ] Detect and remove duplicate issues
* [ ] Resolve conflicting feedback
* [ ] Rank issues by severity
* [ ] Filter low-confidence results

## Phase 6: Output & Presentation

* [ ] Generate human-readable review
* [ ] Group issues by category
* [ ] Add summary section
* [ ] Output to console / file (JSON + text)

## Phase 7: Evaluation

* [ ] Select baseline systems (single LLM, pylint)
* [ ] Run comparisons on same code samples
* [ ] Record results
* [ ] Perform simple ablation (remove one reviewer)
* [ ] Analyze differences

## Phase 8: Documentation & Write-up

* [ ] Document system architecture
* [ ] Save prompt templates
* [ ] Record implementation decisions
* [ ] Write limitations and challenges
* [ ] Prepare figures and tables

---
