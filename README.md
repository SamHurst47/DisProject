# DisProject — AI Code Review Pipeline

The aim of this project is to design and justify an architectural framework and prototype pipeline for integrating multiple LLMs into a structured code review workflow for a single programming language, drawing on prior work in modern code review, LLM assisted programming, and software pipeline design.

***

## Key Features

- Dynamic pipeline builder via a Streamlit web interface
- Multi-agent architecture (logic, security, performance, coordination)
- Hybrid LLM support (local + cloud)
- Integration with static analysis tools
- Interactive review with diff-based suggestion approval
- Batch testing and evaluation tooling

***

## Set Up

### Prerequisites

- Python 3 
- Ollama (for local LLMs)
- API key (for cloud-based agents)


### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/SamHurst47/DisProject.git
cd DisProject
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_key_here
```

Install Ollama to run local models such as `llama3`.

***

## How to Run

### 1. Web Application (Primary Interface)

Launch the Streamlit UI to build and run pipelines interactively:

```bash
streamlit run app_ui.py
```


***

### 2. Experimental \& Utility Scripts

Run these from the root directory:

- **optimising_pipeline.py**
Used for prompt tuning and pipeline configuration experiments

```bash
python optimising_pipeline.py
```

- **testing_suite.py**
Executes batch experiments across multiple pipeline configurations and exports results to CSV

```bash
python testing_suite.py
```

***

## Project Structure

### Root Directory

- **app_ui.py** — Streamlit interface for pipeline configuration and execution
- **main.py** — Lightweight console-based execution manager
- **requirements.txt** — Python dependencies


### Core Application (`/app`)

- **pipeline.py** — Core orchestration engine
- **llms_modules.py** — LLM agents (logic, security, performance, coordinator)
- **static_modules.py** — Static analysis wrappers (Pylint, Bandit, regex tools)
- **input_modules.py** — Input handling (text/file ingestion)
- **output_modules.py** — Output formatting and delivery

***

## Testing

Run the test suite:

```bash
pytest test_pipeline.py
```

The `testing_suite.py` script was used for large-scale experimental evaluation across pipeline configurations.

***

## Legal \& Usage Notice

By using this system, you agree to the following:

### Data Responsibility \& GDPR

- Do not upload code containing personal or sensitive data
- You must have the legal right to analyse any submitted code


### Usage Terms

- The system must not be used for exploitative purposes
- This project depends on third-party tools and APIs; ensure compliance with their licenses (e.g., Gemini API usage limits)
- Commercial use will require additional licensing review


### Social Impact \& Accountability

- LLM outputs are not guaranteed to be correct or unbiased
- The system is intended to assist, not replace, human code review
- Over-reliance may reduce manual review skills

***


