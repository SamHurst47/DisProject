"""
testing.py

Testing suit for running the different configurations of the pipeline to test
the differing Architectural features and compare the outputs.
Author: Sam Hurst
"""
import os
import csv
import time
from datetime import datetime
from dotenv import load_dotenv

# Import the core pipeline components
from app.pipeline import Pipeline
from app.input_modules import TextInputModule
from app.base_module import OutputModule

# Import all our analyzers
from app.static_modules import (
    PylintAnalyzer, BanditAnalyzer, RegexSecretScanner, ComplexityAnalyzer
)
from app.llms_modules import (
    CommentReviewAnalyser, LogicErrorAnalyser, 
    SecurityAuditAnalyser, PerformanceOptimisationAnalyser, CoordinatorAnalyser
)

# Load environment variables
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Data set Loader
def load_testing_data(relative_path="testing_data"):
    dataset = {}
    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    target_directory = os.path.normpath(os.path.join(current_script_dir, relative_path))
    
    print(f"Searching for test files in: {target_directory}")
    
    if not os.path.exists(target_directory):
        print(f"ERROR: Could not find the folder at {target_directory}")
        return dataset
        
    all_python_files = []
    
    # Search Collect all files
    for root, dirs, files in os.walk(target_directory):
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                relative_file_path = os.path.relpath(filepath, target_directory)
                all_python_files.append((relative_file_path, filepath))
                    
    # Alphabetize to keep files grouped by their Sample folders
    all_python_files.sort(key=lambda x: x[0])
    
    # Load them into the dictionary
    for relative_path, absolute_path in all_python_files:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            dataset[relative_path] = f.read()
                
    if dataset:
        print(f"Successfully loaded {len(dataset)} files into the testing suit.")
        print("File processing:")
        
        top_level_folders = []
        for file_path in dataset.keys():
            # Get just the first folder name (e.g., 'Sample1' from 'Sample1/docs/conf.py')
            folder = file_path.replace('\\', '/').split('/')[0] 
            
            if folder not in top_level_folders:
                top_level_folders.append(folder)
                
        # Print the clean list of directories
        for i, folder in enumerate(top_level_folders, start=1):
            print(f"      {i}. {folder}")
        print("\n")
        
    else:
        print("Found the folders, but couldn't find any .py files inside them.")
        
    return dataset

DATASET = load_testing_data()

