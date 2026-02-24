"""
pipeline.py

Used to define the basics pipeline and execute it with error catches 
to be able to diagnoses issue with execution 

Author: Sam Hurst
"""

import traceback
from typing import List

from app.base_module import InputModule, OutputModule, AnalyzerModule
# from app.code_review_payload import CodeReviewPayload # incases needed later 

class Pipeline:
    def __init__(self, input_module: InputModule, output_module: OutputModule):
        """
        Takes inputs and initialise the module with the chosen input method and the analytics in the middle.
        """
        self.input_module = input_module
        self.output_module = output_module
        self.middle_modules: List[AnalyzerModule] = []

    def add_module(self, module: AnalyzerModule):
        """
        Simple procedure to add tools to the analytics pipeline
        """
        self.middle_modules.append(module)

    def run(self):
        """
        Runs pipeline in safe way to ensure any error do not crash 
        program and all middle modules are run correctly in order.
        """
        # Running input function with Error checking of input
        try:
            data = self.input_module.process()
        except Exception as e:
            print(f"ERROR: Failed to input: {e}")
            raise

        # Running analytics functions with Error checking to ensure
        for module in self.middle_modules:
            try:
                data = module.process(data)
            except Exception as e:
                # Used to catch and log error while continuing execution
                module_name = module.__class__.__name__
                print(f"WARNING: Module {module_name} failed. Skipping. Error: {e}")
                
                # Creates a item for errors if one is not already present in error section
                if "pipeline_errors" not in data.metadata:
                    data.metadata["pipeline_errors"] = []
                
                data.metadata["pipeline_errors"].append({
                    "module": module_name,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

        # Running output function with Error checking of output
        try:
            self.output_module.process(data)
        except Exception as e:
            print(f"ERROR: Output module failed: {e}")

        return data