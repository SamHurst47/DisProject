"""
static_modules.py

Define the data classes used throughout the pipeline to store the key data set of the review payload, 
suggested changes, and static issues. This further ensures the consistent data flow between modules.

Author: Sam Hurst
"""
import sys
import json
import subprocess
import tempfile
import os
import re

from app.base_module import AnalyserModule
from app.code_review_payload import StaticIssue


class TodoAnalyser(AnalyserModule):
    """
    A basic static analyser that flags any 'TODO' or 'FIXME' comments in the code.
    """
    def analyse(self, data):
        lines = data.raw_content.split('\n')
        
        for line_number, line in enumerate(lines, start=1):
            upper_line = line.upper()
            
            if "TODO" in upper_line or "FIXME" in upper_line:
                issue = StaticIssue(
                    tool_name="TodoScanner",
                    line_number=line_number,
                    message="Found unresolved TODO or FIXME comment.",
                    severity="info",
                    rule_id="T001"
                )
                data.add_static_issue(issue)
        
        data.metadata["todo_scanner_completed"] = True
        return data


class PylintAnalyzer(AnalyserModule):
    """
    Runs Pylint on the provided code to catch syntax errors and style issues.
    """
    def analyse(self, data):
        if data.language.lower() != "python":
            data.metadata["pylint_skipped"] = "Code is not Python"
            return data

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(data.raw_content)
            temp_filename = temp_file.name

        try:
            # FIXED: Using sys.executable to prevent [Errno 2] path errors
            result = subprocess.run(
                [sys.executable, '-m', 'pylint', temp_filename, '--output-format=json'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                issues = json.loads(result.stdout)
                for issue in issues:
                    static_issue = StaticIssue(
                        tool_name="Pylint",
                        line_number=issue.get("line", 0),
                        message=issue.get("message", "Unknown issue"),
                        severity=issue.get("type", "warning"),
                        rule_id=issue.get("message-id", "")
                    )
                    data.add_static_issue(static_issue)

            data.metadata["pylint_completed"] = True

        except Exception as e:
            print(f"Pylint Analyzer failed: {e}")
            data.metadata["pylint_error"] = str(e)
            
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        return data


class PygountAnalyzer(AnalyserModule):
    """
    Analyzes code size, comments, and whitespace using Pygount.
    """
    def analyse(self, data):
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{data.filename.split(".")[-1]}', delete=False) as temp_file:
            temp_file.write(data.raw_content)
            temp_filename = temp_file.name            
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pygount', '--format=json', temp_filename],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                stats = json.loads(result.stdout)
                if stats and "files" in stats and len(stats["files"]) > 0:
                    file_stats = stats["files"][0]
                    data.metadata["metrics_code_lines"] = file_stats.get("codeCount", 0)
                    data.metadata["metrics_comment_lines"] = file_stats.get("documentationCount", 0)
                    data.metadata["metrics_empty_lines"] = file_stats.get("emptyCount", 0)

            data.metadata["pygount_completed"] = True

        except Exception as e:
            print(f"Pygount Analyzer failed: {e}")
            data.metadata["pygount_error"] = str(e)
            
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        return data


class BanditAnalyzer(AnalyserModule):
    """
    Runs Bandit to find common security vulnerabilities in Python code.
    Requires: pip install bandit
    """
    def analyse(self, data):
        if data.language.lower() != "python":
            data.metadata["bandit_skipped"] = "Code is not Python"
            return data

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(data.raw_content)
            temp_filename = temp_file.name

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'bandit', '-f', 'json', temp_filename],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                try:
                    report = json.loads(result.stdout)
                    issues = report.get("results", [])
                    
                    for issue in issues:
                        static_issue = StaticIssue(
                            tool_name="Bandit",
                            line_number=issue.get("line_number", 0),
                            message=issue.get("issue_text", "Unknown security risk"),
                            severity=issue.get("issue_severity", "HIGH"),
                            rule_id=issue.get("test_id", "")
                        )
                        data.add_static_issue(static_issue)
                except json.JSONDecodeError:
                    data.metadata["bandit_error"] = "Failed to parse Bandit JSON"

            data.metadata["bandit_completed"] = True

        except Exception as e:
            print(f"Bandit Analyzer failed: {e}")
            data.metadata["bandit_error"] = str(e)
            
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        return data


class RegexSecretScanner(AnalyserModule):
    """
    A fast, native scanner that uses regex to find hardcoded secrets, 
    tokens, and API keys without needing external CLI tools.
    """
    def analyse(self, data):
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic API Key / Secret": r"(?i)(api_key|secret|password|token)\s*=\s*['\"][a-zA-Z0-9\-_]{16,}['\"]",
            "Bearer Token": r"Bearer\s+[a-zA-Z0-9\-\._~+]{30,}"
        }
        
        lines = data.raw_content.split('\n')
        
        for line_number, line in enumerate(lines, start=1):
            for secret_type, pattern in patterns.items():
                if re.search(pattern, line):
                    issue = StaticIssue(
                        tool_name="SecretScanner",
                        line_number=line_number,
                        message=f"Potential hardcoded {secret_type} detected.",
                        severity="CRITICAL",
                        rule_id="SEC001"
                    )
                    data.add_static_issue(issue)
                    
        data.metadata["secret_scanner_completed"] = True
        return data


class ComplexityAnalyzer(AnalyserModule):
    """
    A native static tool that flags lines with excessive indentation,
    which usually indicates overly complex, deeply nested logic.
    """
    def analyse(self, data):
        lines = data.raw_content.split('\n')
        
        MAX_SPACES = 16 
        
        for line_number, line in enumerate(lines, start=1):
            if not line.strip() or line.strip().startswith('#'):
                continue
                
            leading_spaces = len(line) - len(line.lstrip(' '))
            leading_tabs = len(line) - len(line.lstrip('\t'))
            total_indent = leading_spaces + (leading_tabs * 4)
            
            if total_indent > MAX_SPACES:
                issue = StaticIssue(
                    tool_name="ComplexityScanner",
                    line_number=line_number,
                    message=f"Deeply nested code detected ({total_indent // 4} levels deep). Consider refactoring.",
                    severity="warning",
                    rule_id="CPLX001"
                )
                data.add_static_issue(issue)
                
        data.metadata["complexity_scanner_completed"] = True
        return data


'''
Work In Progress
class SonarQubeMockAnalyzer(AnalyserModule):
    """
    Triggers a SonarScanner run. 
    Note: Real SonarQube integration usually requires checking out a full repo, 
    running the scanner, and polling the Sonar Web API for the quality gate status.
    """
    def __init__(self, project_key="my_pipeline_project"):
        self.project_key = project_key

    def analyze(self, data):
        # In a real scenario, you'd write the code to a specific directory structure
        # that Sonar expects, run `sonar-scanner`, wait for the server task to finish,
        # and then make an HTTP GET to http://localhost:9000/api/issues/search?projectKeys=...
        
        data.metadata["sonar_status"] = "Pending full repo scan"
        data.metadata["sonar_project_key"] = self.project_key
        
        return data
'''