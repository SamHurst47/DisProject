"""
app_ui.py

Serves as a bridge between the pipeline's core functionality and the web interface's configuration and output components.

Author: Sam Hurst
"""
import streamlit as st
import pandas as pd
import time
import os
import uuid
import subprocess
from dotenv import load_dotenv

# Import the core pipeline components
from app.pipeline import Pipeline
from app.input_modules import TextInputModule
from app.base_module import OutputModule

# Import all analyzers directly from your modules
from app.static_modules import (
    PylintAnalyzer, BanditAnalyzer, RegexSecretScanner, ComplexityAnalyzer
)
from app.llms_modules import (
    CommentReviewAnalyser, LogicErrorAnalyser, 
    SecurityAuditAnalyser, PerformanceOptimisationAnalyser, 
    CoordinatorAnalyser
)

# Load environment variables
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Local Model Name Collector
@st.cache_data(ttl=60) # Caches the result for 60 seconds so the UI doesn't lag
def get_local_ollama_models():
    """Runs 'ollama list' in the terminal and parses the available models."""
    try:
        # Execute the terminal command
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        models = []
        # Skip the first line (the header: NAME ID SIZE MODIFIED)
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0]) # The model name is the first column
        
        # Add custom input so more models cna bne added by the user
        models.append("Custom...")
        return models
    except (subprocess.CalledProcessError, FileNotFoundError):
        # FATAL ERROR: Halt the entire application
        st.error("CRITICAL ERROR: Ollama is not running or not installed.**\n\nThis application requires Ollama to host local LLM agents. Please install Ollama from [ollama.com](https://ollama.com/), ensure the background service is running, and then refresh this page.")
        st.stop()

# Instantiates the output module responsible for routing results to the web user interface.
class UIOutputModule(OutputModule):
    def write(self, data):
        return data

# WEB PAGE CREATION

# Sets the Ui Config
st.set_page_config(page_title="LLM Pipeline Builder", layout="wide")

if "pipeline_modules" not in st.session_state:
    st.session_state.pipeline_modules = []

# --- NEW: State for Interactive Review ---
if "review_active" not in st.session_state:
    st.session_state.review_active = False
    st.session_state.suggestions = []
    st.session_state.static_issues = []
    st.session_state.decisions = {} # Tracks "pending", "accepted", or "declined"
    st.session_state.original_code = ""
    st.session_state.filename = ""

# Module Definitions Dictionary
AVAILABLE_MODULES = {
    # --- STATIC TOOLS ---
    "Static: Pylint": {"class": PylintAnalyzer, "type": "static"},
    "Static: Bandit": {"class": BanditAnalyzer, "type": "static"},
    "Static: Secret Scanner": {"class": RegexSecretScanner, "type": "static"},
    "Static: Complexity": {"class": ComplexityAnalyzer, "type": "static"},
    
    # --- LLM AGENTS ---
    "LLM: Comment Reviewer": {"class": CommentReviewAnalyser, "type": "llm"},
    "LLM: Logic Error Agent": {"class": LogicErrorAnalyser, "type": "llm"},
    "LLM: Security Audit Agent": {"class": SecurityAuditAnalyser, "type": "llm"},
    "LLM: Performance Agent": {"class": PerformanceOptimisationAnalyser, "type": "llm"},
    "LLM: Final Coordinator": {"class": CoordinatorAnalyser, "type": "llm"}
}

st.title("Dynamic Architecture Builder")
st.markdown("Build your custom multi-agent pipeline top-to-bottom, configure each node, and execute.")

# File upload and module configuration: add display modules
col_upload, col_add = st.columns(2)

# File Upload
code_content = None
with col_upload:
    st.subheader("1. Target Code")
    uploaded_file = st.file_uploader("Upload Python File (.py)", type=["py"], label_visibility="collapsed")
    if uploaded_file:
        code_content = uploaded_file.getvalue().decode("utf-8")

# Module add to pipeline 
with col_add:
    st.subheader("2. Add to Pipeline")
    selected_new_module = st.selectbox("Select a module to append:", list(AVAILABLE_MODULES.keys()), label_visibility="collapsed")
    if st.button("➕ Add Module", type="secondary"):
        st.session_state.pipeline_modules.append({
            "id": str(uuid.uuid4()),
            "name": selected_new_module,
            "type": AVAILABLE_MODULES[selected_new_module]["type"],
            "config": {} 
        })
        st.rerun()

