"""
main.py

Used as temporary file for managing  execution and testing 
will be replaced once web application built

Author: Sam Hurst
"""

from app.pipeline import Pipeline
from app.input_modules import TextInputModule
from app.output_modules import PrintOutputModule
from app.static_modules import Static1

def build_pipeline(input_module, analyzers, output_module):
    """
    Builder function that assembles the pipeline. 
    The web app will eventually import and use this directly!
    """
    pipeline = Pipeline(
        input_module=input_module,
        output_module=output_module
    )

    for analyzer in analyzers:
        pipeline.add_module(analyzer)

    return pipeline


def main():

    # Change to other mode simple testing atm
    current_input = TextInputModule(
        text="def bad_code():\n  pass # TODO fix this", 
        filename="test.py", 
        language="python"
    )
    
    # Could upgrade this to be dynamic but will need updating anyway when build web application 
    active_analyzers = [
        Static1(),
        # Flake8Analyzer(),
        # BanditAnalyzer(),
        # LLMReviewAnalyzer(model="gemini-3.1") 
    ]
    
    current_output = PrintOutputModule()

    print(f"Building pipeline with {len(active_analyzers)} analyzers...")
    pipeline = build_pipeline(
        input_module=current_input,
        analyzers=active_analyzers,
        output_module=current_output
    )

    print("Running pipeline...\n" + "-"*30)
    final_payload = pipeline.run()
    
    #print(final_payload)


if __name__ == "__main__":
    main()