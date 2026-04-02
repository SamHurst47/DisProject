import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

from app.code_review_payload import CodeReviewPayload, SuggestedChange, StaticIssue
from app.pipeline import Pipeline
from app.base_module import InputModule, OutputModule, AnalyserModule
from app.llms_base_modules import BaseLLMAnalyser
from app.llms_modules import CommentReviewAnalyser, SecurityAuditAnalyser
from app.static_modules import PylintAnalyzer


def test_payload_initialization():
    data = CodeReviewPayload(raw_content="print('hello')", filename="test.py", language="python")
    assert data.language == "python"
    assert len(data.suggested_changes) == 0
    assert len(data.static_issues) == 0

def test_payload_adds_suggestions():
    data = CodeReviewPayload(raw_content="x = 1", filename="test.py", language="python")
    change = SuggestedChange(
        line_start=1, line_end=1, original_code="x = 1", 
        suggested_code="x: int = 1", explanation="Type hint", reviewer="Test"
    )
    data.add_suggestion(change)
    assert len(data.suggested_changes) == 1
    assert data.suggested_changes[0].reviewer == "Test"

class DummyInputModule(InputModule):
    def read(self): 
        return CodeReviewPayload(raw_content="dummy code", filename="dummy.py", language="python")

class DummyAnalyserModule(AnalyserModule):
    def __init__(self, tag_name):
        self.tag_name = tag_name
    def analyse(self, data):
        if "run_order" not in data.metadata:
            data.metadata["run_order"] = []
        data.metadata["run_order"].append(self.tag_name)
        return data

class DummyOutputModule(OutputModule):
    def write(self, data): 
        data.metadata["output_ran"] = True
        return data

def test_pipeline_execution_order():
    """Tests if the pipeline pulls from input, runs analyzers in order, and pushes to output."""
    
    pipeline = Pipeline(
        input_module=DummyInputModule(),
        output_module=DummyOutputModule()
    )
    
    pipeline.add_module(DummyAnalyserModule("Analyzer_1"))
    pipeline.add_module(DummyAnalyserModule("Analyzer_2"))
    pipeline.add_module(DummyAnalyserModule("Analyzer_3"))
    
    final_data = pipeline.run()
    
    assert final_data is not None
    assert "run_order" in final_data.metadata
    assert final_data.metadata["run_order"] == ["Analyzer_1", "Analyzer_2", "Analyzer_3"]
    assert final_data.metadata.get("output_ran") is True

@patch('subprocess.run')
def test_pylint_analyzer(mock_subprocess):
    """Mocks the OS subprocess to test if Pylint parses JSON correctly."""
    
    # 1. Setup fake Pylint JSON output
    fake_pylint_output = json.dumps([
        {
            "type": "warning",
            "line": 15,
            "message": "Line too long",
            "message-id": "C0301"
        }
    ])
    
    mock_subprocess.return_value = MagicMock(stdout=fake_pylint_output, returncode=0)
    
    analyzer = PylintAnalyzer()
    data = CodeReviewPayload(raw_content="x=1", filename="test.py", language="python")
    
    result_data = analyzer.analyse(data)
    
    assert len(result_data.static_issues) == 1
    issue = result_data.static_issues[0]
    assert issue.tool_name == "Pylint"
    assert issue.line_number == 15
    assert issue.message == "Line too long"
    assert issue.severity == "warning"

@patch("app.llms_base_modules.BaseLLMAnalyser._call_llm")
def test_security_audit_analyzer(mock_call_llm):
    """Tests if a specific LLM subclass processes its prompt and updates the payload."""
    
    fake_json_response = json.dumps({
        "suggestions": [
            {
                "line_start": 5,
                "line_end": 5,
                "original_code": "api_key = '12345'",
                "suggested_code": "api_key = os.getenv('API_KEY')",
                "explanation": "Hardcoded secret."
            }
        ]
    })
    
    mock_call_llm.return_value = (fake_json_response, 2.0)
    
    analyzer = SecurityAuditAnalyser(model_name="test-model", provider="api")
    data = CodeReviewPayload(raw_content="api_key = '12345'", filename="test.py", language="python")
    
    result_data = analyzer.analyse(data)
    
    assert len(result_data.suggested_changes) == 1
    assert result_data.suggested_changes[0].reviewer == "Api - Security Audit (test-model)"
    assert "Hardcoded secret" in result_data.suggested_changes[0].explanation


@patch("app.llms_base_modules.BaseLLMAnalyser._call_llm")
def test_base_llm_analyser_handles_bad_json(mock_call_llm):
    mock_call_llm.return_value = ("```json\n This is not valid JSON! \n```", 0.5)
    
    analyzer = CommentReviewAnalyser(model_name="test-model", provider="api")
    data = CodeReviewPayload(raw_content="code", filename="test.py", language="python")
    
    result_data = analyzer.analyse(data)
    
    assert len(result_data.suggested_changes) == 0
    assert "Comment Review_error" in result_data.metadata
    assert "Expecting value" in result_data.metadata["Comment Review_error"]