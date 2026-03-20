"""
llms_modules.py

Builds off the base class BaseLLMAnalyser to create calls for the LLMs 
to review the code base, each for specific functions.

Author: Sam Hurst
"""
from app.llms_base_modules import BaseLLMAnalyser

class CommentReviewAnalyser(BaseLLMAnalyser):
    """Focuses on suggesting reviews for comment based issues"""
    
    def __init__(self, model_name: str = "llama3", 
                 provider: str = "ollama", 
                 host: str = "http://localhost:11434", 
                 api_key: str = None,
                 reflection_iterations: int = 0, 
                 depends_on_static: list = None, 
                 depends_on_llm: list = None):
        super().__init__(
            model_name=model_name, 
            task_name="Comment Review",
            provider=provider,
            host=host,
            api_key=api_key,
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
    
class LogicErrorAnalyser(BaseLLMAnalyser):
    """Focuses on bugs, edge cases, and structural errors."""
    
    def __init__(self, model_name: str = "codellama", 
                 provider: str = "ollama", 
                 host: str = "http://localhost:11434", 
                 api_key: str = None,
                 reflection_iterations: int = 0,
                 depends_on_static: list = None, 
                 depends_on_llm: list = None):
        super().__init__(
            model_name=model_name, 
            task_name="Logic and Error Check",
            provider=provider,
            host=host,
            api_key=api_key,
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
    

class CoordinatorAnalyser(BaseLLMAnalyser):
    """
    Acts as the Lead Engineer/Coordinator. 
    Reads the code AND all selected module findings, resolves conflicts, 
    and synthesizes a final, authoritative code review.
    """
    
    def __init__(self, model_name: str = "llama3", 
                 provider: str = "ollama", 
                 host: str = "http://localhost:11434", 
                 api_key: str = None,
                 reflection_iterations: int = 0,
                 depends_on_static: list = None, 
                 depends_on_llm: list = None):
        super().__init__(
            model_name=model_name, 
            task_name="Final Coordinator Synthesis",
            provider=provider,
            host=host,
            api_key=api_key,
            reflection_iterations=reflection_iterations,
            depends_on_static=depends_on_static,
            depends_on_llm=depends_on_llm
        )

    def build_prompt(self, data) -> str:
        # Automatically sucks in all the outputs from the earlier modules in the pipeline
        previous_context = self._gather_pipeline_context(data)

        return f"""
        You are the Lead Code Review Coordinator.
        Below is the original {data.language} code, followed by a list of findings 
        from various automated linters and specialized AI reviewers (the "junior" reviewers).
        
        {previous_context}
        
        CRITIQUE TASK:
        1. Review the context above against the original code. 
        2. Filter out false positives and pedantic noise.
        3. Resolve any conflicting advice between different tools.
        4. Synthesize the absolute best, most robust code improvements.
        
        Return ONLY a JSON object with a single key 'suggestions' containing a list of objects.
        Each object must have exactly these keys:
        - "line_start": (int) the starting line number
        - "line_end": (int) the ending line number
        - "original_code": (str) the snippet being replaced
        - "suggested_code": (str) the corrected snippet
        - "explanation": (str) why this change is needed and how it resolves the previous feedback
        
        Original Code:
        ```
        {data.raw_content}
        ```
        """