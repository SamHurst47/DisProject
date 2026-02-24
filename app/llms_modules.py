"""
llms_modules.py

Builds off the base class BaseOllamaAnalyser and future APIAnalyser to call 
create call for the LLMs to review the code base each for specific functions

Author: Sam Hurst
"""
from app.llms_base_modules import BaseOllamaAnalyser

class CommentReviewAnalyser(BaseOllamaAnalyser):
    """Focuses on suggesting reviews for comment based issues"""
    
    def __init__(self, model_name: str = "llama3"):
        super().__init__(model_name=model_name, task_name="Comment Review")

    # Build in self authenticate to check referring to correct info 
    def build_prompt(self, data) -> str:
        return f"""
        You are a code reviewer focusing ONLY on documentation and comments.
        Review this {data.language} code. Are there missing docstrings? Unclear comments?
        
        Return JSON with a 'suggestions' list (keys: line_start, line_end, original_code, suggested_code, explanation).
        Code:
        ```
        {data.raw_content}
        ```
        """

class LogicErrorAnalyser(BaseOllamaAnalyser):
    """Focuses on bugs, edge cases, and structural errors."""
    
    def __init__(self, model_name: str = "codellama"):
        super().__init__(model_name=model_name, task_name="Logic and Error Check")

    def build_prompt(self, data) -> str:
        # Can feed in static tool info
        static_context = ""
        if data.static_issues:
            static_context = "Static tools found these potential issues:\n" + \
                             "\n".join([f"- Line {i.line_number}: {i.message}" for i in data.static_issues])

        return f"""
        You are a senior engineer hunting for logical bugs and edge cases. 
        Ignore missing comments. Focus strictly on structure, security, and errors.
        {static_context}
        
        Return JSON with a 'suggestions' list (keys: line_start, line_end, original_code, suggested_code, explanation).
        Code:
        ```
        {data.raw_content}
        ```
        """