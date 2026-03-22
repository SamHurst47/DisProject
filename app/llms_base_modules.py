"""
llms_base_modules.py

Create a base class able to call LLMs of various models 
pulling them from the internet where needed, supporting multiple providers.

Author: Sam Hurst
"""
import json
import time
import requests

from app.base_module import AnalyserModule
from app.code_review_payload import SuggestedChange

class BaseLLMAnalyser(AnalyserModule):
    """
    Base engine for any LLM step.
    Handles local (Ollama) or external (API) models, JSON validation, 
    positive feedback loops, and payload updating.
    """
    def __init__(self, model_name: str, task_name: str, 
                 provider: str = "ollama", # 'ollama' or 'api'
                 host: str = "http://localhost:11434", 
                 api_key: str = None,
                 reflection_iterations: int = 0, 
                 depends_on_static: list = None, 
                 depends_on_llm: list = None):
        
        self.model_name = model_name
        self.task_name = task_name
        self.provider = provider.lower()
        self.host = host
        self.api_key = api_key
        self.reflection_iterations = reflection_iterations
        
        self.depends_on_static = depends_on_static
        self.depends_on_llm = depends_on_llm
        
        # Ollama specific URLs
        self.generate_url = f"{self.host}/api/generate"
        self.tags_url = f"{self.host}/api/tags"
        self.pull_url = f"{self.host}/api/pull"

    def _ensure_model_exists(self):
        """Check if model is present locally (Ollama only)."""
        if self.provider != "ollama":
            return

        try:
            # List current Models 
            tags_response = requests.get(self.tags_url)
            tags_response.raise_for_status()
            
            search_name = self.model_name if ":" in self.model_name else f"{self.model_name}:latest"
            existing_models = [m.get("name") for m in tags_response.json().get("models", [])]

            # Download if not available 
            if search_name not in existing_models and self.model_name not in existing_models:
                print(f"[{self.task_name}] Model '{self.model_name}' not found locally.")
                print(f"Pulling from Ollama registry ...")
                
                # stream=False forces our Python script to wait until the download finishes
                pull_response = requests.post(self.pull_url, json={"name": self.model_name, "stream": False})
                pull_response.raise_for_status()
                
                print(f"[{self.task_name}] Successfully downloaded '{self.model_name}'!")
                
        except Exception as e:
            print(f"[{self.task_name}] Failed to verify or pull model: {e}")
            # Dose not raise so we can let the rest of execution continue

    def build_prompt(self, data) -> str:
        """Subclasses MUST implement this to define their specific job."""
        raise NotImplementedError("Subclasses must build their own prompts!")

    def build_reflection_prompt(self, data, draft_json_string: str) -> str:
        
        return f"""
        You are a strict Principal Software Engineer. 
        You previously drafted these code review suggestions for the following {data.language} code.
        
        Original Code:
        ```
        {data.raw_content}
        ```
        
        Draft Suggestions:
        ```json
        {draft_json_string}
        ```
        
        CRITIQUE TASK:
        1. Remove any suggestions that are false positives or overly pedantic.
        2. Improve the 'suggested_code' fixes to be more robust.
        3. Clarify the 'explanation' fields.
        
        Return ONLY a JSON object containing the final, polished 'suggestions' list.
        """

    def _gather_pipeline_context(self, data) -> str:
        """Collects previously output data from selected modules."""
        context_blocks = []

        # Finds static issues flagged
        if data.static_issues:
            filtered_static = data.static_issues
            if self.depends_on_static: 
                filtered_static = [i for i in data.static_issues if i.tool_name in self.depends_on_static]
            
            if filtered_static:
                context_blocks.append("--- STATIC ANALYSIS FINDINGS ---")
                for issue in filtered_static:
                    context_blocks.append(f"Line {issue.line_number} [{issue.tool_name}]: {issue.message}")
                context_blocks.append("") 

        # Finds LLM issues flagged
        if data.suggested_changes:
            filtered_llm = data.suggested_changes
            if self.depends_on_llm: 
                filtered_llm = [
                    c for c in data.suggested_changes 
                    if any(task.lower() in c.reviewer.lower() for task in self.depends_on_llm)
                ]

            if filtered_llm:
                context_blocks.append("--- PREVIOUS REVIEWER SUGGESTIONS ---")
                for change in filtered_llm:
                    context_blocks.append(f"Lines {change.line_start}-{change.line_end} ({change.reviewer}):")
                    context_blocks.append(f"Problem: {change.explanation}")
                    context_blocks.append(f"Suggested Fix:\n{change.suggested_code}\n")

        if not context_blocks:
            return "No relevant previous context found."

        return "\n".join(context_blocks)


    def _call_llm(self, prompt: str) -> tuple[str, float]:
        """Routes the prompt to the correct backend based on self.provider."""
        if self.provider == "ollama":
            return self._call_ollama_backend(prompt)
        elif self.provider == "api":
            return self._call_api_backend(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _call_ollama_backend(self, prompt: str) -> tuple[str, float]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json" 
        }
        response = requests.post(self.generate_url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "{}"), data.get("eval_duration", 0) / 1e9

    def _call_api_backend(self, prompt: str) -> tuple[str, float]:
        """Calls the Google Gemini API natively."""
        start_time = time.time()
        
        # Clean the key of any accidental spaces or newlines
        clean_key = str(self.api_key).strip()
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json" 
            }
        }
        
        # Inject the clean key directly into the URL parameter
        endpoint = f"{self.host}/v1beta/models/{self.model_name}:generateContent?key={clean_key}"
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        # Prints error code
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            
        response.raise_for_status()
        
        data = response.json()
        
        try:
            result_string = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            print(f"[{self.task_name}] Unexpected API response structure.")
            result_string = "{}" 
            
        duration = time.time() - start_time
        
        return result_string, duration

    def analyse(self, data):
        # check model exists
        self._ensure_model_exists()

        initial_prompt = self.build_prompt(data)
        
        # Self Contained Running engin to stop major pipeline faults
        try:
            print(f"[{self.task_name}] Generating draft review using {self.provider.upper()}...")
            
            current_json_string, total_duration = self._call_llm(initial_prompt)

            for i in range(self.reflection_iterations):
                print(f"[{self.task_name}] Running reflection pass {i + 1}/{self.reflection_iterations}...")
                
                reflection_prompt = self.build_reflection_prompt(data, current_json_string)
                
                current_json_string, step_duration = self._call_llm(reflection_prompt)
                total_duration += step_duration
                
                data.metadata[f"{self.task_name}_reflected_passes"] = self.reflection_iterations

            llm_output = json.loads(current_json_string)
            suggestions = llm_output.get("suggestions", [])

            for item in suggestions:
                suggestion = SuggestedChange(
                    line_start=item.get("line_start", 0),
                    line_end=item.get("line_end", 0),
                    original_code=item.get("original_code", ""),
                    suggested_code=item.get("suggested_code", ""),
                    explanation=item.get("explanation", ""),
                    reviewer=f"{self.provider.title()} - {self.task_name} ({self.model_name})" + (" [Reflected]" if self.reflection_iterations else "")
                )
                data.add_suggestion(suggestion)

            metric_key = self.task_name.lower().replace(" ", "_")
            data.metadata[f"{metric_key}_total_duration_secs"] = total_duration

        except Exception as e:
            print(f"[{self.task_name}] Analyser failed: {e}")
            data.metadata[f"{self.task_name}_error"] = str(e)

        return data