"""
llms_modules.py

Builds off the base class BaseOllamaAnalyser and future APIAnalyser to call 
create call for the LLMs to review the code base each for specific functions

Author: Sam Hurst
"""
from app.llms_base_modules import BaseOllamaAnalyser

class CommentReviewAnalyser(BaseOllamaAnalyser):
    """Focuses on suggesting reviews for comment based issues"""
    
    def __init__(self, model_name: str = "llama3", reflection_iterations: int = 0, 
                 depends_on_static: list = None, depends_on_llm: list = None):
        super().__init__(
            model_name=model_name, 
            task_name="Comment Review",
            reflection_iterations=reflection_iterations,
            depends_on_static=depends_on_static,
            depends_on_llm=depends_on_llm
        )

    def build_prompt(self, data) -> str:
        previous_context = self._gather_pipeline_context(data)
        
        return f"""
        You are a code reviewer focusing ONLY on documentation and comments.
        Below is the original {data.language} code, followed by relevant findings from previous tools.
        
        {previous_context}
        
        Review the code. Are there missing docstrings? Unclear comments?
        
        Return JSON with a 'suggestions' list (keys: line_start, line_end, original_code, suggested_code, explanation).
        Code:
        ```
        {data.raw_content}
        ```
        """
    
class LogicErrorAnalyser(BaseOllamaAnalyser):
    """Focuses on bugs, edge cases, and structural errors."""
    
    def __init__(self, model_name: str = "codellama", reflection_iterations: int = 0,
                 depends_on_static: list = None, depends_on_llm: list = None):
        super().__init__(
            model_name=model_name, 
            task_name="Logic and Error Check",
            reflection_iterations=reflection_iterations,
            depends_on_static=depends_on_static,
            depends_on_llm=depends_on_llm
        )

    def build_prompt(self, data) -> str:
        previous_context = self._gather_pipeline_context(data)

        return f"""
        You are a senior engineer hunting for logical bugs and edge cases. 
        Ignore missing comments. Focus strictly on structure, security, and errors.
        
        Consider these findings from previous static tools and reviewers:
        {previous_context}
        
        Return JSON with a 'suggestions' list (keys: line_start, line_end, original_code, suggested_code, explanation).
        Code:
        ```
        {data.raw_content}
        ```
        """