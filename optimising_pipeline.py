"""
optimising_pipeline.py

used as an active test file to help optimise the pice within the pipeline such as 
prompt and configuration before testing to further understand the how to maximises architectures features.

Author: Sam Hurst
"""
import os
from dotenv import load_dotenv

from app.pipeline import Pipeline
from app.input_modules import TextInputModule
from app.base_module import OutputModule
from app.static_modules import PylintAnalyzer
from app.static_modules import (
    PylintAnalyzer,
    PygountAnalyzer,     TodoAnalyzer     
)
from app.llms_modules import (
    CommentReviewAnalyser,           
    GeneralReviewAnalyser,           
    LogicErrorAnalyser,              
    SecurityAuditAnalyser,           
    PerformanceOptimisationAnalyser, 
    TestEngineerAnalyser,           
    ComplianceOfficerAnalyser,       
    CoordinatorAnalyser            
)

# Load API keys
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Set up demo data to be inputted
code_for_review = """
import sqlite3
import time

# TODO: Fix this function later
def process_user_data(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Logic / Security flaw: SQL Injection risk
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    user = cursor.fetchone()
    
    # Security flaw: Hardcoded secret key
    api_key = "AIzaSyB-SuperSecretKey-DO-NOT-SHARE"
    
    # Performance flaw: Inefficient loop doing nothing useful
    results = []
    for i in range(10000):
        time.sleep(0.001)
        results.append(i * 2)
        
    return user, results
"""
### Test 1: Let's see if the Security agent catches the hardcoded key
### Test 2: Let's see if Performance catches the bad loop
### Test 3: See if the Coordinator can synthesize it all using Gemini

# Sets up subclass to output in easy text formate for viewing optimisation.
class DebugOutputModule(OutputModule):
    def write(self, data):
        print("Pipeline Output")

        # Print Static Issues
        print("\n[Static Issues]")
        if not data.static_issues:
            print("  None found.")
        else:
            for issue in data.static_issues:
                print(f"  - Line {issue.line_number}: {issue.message}")

        # Print LLM Suggestions
        print("\n[LLM SUGGESTIONS]")
        if not data.suggested_changes:
            print("  None found.")
        else:
            for change in data.suggested_changes:
                print(f"\n  Reviewer: {change.reviewer}")
                print(f"  Lines: {change.line_start}-{change.line_end}")
                # Using repr() to show raw strings as requested
                print(f"  Original:  {repr(change.original_code)}")
                print(f"  Suggested: {repr(change.suggested_code)}")
                print(f"  Reason:    {change.explanation}")

        # Print Metadata & Timings
        print("\n[METADATA & TIMINGS]")
        if not data.metadata:
            print("  None recorded.")
        else:
            for k, v in data.metadata.items():
                # Logic to format durations to 2 decimal places
                if "duration" in k.lower() and isinstance(v, (int, float)):
                    print(f"  - {k}: {v:.2f} seconds")
                else:
                    print(f"  - {k}: {v}")
             
        return data


def main():
    # Sets up input functionality
    test_input = TextInputModule(
        text=code_for_review.strip(), 
        filename="bad_code.py", 
        language="python"
    )
    debug_output = DebugOutputModule()
    # Adds module's and configs to list of use 
    test_analysers = [
        PylintAnalyzer(),
        SecurityAuditAnalyser(
            model_name="llama3", 
            provider="ollama"
        ),
        PerformanceOptimisationAnalyser(
            model_name="llama3", 
            provider="ollama"
        ),
        CoordinatorAnalyser(
            model_name="gemini-2.5-flash",
            provider="api",
            api_key=GEMINI_KEY,
            host="https://generativelanguage.googleapis.com",            
            reflection_iterations=0,
            depends_on_static=["Pylint"],
            depends_on_llm=["Security Audit", "Performance Engineering"]
        )
    ]
    # Creates pipeline 
    pipeline = Pipeline(input_module=test_input, output_module=debug_output)
    # Added analyser modules 
    for analyzer in test_analysers:
        pipeline.add_module(analyzer)
    # Comment at start of Code 
    print("Running optimization pipeline...\n")
    pipeline.run()

if __name__ == "__main__":
    main()