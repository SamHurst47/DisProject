"""
main.py

Used as temporary file for managing  execution and testing 
will be replaced once web application built

Author: Sam Hurst
"""
import os
from dotenv import load_dotenv
from app.pipeline import Pipeline
from app.input_modules import TextInputModule
from app.output_modules import PrintOutputModule
from app.static_modules import TodoAnalyser, PylintAnalyzer, PygountAnalyzer
from app.llms_modules import CommentReviewAnalyser, LogicErrorAnalyser, CoordinatorAnalyser

load_dotenv()

def build_pipeline(input_module, analysers, output_module):
    """
    Builder function that assembles the pipeline. 
    The web app will eventually import and use this directly!
    """
    pipeline = Pipeline(
        input_module=input_module,
        output_module=output_module
    )

    for analyser in analysers:
        pipeline.add_module(analyser)

    return pipeline


def main():

    # Change to other mode simple testing atm
    current_input = TextInputModule(
        text="""
            def is_even(num):
                # TODO hello
                #Check if num is even: divisible by 2 with no remainder.
                #Uses modulo operator: even if num % 2 == 0.
                #Handles positives correctly (intended logic).
                
                return num % 2  # BUG: Returns 0/1 (truthy always except multiples of 2? No—in Python non-zero is True, so positives always "even"!

            # Test cases
            print(is_even(4))   # Prints True (correct)
            print(is_even(5))   # Prints True (WRONG: should be False)
            print(is_even(-3))  # Prints True (quirky, but bugged anyway)
            """,
        filename="test.py", 
        language="python"
    )
    
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")

    # Could upgrade this to be dynamic but will need updating anyway when build web application 

    active_analysers = [
        TodoAnalyser(), # Runs instantly (Python)
        PylintAnalyzer(),
        PygountAnalyzer(),
        CommentReviewAnalyser(model_name="llama3", reflection_iterations=1,depends_on_static=["Pylint"]), # Runs fast (Small LLM)
        LogicErrorAnalyser(model_name="codellama:13b", reflection_iterations=0,depends_on_llm=["Comment Review"]), # Runs slower, but does deep thinking (Large LLM)
        CoordinatorAnalyser(
            model_name="gemini-2.5-flash", 
            provider="api",
            host="https://generativelanguage.googleapis.com",
            api_key=GEMINI_KEY, 
            reflection_iterations=1,
            depends_on_static=["Pylint"],
            depends_on_llm=["Comment Review"]
        )
    ]
    
    current_output = PrintOutputModule()

    print(f"Building pipeline with {len(active_analysers)} analysers...")
    pipeline = build_pipeline(
        input_module=current_input,
        analysers=active_analysers,
        output_module=current_output
    )

    print("Running pipeline...\n" + "-"*30)
    final_payload = pipeline.run()
    
    #print(final_payload)


if __name__ == "__main__":
    main()
