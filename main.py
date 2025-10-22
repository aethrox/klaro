# main.py - Final English Version (Saf Python ReAct)

import os
from dotenv import load_dotenv 
load_dotenv() 

import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document # For RAG

from prompts import SYSTEM_PROMPT 
from tools import list_files, read_file, analyze_code, web_search, init_knowledge_base, retrieve_knowledge 

# --- 1. Configuration and Model Selection ---
LLM_MODEL = "gpt-4o-mini" 
llm = ChatOpenAI(model=LLM_MODEL, temperature=0.2) 

# Collect all tools into a dictionary
TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "analyze_code": analyze_code,
    "web_search": web_search,
    "retrieve_knowledge": retrieve_knowledge, # RAG tool
}

# Create a clean list of tool descriptions for the LLM prompt
TOOL_DESCRIPTIONS = "\n".join([f"- {name}: {tool.__doc__.strip()}" for name, tool in TOOLS.items()])

# --- 2. Prompt Template (Pure ReAct Format) ---
REACT_PROMPT_TEMPLATE = """
{system_prompt}

Available Tools (Tools) and Descriptions:
-------------------------
{tool_descriptions}
-------------------------

Current Conversation History and Scratchpad (Thought, Action, Observation):
{scratchpad}

User's Task: {input}

Please use the tools above, following the Thought and Action steps to complete the task.
You MUST strictly adhere to the Action format: `Action: tool_name[parameter]` (Example: Action: list_files[.])
To end the loop, provide your final answer in the format: **'Final Answer: [MARKDOWN_CONTENT]'**
"""

def parse_action(text: str) -> tuple[str, str] | None:
    """Parses Action and parameter from the LLM's output."""
    
    # 1. Look for the standard Action pattern: Action: tool_name[param]
    match = re.search(r"Action:\s*(\w+)\s*\[(.*?)\]", text, re.DOTALL)
    
    if match:
        action = match.group(1).strip()
        param = match.group(2).strip().strip("'\"") 
        return action, param
    
    # 2. Look for the function call pattern: Action: tool_name(param)
    match_func = re.search(r"Action:\s*(\w+)\s*\((.*?)\)", text, re.DOTALL)
    if match_func:
        action = match_func.group(1).strip()
        param = match_func.group(2).strip().strip("'\"")
        return action, param
        
    return None

# RAG Style Guide Content
DEFAULT_GUIDE_CONTENT = """
# Klaro Project Documentation Style Guide: 

All README.md documents produced using this guide must adhere to the following standards:

1.  **Heading Structure:** Headings must start with # and ##.
2.  **Sections:** Every README must include the following sections: `# Project Name`, `## Setup`, `## Usage`, `## Components`.
3.  **Tone and Language:** The tone must be technical, professional, and clear. Code examples must always be formatted with triple backticks (```python).
"""

def run_klaro_agent(project_path: str = "."):
    """
    Runs the Klaro Pure Python ReAct Agent.
    """
    print(f"--- Launching Klaro Autonomous Documentation Agent (Pure Python ReAct - {LLM_MODEL}) ---")
    
    # 🌟 STAGE 3 INTEGRATION: Knowledge Base Setup (RAG)
    print("📢 Initializing RAG Knowledge Base...")
    
    documents_to_index = [
        Document(page_content=DEFAULT_GUIDE_CONTENT, metadata={"source": "Klaro_Style_Guide"}),
    ]
    
    setup_result = init_knowledge_base(documents_to_index)
    print(f"   -> Setup Result: {setup_result}")

    max_steps = 15 
    scratchpad = "" 
    
    task_input = (
        f"Please analyze the codebase in '{project_path}' and create a README.md document. "
        "Steps: 1. Explore with 'list_files'. 2. Read critical files with 'read_file' and analyze code with 'analyze_code'. "
        "3. Gather external info with 'web_search'. 4. Use the 'retrieve_knowledge' tool to fetch the 'README style guidelines' before writing the final answer."
    )
    
    current_prompt = ChatPromptTemplate.from_template(REACT_PROMPT_TEMPLATE)
    
    for step in range(max_steps):
        print(f"\n--- STEP {step + 1} / {max_steps} ---")
        
        # 1. Prepare Prompt
        formatted_prompt = current_prompt.format(
            system_prompt=SYSTEM_PROMPT,
            tool_descriptions=TOOL_DESCRIPTIONS,
            scratchpad=scratchpad,
            input=task_input
        )
        
        # 2. Run LLM (Thought -> Action)
        messages = [
            HumanMessage(content=formatted_prompt)
        ]
        
        try:
            llm_output = llm.invoke(messages).content
        except Exception as e:
            print(f"LLM Call Failed: {e}")
            break

        print(f"LLM Output:\n{llm_output}")
        scratchpad += f"\n{llm_output}" 
        
        # 3. Final Answer Check
        if "Final Answer:" in llm_output:
            print("====================================")
            print("✅ TASK SUCCESS: Final Answer received.")
            final_answer = llm_output.split("Final Answer:")[1].strip()
            return final_answer
        
        # 4. Parse Action (Action -> Observation)
        action_pair = parse_action(llm_output)
        
        if not action_pair:
            observation = "Observation: Error: No valid 'Action: tool_name[param]' format found. Please strictly adhere to the ReAct format."
        else:
            action, param = action_pair
            
            print(f"-> Executing: {action}['{param}']")
            
            # 5. Execute Tool and Observe
            if action in TOOLS:
                try:
                    tool_func = TOOLS[action]
                    observation_result = tool_func(param)
                    observation = f"Observation: {observation_result}"
                except Exception as e:
                    observation = f"Observation: Tool Execution Error: {e}"
            else:
                observation = f"Observation: Error: Unknown tool name '{action}'. Please use one from the TOOLS list."

        print(f"Observation Added:\n{observation}")
        scratchpad += f"\n{observation}"

    # Reached maximum steps
    print("\n====================================")
    return "Error: Maximum steps reached (15 steps). Agent failed to complete the task."


if __name__ == "__main__":
    final_result = run_klaro_agent(project_path=".")
    print("\n" + "="*50)
    print("KLARO RESULT:")
    print("="*50)
    print(final_result)