"""
llms_base_modules.py

Create a base class able to call LLMs of various models 
pulling them form the intern where needed.

Author: Sam Hurst
"""
import json
import requests

from app.base_module import AnalyserModule
from app.code_review_payload import SuggestedChange

class BaseOllamaAnalyser(AnalyserModule):
    """
    Base engine for any local Ollama LLM step.
    Handles auto-pulling missing models, HTTP requests, JSON validation, 
    and payload updating.
    """
    def __init__(self, model_name: str, task_name: str, host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.task_name = task_name
        self.host = host
        self.generate_url = f"{self.host}/api/generate"
        self.tags_url = f"{self.host}/api/tags"
        self.pull_url = f"{self.host}/api/pull"

    def _ensure_model_exists(self):
        """Check is model is present locally or need pulling form internet."""
        try:
            # List current Models 
            tags_response = requests.get(self.tags_url)
            tags_response.raise_for_status()
            
            search_name = self.model_name if ":" in self.model_name else f"{self.model_name}:latest"
            existing_models = [m.get("name") for m in tags_response.json().get("models", [])]

            # Download if not available 
            if search_name not in existing_models and self.model_name not in existing_models:
                print(f" [{self.task_name}] Model '{self.model_name}' not found locally.")
                print(f" Pulling from Ollama registry ...")
                
                # stream=False forces our Python script to wait until the download finishes
                pull_response = requests.post(self.pull_url, json={"name": self.model_name, "stream": False})
                pull_response.raise_for_status()
                
                print(f" [{self.task_name}] Successfully downloaded '{self.model_name}'!")
                
        except Exception as e:
            print(f"⚠️ [{self.task_name}] Failed to verify or pull model: {e}")
            # Dose not raise so we can let the rest of execution continue

    def build_prompt(self, data) -> str:
        """Subclasses MUST implement this to define their specific job."""
        raise NotImplementedError("Subclasses must build their own prompts!")

    def analyse(self, data):
        # check model exists
        self._ensure_model_exists()

        # Collects prompt defined in initialization 
        prompt = self.build_prompt(data)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json" 
        }

        try:
            # 
            response = requests.post(self.generate_url, json=payload)
            response.raise_for_status()
            result_data = response.json()
            
            # Parse the json response 
            llm_output = json.loads(result_data.get("response", "{}"))
            suggestions = llm_output.get("suggestions", [])

            # Fills the suggestion data class out and added to list of issues
            for item in suggestions:
                suggestion = SuggestedChange(
                    line_start=item.get("line_start", 0),
                    line_end=item.get("line_end", 0),
                    original_code=item.get("original_code", ""),
                    suggested_code=item.get("suggested_code", ""),
                    explanation=item.get("explanation", ""),
                    reviewer=f"Ollama - {self.task_name} ({self.model_name})"
                )
                data.add_suggestion(suggestion)

            # Recodes execution in metadata 
            metric_key = self.task_name.lower().replace(" ", "_")
            data.metadata[f"{metric_key}_duration_secs"] = result_data.get("eval_duration", 0) / 1e9

        except Exception as e:
            # Catch bad JSON, connection errors, etc., and log them to metadata
            print(f"❌ [{self.task_name}] Analyser failed: {e}")
            data.metadata[f"{self.task_name}_error"] = str(e)

        # Always return the data structure for next module to orate on
        return data