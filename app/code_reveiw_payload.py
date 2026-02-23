"""
code_review_payload.py

Define the data classes sued thought the pipeline to store the key data set of the review payload, 
suggested changes and static issues this further ensure the consistent data flow between modules.

Author: Sam Hurst
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class StaticIssue:
    """Represents a finding from a static analysis tool like Flake8 or Bandit."""
    tool_name: str       # e.g., "flake8", "sonar"
    line_number: int
    message: str
    severity: str        # e.g., "warning", "error", "info"
    rule_id: Optional[str] = None # e.g., "E501"

@dataclass
class SuggestedChange:
    """Represents an intelligent code change suggested by an LLM."""
    line_start: int
    line_end: int
    original_code: str
    suggested_code: str
    explanation: str     # Why the LLM thinks this should change
    reviewer: str        # e.g., "gemini-3.1", "gpt-4"

@dataclass
class CodeReviewPayload:
    """
    Standardized payload that gets passed and mutated down the pipeline.
    """
    # Original Input State
    raw_content: str
    filename: Optional[str] = "snippet.txt"
    language: Optional[str] = "text"
    is_diff: bool = False
    author: Optional[str] = "anonymous"
    
    # Accumulated Pipeline State
    static_issues: List[StaticIssue] = field(default_factory=list)
    suggested_changes: List[SuggestedChange] = field(default_factory=list)
    
    # Storage for other issues and comments to be passed down the pipeline making flexible storage 
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Methods to add issues to be passed down
    def add_static_issue(self, issue: StaticIssue):
        self.static_issues.append(issue)
        
    def add_suggestion(self, suggestion: SuggestedChange):
        self.suggested_changes.append(suggestion)