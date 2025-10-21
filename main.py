import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from prompts import README_PROMPT
from tools import CodeReaderTool

def get_code_content(file_path: str) -> dict:
    """
    An intermediate function: It only reads the file content and returns it as a dictionary.
    This works more seamlessly with the LangChain Expression Language (LCEL).
    """
    code_reader = CodeReaderTool()
    content = code_reader.run(file_path)
    return {"code_content": content}

def generate_readme_for_file(file_path: str):
    """
    README oluşturma sürecini yönetir.
    """
    # 1. Load API keys and settings
    load_dotenv()
    
    print("--- Klaro MVP ---")
    
    # 2. Prepare necessary components
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    output_parser = StrOutputParser()

    # 3. Create the LangChain chain
    project_name = os.path.basename(file_path).split('.')[0].replace('_', ' ').title() # We use the file path as the default project name.
    
    project_info = RunnablePassthrough.assign(
        project_name=lambda x: project_name # Dynamically assign a name such as 'main' or 'prompts'
    )

    chain = (
        {"file_path": RunnablePassthrough()}
        # 1. Read the code content
        | RunnablePassthrough.assign(code_info=lambda x: get_code_content(x["file_path"]))
        # 2. Create the 'project_name' and 'code_content' variables and prepare them for the PromptTemplate.
        | {
            "project_name": lambda x: project_name, # Yeni eklenen kısım
            "code_content": lambda x: x["code_info"]["code_content"],
        }
        | README_PROMPT
        | llm
        | output_parser
    )

    print(f"1. Reading and processing '{file_path}'...")
    
    # 4. Run the chain to generate the README
    try:
        print("2. Generating README.md via LLM (using gpt-4o-mini)...") # I added a logo with the model name specified.
        readme_content = chain.invoke(file_path)

        # 5. Save the result to a file
        generated_filename = "README_generated.md"
        print(f"3. Saving output to '{generated_filename}'...")
        with open(generated_filename, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print("\n--- Process Complete ---")
        print(f"Generated README content saved to {generated_filename}")

    except Exception as e:
        print("\n--- AN ERROR OCCURRED ---")
        print(f"An error occurred during the generation process: {e}")
        print("Please check your API keys, network connection, and file paths.")


if __name__ == "__main__":
    # Get the file path from the user
    target_file = input("Enter the path of the Python file to document: ")
    
    # If the file does not exist, print an error message
    if not os.path.exists(target_file):
        print(f"Error: File not found: {target_file}")
    else:
        generate_readme_for_file(target_file)

