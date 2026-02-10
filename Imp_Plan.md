# Implementation Checklist & Task Plan

## Phase 1: Project Setup

* [ ] Confirm project scope with supervisor
* [ ] Decide input type (single file vs small project)
* [ ] Choose LLM access method (API / local model)
* [ ] Set up Git repository
* [ ] Create Python virtual environment
* [ ] Define project folder structure

## Phase 2: Data & Input Handling

* [ ] Collect example Python files (open-source or self-written)
* [ ] Implement code loader (read `.py` files)
* [ ] Implement code splitter (functions / classes)
* [ ] Extract comments and docstrings
* [ ] Add basic input validation

## Phase 3: Review Role Design

* [ ] Define reviewer roles (bugs, style, security, etc.)
* [ ] Write system prompts for each role
* [ ] Define strict JSON output schema
* [ ] Test prompts on small code snippets

## Phase 4: Hybrid Review Logic

* [ ] Implement basic rule-based checks (e.g. file size, complexity)
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

## Minimal "Start Tomorrow" To-Do List

If you want the absolute minimum to begin:

* Set up repo + environment
* Choose 3–5 Python files as test inputs
* Define reviewer roles
* Write one working LLM reviewer
* Return structured JSON output

Once that works, everything else builds naturally.
