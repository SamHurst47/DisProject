"""
static_modules.py

Define the data classes used thought the pipeline to store the key data set of the review payload, 
suggested changes and static issues this further ensure the consistent data flow between modules.

Author: Sam Hurst
"""
import json
import subprocess
import tempfile
import os

from app.base_module import AnalyserModule
from app.code_review_payload import StaticIssue

class TodoAnalyser(AnalyserModule):
    """
    A basic static analyser that flags any 'TODO' or 'FIXME' comments in the code.
    """
    def analyse(self, data):
        # Collects raw code
        lines = data.raw_content.split('\n')
        
        # Scans line by line 
        for line_number, line in enumerate(lines, start=1):
            upper_line = line.upper()
            
            if "TODO" in upper_line or "FIXME" in upper_line:
                # Simple check and report recording
                issue = StaticIssue(
                    tool_name="TodoScanner",
                    line_number=line_number,
                    message="Found unresolved TODO or FIXME comment.",
                    severity="info",
                    rule_id="T001"
                )
                
                # Add the issue 
                data.add_static_issue(issue)
        
        # Recodes execution in metadata 
        data.metadata["todo_scanner_completed"] = True
        
        # Always return the data structure for next module to orate on
        return data
    
class PylintAnalyzer(AnalyserModule):
    """
    Runs Pylint on the provided code to catch syntax errors and style issues.
    """
    def analyse(self, data):
        # Checks if the input is python
        if data.language.lower() != "python":
            data.metadata["pylint_skipped"] = "Code is not Python"
            return data

        # Creates a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(data.raw_content)
            temp_filename = temp_file.name

        try:
            # Run Pylint via CLI, requesting JSON output
            # Pylint returns a non-zero exit code if it finds issues, so we ignore failures here
            result = subprocess.run(
                ['pylint', temp_filename, '--output-format=json'],
                capture_output=True,
                text=True
            )
            
            # Parse the output
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
            print(f" Pylint Analyzer failed: {e}")
            data.metadata["pylint_error"] = str(e)
            
        finally:
            # Clean up the temp file so we don't leak disk space
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
            # Pygount can output JSON stats
            result = subprocess.run(
                ['pygount', '--format=json', temp_filename],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                stats = json.loads(result.stdout)
                # There should only be one file in the summary
                if stats and "files" in stats and len(stats["files"]) > 0:
                    file_stats = stats["files"][0]
                    # Store these metrics in the metadata!
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
        
        # For now, let's leave a footprint that indicates this would be an async/heavy job
        data.metadata["sonar_status"] = "Pending full repo scan"
        data.metadata["sonar_project_key"] = self.project_key
        
        return data
'''