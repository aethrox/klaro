from langchain_core.prompts import PromptTemplate

# The final, most strict prompt to enforce all formatting rules.
readme_template = """
**CRITICAL INSTRUCTIONS: YOU MUST FOLLOW THESE RULES EXACTLY. FAILURE TO COMPLY WILL RESULT IN AN INVALID OUTPUT.**

1.  **Primary Goal:** Generate the content for a professional README.md file based on the code provided.
2.  **Formatting is MANDATORY and NON-NEGOTIABLE.**

<output_format_rules>
    <rule_1_no_wrapper>
        **NO WRAPPER BLOCKS:** Your response MUST NOT be enclosed in a markdown code block (like ```markdown ... ```).
        Your response must start DIRECTLY with the first line of the README file's content (e.g., `# Project Title`). Do not add any preamble or explanation.
    </rule_1_no_wrapper>
    
    <rule_2_use_single_backticks>
        **USE SINGLE BACKTICKS:** You MUST enclose every single file name, variable name, function name, class name, and library name in single backticks (`). This is a critical requirement for correctness.
        -   **CORRECT EXAMPLE:** `gpt-4o`
        -   **CORRECT EXAMPLE:** `CodeReaderTool`
        -   **CORRECT EXAMPLE:** `main.py`
        -   **CORRECT EXAMPLE:** `langchain`
        -   **INCORRECT EXAMPLE:** gpt-4o, CodeReaderTool, main.py, langchain
    </rule_2_use_single_backticks>
    
    <rule_3_use_code_fences>
        **USE CODE FENCES FOR CODE:** Use triple backticks with a language identifier (e.g., ```python) for multi-line code snippets.
    </rule_3_use_code_fences>
</output_format_rules>

Now, based on the following code, generate the complete and perfectly formatted README.md file content.

**Code Content to Analyze:**
---
{code_content}
---

**Final Instruction:** Your generated output will be saved directly to a file. Ensure it starts with a `#` heading and adheres to every rule listed above without exception.
"""

README_PROMPT = PromptTemplate(
    input_variables=["code_content"],
    template=readme_template
)