st.divider()

# Pipeline Config Module
st.subheader("3. Pipeline Sequence")

if not st.session_state.pipeline_modules:
    st.info("Your pipeline is empty. Add modules from the dropdown above to start building.")

for index, mod in enumerate(st.session_state.pipeline_modules):
    with st.expander(f"{index + 1}. {mod['name']}", expanded=True):
        
        if mod["type"] == "llm":
            c1, c2 = st.columns(2)
            with c1:
                mod["config"]["provider_choice"] = st.radio(
                    "Select Deployment Host", 
                    ["Local (Ollama)", "Cloud API"], 
                    horizontal=True,
                    key=f"prov_{mod['id']}"
                )
            with c2:
                mod["config"]["iters"] = st.slider(
                    "Reflection Cycles (Self-Correction)", 0, 3, 0, 
                    key=f"iters_{mod['id']}"
                )

            c3, c4 = st.columns(2)
            with c3:
                if mod["config"]["provider_choice"] == "Local (Ollama)":
                    model_options = get_local_ollama_models()
                else:
                    model_options = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro", "Custom..."]
                
                selected_model = st.selectbox("Model Tier", model_options, key=f"sel_{mod['id']}")
            
            with c4:
                if selected_model == "Custom...":
                    mod["config"]["model_name"] = st.text_input("Enter exact model ID/Name:", key=f"txt_{mod['id']}")
                else:
                    mod["config"]["model_name"] = selected_model

            available_static = [m["name"].split(": ")[1].replace(" ", "") for m in st.session_state.pipeline_modules[:index] if m["type"] == "static"]
            mapped_static = ["RegexSecretScanner" if x == "SecretScanner" else x for x in available_static]

            mod["config"]["depends_static"] = st.multiselect(
                "Context (Static Tool Outputs to feed this Agent)", 
                options=mapped_static,
                default=mapped_static, 
                key=f"dep_{mod['id']}"
            )
                
        else:
            st.write("Standard static tool. No configuration required.")
            
        if st.button("Remove", key=f"del_{mod['id']}"):
            st.session_state.pipeline_modules.pop(index)
            st.rerun()

st.divider()

# Execution module 
start_button = st.button("Execute Custom Pipeline", use_container_width=True, type="primary")

if start_button:
    if not uploaded_file:
        st.error("Please upload a Python file first.")
    elif len(st.session_state.pipeline_modules) == 0:
        st.error("Your pipeline is empty! Add some modules.")
    else:
        has_empty_custom = any(
            m["type"] == "llm" and (not m["config"].get("model_name") or m["config"]["model_name"].strip() == "")
            for m in st.session_state.pipeline_modules
        )
        
        if has_empty_custom:
            st.error("You selected a 'Custom...' model but left the text input blank. Please enter a model name.")
        else:
            st.subheader("Live Execution Logs")
            terminal_container = st.empty()
            logs = ["Assembling dynamic pipeline architecture..."]
            terminal_container.code("\n".join(logs), language="bash")
            
            input_mod = TextInputModule(text=code_content, filename=uploaded_file.name, language="python")
            output_mod = UIOutputModule()
            pipeline = Pipeline(input_module=input_mod, output_module=output_mod)

            for mod in st.session_state.pipeline_modules:
                mod_class = AVAILABLE_MODULES[mod["name"]]["class"]
                
                if mod["type"] == "static":
                    pipeline.add_module(mod_class())
                    logs.append(f"  + Added {mod['name']}")
                elif mod["type"] == "llm":
                    model = mod["config"]["model_name"]
                    is_local = mod["config"]["provider_choice"] == "Local (Ollama)"
                    
                    actual_provider = "ollama" if is_local else "api"
                    actual_host = "http://localhost:11434" if is_local else "https://generativelanguage.googleapis.com"
                    
                    kwargs = {
                        "model_name": model,
                        "provider": actual_provider,
                        "reflection_iterations": mod["config"]["iters"],
                        "depends_on_static": mod["config"]["depends_static"],
                        "host": actual_host,
                        "api_key": None if is_local else GEMINI_KEY
                    }
                    
                    pipeline.add_module(mod_class(**kwargs))
                    logs.append(f"  + Added {mod['name']} ({model} via {actual_provider})")
                    
                terminal_container.code("\n".join(logs[-15:]), language="bash")

            logs.append("\nEXECUTING PIPELINE...")
            terminal_container.code("\n".join(logs[-15:]), language="bash")
            
            start_time = time.time()
            with st.spinner("Pipeline is running... this may take a moment depending on the models selected."):
                final_payload = pipeline.run()
            
            duration = time.time() - start_time
            logs.append(f"PIPELINE COMPLETE in {duration:.2f} seconds.")
            terminal_container.code("\n".join(logs[-15:]), language="bash")
            
            # --- NEW: Save results to session state so they survive button clicks ---
            st.session_state.review_active = True
            st.session_state.suggestions = final_payload.suggested_changes
            st.session_state.static_issues = final_payload.static_issues
            st.session_state.original_code = code_content
            st.session_state.filename = uploaded_file.name
            st.session_state.decisions = {i: "pending" for i in range(len(final_payload.suggested_changes))}


