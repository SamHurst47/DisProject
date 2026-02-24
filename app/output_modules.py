"""
output_modules.py

Used to define the different output methods utilising payload define in code_review_payload
and convert payload in to a printable output and eventual to link in to the web service.

Author: Sam Hurst
"""
from app.base_module import OutputModule

class PrintOutputModule(OutputModule):
    """
    Output module that prints a formatted CLI report of the final pipeline result.
    Perfect for local testing before the web UI is ready.
    """

    def write(self, data):
        # Nice formatting 
        print("\n" + "="*60)
        print(f" CODE REVIEW REPORT: {data.filename} ({data.language})")
        print("="*60)

        # Print Static Issues
        print(f"\n  [ STATIC ANALYSIS ] - Found: {len(data.static_issues)} issues")
        if not data.static_issues:
            print("  No static issues found.")
        else:
            for issue in data.static_issues:
                # Searches rescord and ouptuts relvant info 
                print(f"  * Line {issue.line_number} [{issue.tool_name}] ({issue.severity.upper()}): {issue.message}")

        # Print LLMs Suggestions
        print(f"\n [ LLM SUGGESTIONS ] - Found: {len(data.suggested_changes)} suggestions")
        if not data.suggested_changes:
            print("  No LLM suggestions.")
        else:
            for count, sig in enumerate(data.suggested_changes, 1):
                print(f"  --- Suggestion {count} ({sig.reviewer}) ---")
                print(f"  Lines: {sig.line_start} to {sig.line_end}")
                print(f"  Why: {sig.explanation}")
                print(f"  Suggested Fix:\n{self._indent_code(sig.suggested_code)}\n")

        # Print Metadata (COMMENT)
        print(f"\n [ PIPELINE METADATA ]")
        if not data.metadata:
            print("  No metadata recorded.")
        else:
            for key, value in data.metadata.items():
                print(f"  * {key}: {value}")
        
        print("\n" + "="*60 + "\n")

    def _indent_code(self, code_string: str, spaces: int = 4) -> str:
        """Used a to indent and make output lines of code look more neat will be 
        removed for final product as formatting done on web app."""
        indent = " " * spaces
        return "\n".join(f"{indent}{line}" for line in code_string.split("\n"))