# Checkpointing module 
class CSVCheckpointOutput(OutputModule):
    def __init__(self, csv_filename, config_name):
        self.csv_filename = csv_filename
        self.config_name = config_name
        
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Config_Name", "File_Name", "Issue_Category", 
                    "Line_Start", "Line_End", "Tool_or_Reviewer", "Original_Code", 
                    "Suggested_Code", "Explanation_or_Message", "Severity", 
                    "Total_Pipeline_Duration_Secs"
                ])

    def write(self, data): 
        total_duration = sum([v for k, v in data.metadata.items() if "duration" in k])
        
        with open(self.csv_filename, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for issue in data.static_issues:
                writer.writerow([
                    timestamp, self.config_name, data.filename, "STATIC",
                    issue.line_number, issue.line_number, issue.tool_name, 
                    "", "", issue.message, issue.severity, round(total_duration, 2)
                ])
                
            for change in data.suggested_changes:
                writer.writerow([
                    timestamp, self.config_name, data.filename, "LLM",
                    change.line_start, change.line_end, change.reviewer,
                    change.original_code, change.suggested_code, 
                    change.explanation, "N/A", round(total_duration, 2)
                ])
                
        print(f"  [+] Checkpointed results for {data.filename} to CSV.")
        return data

# Architectural Configurations
def get_configurations():
    return {

        "Test_1_Static_Only": [
            PylintAnalyzer(),
            BanditAnalyzer(),
            RegexSecretScanner(),
            ComplexityAnalyzer()
        ],

        "Test_2A_Single_Generalist": [
            PylintAnalyzer(),
            LogicErrorAnalyser(model_name="llama3", provider="ollama") 
        ],

        "Test_2B_Specialized_Roles": [
            PylintAnalyzer(),
            LogicErrorAnalyser(model_name="llama3", provider="ollama"),
            SecurityAuditAnalyser(model_name="codellama:13b", provider="ollama"),
            PerformanceOptimisationAnalyser(model_name="llama3", provider="ollama")
        ],

        "Test_3_Iterative_Feedback": [
            PylintAnalyzer(),
            LogicErrorAnalyser(
                model_name="deepseek-r1:8b", 
                provider="ollama", 
                reflection_iterations=2 
            ),
            SecurityAuditAnalyser(
                model_name="codellama:13b", 
                provider="ollama", 
                reflection_iterations=2 
            ),
            PerformanceOptimisationAnalyser(
                model_name="llama3", 
                provider="ollama", 
                reflection_iterations=2 
            )
        ],

        "Test_4_Hybrid_Deployment": [
            PylintAnalyzer(),
            BanditAnalyzer(),
            LogicErrorAnalyser(model_name="llama3", provider="ollama"),
            SecurityAuditAnalyser(
                model_name="gemini-2.5-flash-lite", 
                provider="api",
                host="https://generativelanguage.googleapis.com",
                api_key=GEMINI_KEY
            )
        ],

        "Test_5_Coordinator": [
            PylintAnalyzer(),
            BanditAnalyzer(),
            LogicErrorAnalyser(model_name="llama3", provider="ollama"),
            SecurityAuditAnalyser(
                model_name="gemini-2.5-flash-lite", 
                provider="api",
                host="https://generativelanguage.googleapis.com",
                api_key=GEMINI_KEY
            ),
            CoordinatorAnalyser(
                model_name="gemini-2.5-flash-lite", 
                provider="api", 
                host="https://generativelanguage.googleapis.com", 
                api_key=GEMINI_KEY,
                reflection_iterations=0,
                depends_on_static=["Pylint", "Bandit"],
                depends_on_llm=["Logic Error", "Security Audit"]
            )
        ],

        # Optimal Tests

        "Optimal_1_Pipeline_Balanced": [
            PylintAnalyzer(),
            BanditAnalyzer(),
            RegexSecretScanner(),
            LogicErrorAnalyser(model_name="llama3", provider="ollama"),
            PerformanceOptimisationAnalyser(model_name="gemma4:e4b", provider="ollama"),
            CoordinatorAnalyser(
                model_name="gemini-2.5-flash-lite", 
                provider="api", 
                host="https://generativelanguage.googleapis.com", 
                api_key=GEMINI_KEY,
                reflection_iterations=1, 
                depends_on_static=["Pylint", "Bandit", "SecretScanner"],
                depends_on_llm=["Logic Error", "Performance Engineering"] 
            )
        ],

        "Optimal_2_Pipeline_Maximum": [
            PylintAnalyzer(),
            BanditAnalyzer(),
            RegexSecretScanner(),
            ComplexityAnalyzer(),
            CommentReviewAnalyser(
                model_name="gemma4:e2b", provider="ollama"
            ),
            LogicErrorAnalyser(
                model_name="gemini-2.5-flash-lite", provider="api", host="https://generativelanguage.googleapis.com", api_key=GEMINI_KEY
            ),
            SecurityAuditAnalyser(
                model_name="gemini-2.5-flash-lite", provider="api", host="https://generativelanguage.googleapis.com", api_key=GEMINI_KEY
            ),
            CoordinatorAnalyser(
                model_name="gemini-2.5-flash-lite",
                provider="api", 
                host="https://generativelanguage.googleapis.com", 
                api_key=GEMINI_KEY,
                reflection_iterations=2, 
                depends_on_static=["Pylint", "Bandit", "SecretScanner", "ComplexityScanner"],
                depends_on_llm=["Comment Review", "Logic Error", "Security Audit"]
            )
        ],
        
        "Optimal_3_Pipeline_Tiered": [
            PylintAnalyzer(),
            BanditAnalyzer(),
            RegexSecretScanner(),
            ComplexityAnalyzer(),
            LogicErrorAnalyser(
                model_name="llama3", 
                provider="ollama",
                depends_on_static=["Pylint", "ComplexityScanner"]
            ),
            PerformanceOptimisationAnalyser(
                model_name="deepseek-r1:8b", 
                provider="ollama",
                depends_on_static=["ComplexityScanner"] 
            ),
            SecurityAuditAnalyser(
                model_name="gemini-2.5-flash-lite", 
                provider="api",
                host="https://generativelanguage.googleapis.com",
                api_key=GEMINI_KEY,
                depends_on_static=["Bandit", "SecretScanner"] 
            ),
            CoordinatorAnalyser(
                model_name="gemini-2.5-flash-lite", 
                provider="api", 
                host="https://generativelanguage.googleapis.com",
                api_key=GEMINI_KEY, 
                reflection_iterations=1, 
                depends_on_static=["Pylint", "Bandit", "SecretScanner", "ComplexityScanner"],
                depends_on_llm=["Logic Error", "Security Audit", "Performance Engineering"]
            )
        ]
        
    }

# Finds completed test to not rerun
def get_completed_runs(csv_filename):
    completed = set()
    if not os.path.exists(csv_filename):
        return completed
        
    with open(csv_filename, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None) 
        
        if not header: 
            return completed
            
        try:
            config_idx = header.index("Config_Name")
            file_idx = header.index("File_Name")
        except ValueError:
            return completed 
            
        for row in reader:
            if len(row) > max(config_idx, file_idx):
                completed.add((row[config_idx], row[file_idx]))
                
    return completed

# Execution
def run_test():
    if not DATASET:
        print("Testing aborted: No dataset loaded. Please check the folder path.")
        return

    configs = get_configurations()
    
    # Guarantee the output directory exists
    output_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "pipeline_testing_output"))
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting Testing")
    print(f"Output files will be saved in: ./{output_dir}/")
    
    # Use enumerate to count the configs 
    for index, (config_name, analyzers) in enumerate(configs.items(), start=1):
        
        # Create the unique filename: "pipeline_testing_output/test_config_1.csv"
        csv_file = os.path.join(output_dir, f"test_config_{index}.csv")
        
        # Read resume data JUST for this specific config file
        completed_runs = get_completed_runs(csv_file)
        
        print(f" TESTING CONFIGURATION {index}: {config_name}")
        print("\n")

        if completed_runs:
            print(f" Resuming from checkpoint: Found existing data in {csv_file.split('/')[-1]}")
        
        for filename, code_content in DATASET.items():
            
            if (config_name, filename) in completed_runs:
                print(f"Skipping {filename} (Already processed in this config)")
                continue
                
            print(f"\n  Analyzing file: {filename}...")
            
            input_mod = TextInputModule(text=code_content.strip(), filename=filename, language="python")
            output_mod = CSVCheckpointOutput(csv_filename=csv_file, config_name=config_name)
            
            pipeline = Pipeline(input_module=input_mod, output_module=output_mod)
            for analyzer in analyzers:
                pipeline.add_module(analyzer)
                
            start_time = time.time()
            try:
                pipeline.run()
            except Exception as e:
                print(f"Pipeline failed on {filename}: {e}")
                
            run_time = time.time() - start_time
            print(f"Finished in {run_time:.2f} seconds.")
            
            time.sleep(2)

if __name__ == "__main__":
    run_test()