# Interactive Result Display
if st.session_state.review_active:
    st.divider()
    st.header("Interactive Review Results")
    
    static_count = len(st.session_state.static_issues)
    llm_count = len(st.session_state.suggestions)
    st.write(f"**Static Issues:** {static_count} | **Agent Suggestions:** {llm_count}")
    
    # Display Static Issues
    if static_count > 0:
        with st.expander("Static Tool Findings", expanded=False):
            static_data = [{"Tool": i.tool_name, "Severity": i.severity, "Line": i.line_number, "Message": i.message} for i in st.session_state.static_issues]
            st.dataframe(pd.DataFrame(static_data), use_container_width=True)
            
    # Display LLM Issues
    if llm_count > 0:
        st.subheader("LLM Agent Suggestions")
        resolved_count = 0
        
        for index, sug in enumerate(st.session_state.suggestions):
            status = st.session_state.decisions[index]
            
            if status == "accepted":
                resolved_count += 1
            elif status == "declined":
                resolved_count += 1
                
            with st.container(border=True):
                st.markdown(f"**{sug.reviewer}** recommends a change on **Lines {sug.line_start}-{sug.line_end}**")
                st.write(f"*{sug.explanation}*")
                
                # Show side-by-side code diff
                code_col1, code_col2 = st.columns(2)
                with code_col1:
                    st.write("**Original**")
                    st.code(sug.original_code, language="python")
                with code_col2:
                    st.write("**Suggested**")
                    st.code(sug.suggested_code, language="python")
                
                # Accept/Decline Buttons
                if status == "pending":
                    btn_col1, btn_col2, _ = st.columns([1, 1, 4])
                    with btn_col1:
                        if st.button("Accept", key=f"acc_{index}", type="primary"):
                            st.session_state.decisions[index] = "accepted"
                            st.rerun()
                    with btn_col2:
                        if st.button("Decline", key=f"dec_{index}"):
                            st.session_state.decisions[index] = "declined"
                            st.rerun()
                else:
                    if status == "accepted":
                        st.success("You accepted this change.")
                    else:
                        st.error("You declined this change.")

        # Download Logic
        if resolved_count == llm_count:
            st.divider()
            st.success("All suggestions reviewed! You can now download the patched file.")
            
            # String Replacement Patching Logic
            patched_code = st.session_state.original_code
            
            # Get all accepted suggestions
            accepted_sugs = [sug for i, sug in enumerate(st.session_state.suggestions) if st.session_state.decisions[i] == "accepted"]
            
            # Apply patches by exact string replacement
            for sug in accepted_sugs:
                # Check if the exact block exists in the current code
                if sug.original_code in patched_code:
                    # Replace only the first occurrence to be safe
                    patched_code = patched_code.replace(sug.original_code, sug.suggested_code, 1)
                else:
                    # Warn the user if a patch failed to apply (usually due to overlapping agent changes)
                    st.warning(f"**Patch Warning:** Could not find the exact code block to replace for the suggestion by {sug.reviewer}. Another agent's accepted patch may have already altered this section.")
            
            st.download_button(
                label=f"Download Patched {st.session_state.filename}",
                data=patched_code,
                file_name=f"reviewed_{st.session_state.filename}",
                mime="text/x-python",
                type="primary",
                use_container_width=True
            )