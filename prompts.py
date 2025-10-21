from langchain_core.prompts import PromptTemplate

# Basit bir LangChain Zinciri için prompt şablonu
readme_template = """
You are an expert software developer and technical writer.
Based on the following code content from a file, generate a professional README.md.

The README should include the following sections:
- **## Overview**: A brief, one-paragraph summary of what the code does.
- **## Usage**: A simple explanation of how to run or use the code.
- **## Code Details**: A more detailed explanation of the main functions or classes.

Here is the code content from the file:
---
{code_content}
---

Generate the complete README.md file now, using proper Markdown formatting:
"""

# Burada README_PROMPT oluşturuluyor ve kod içeriğini alacak şekilde yapılandırılıyor.
README_PROMPT = PromptTemplate(
    input_variables=["code_content"],
    template=readme_template
)
