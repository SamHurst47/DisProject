# Code Review Pipeline Schema (Updated)

---

## Input Module

**Inputs** (from upload to web interface or direct parsing):

| Field | Type | Required | Description |
| :-- | :-- | :-- | :-- |
| file_path | string | Optional | Path to `.py` file, Git diff, or project dir. Optional if `raw_content` encodes paths. |
| raw_content | string | Yes | Unparsed Python source or unified diff; feeds all downstream processes. |
| metadata | object | No | `{language: string, source_type: "file"|"diff"|"repo", upload_id?: string}`; optional metadata. |

**Outputs** (to intermediate modules):

| Field | Type | Required | Description |
| :-- | :-- | :-- | :-- |
| code_data | array[object] | Yes | Standardized array of code items: `[{id, file_path, content, ast_tree?, metadata?}]`; validated and enriched. |

**`code_data` object**:

```json
{
  "id": "stable_file_id_001",
  "file_path": "src/foo.py",
  "content": "print('hello world')",
  "ast_tree": null,
  "metadata": {
    "language": "python",
    "source_type": "file"
  }
}
``` 

---

## Intermediate Modules (Static Modules and LLM moduels)

**Input/Output** (Unified shceme to enable total flexiabilty):  
| Field | Type | Required | Description |
| :-- | :-- | :-- | :-- |
| code_data | array[object] | No | `[{id, file_path, content, ast_tree?, metadata?}]`; raw or enriched code. |
| review_items | array[object] | No | Cumulative issues: `[{module_id, module_version, location, severity, message, confidence?, fix?}]`. |
| state | object | No | `{scores, config, cache, metadata}`; module-specific state (e.g., LLM cache, runtime info). |

---

## Output Module

**Inputs** (from all intermediates): `review_items[]` array (order-independent).

**Outputs** (final artifacts to eventualy be proccessed in web interface):

| Field | Type | Required | Description |
| :-- | :-- | :-- | :-- |
| summary | object | Yes | `{overall_score, critical_issues_count, pass_fail, policy, run_id}`; executive metrics with traceability. |
| grouped_by_module | object | Yes | `{module_id: review_items[]}`; preserves source attribution. |
| rendered_report | string | Yes | Markdown/HTML report with line links; human-readable. |
| json_export | object | No | Raw data dump for analysis/reproducibility. |

---

## Module Flow Digram
