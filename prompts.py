from langchain_core.prompts import PromptTemplate

# Basit bir LangChain Zinciri için prompt şablonu
readme_template = """
You are an expert software developer and technical writer with a keen eye for detail in Markdown formatting.
Based on the following code content from a file, generate a professional README.md.

The README must include the following sections:
- **## Overview**: A brief, one-paragraph summary of what the code does.
- **## Usage**: A simple explanation of how to run or use the code.
- **## Code Details**: A more detailed explanation of the main functions or classes.

**Formatting Rules (Very Important):**
1. Use proper Markdown for all sections, headers, and lists.
2. **Crucially, enclose all file names, variable names, function names, and library names within single backticks (`). For example, instead of writing "dotenv", you must write `dotenv`. Instead of "generate_readme_for_file", you must write `generate_readme_for_file`.**
3. For multi-line code blocks, use triple backticks with the language identifier (e.g., ```bash or ```python).

Here is the code content from the file:
---
{code_content}
---

Generate the complete README.md file now, strictly following all formatting rules.
"""

README_PROMPT = PromptTemplate(
    input_variables=["code_content"],
    template=readme_template
)
