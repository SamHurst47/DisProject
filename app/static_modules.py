"""
static_modules.py

Define the data classes used thought the pipeline to store the key data set of the review payload, 
suggested changes and static issues this further ensure the consistent data flow between modules.

Author: Sam Hurst
"""
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