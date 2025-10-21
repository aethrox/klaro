from langchain_core.prompts import PromptTemplate

# A more aggressive prompt template to ensure model compliance
readme_template = """
**YOU MUST FOLLOW ALL FORMATTING RULES. THIS IS YOUR PRIMARY OBJECTIVE.**

Your main task is to generate a professional README.md file.
Your secondary task is to ensure all formatting is perfect.

<formatting_rules>
1.  Use proper Markdown for all sections, headers, and lists.
2.  **CRITICAL RULE:** Enclose all file names, variable names, function names, and library names within single backticks (`).
    -   **EXAMPLE:** Instead of writing "dotenv", you MUST write `dotenv`.
    -   **EXAMPLE:** Instead of writing "generate_readme_for_file", you MUST write `generate_readme_for_file`.
    -   **EXAMPLE:** Instead of writing "ChatOpenAI", you MUST write `ChatOpenAI`.
3.  For multi-line code blocks, use triple backticks with the language identifier (e.g., ```bash or ```python).
</formatting_rules>

Now, execute your main task.
Generate a professional README.md based on the following file content.

The README must include these sections:
- **## Overview**: A brief summary of what the code does.
- **## Usage**: An explanation of how to run or use the code.
- **## Code Details**: A detailed description of the main functions or classes.

Here is the code content from the file:
---
{code_content}
---

Generate the complete README.md file, strictly adhering to all rules specified within the <formatting_rules> tags.
"""

README_PROMPT = PromptTemplate(
    input_variables=["code_content"],
    template=readme_template
)