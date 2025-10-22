from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os

class ReadFileToolInput(BaseModel):
    # Input for the file reading tool.
    file_path: str = Field(description="The relative or absolute path to the file that needs to be read.")

class CodeReaderTool(BaseTool):
    # A tool for reading the content of a specific code file.
    name: str = "code_reader"
    description: str = "Useful for reading the content of a specific code file. Provide the file path."
    args_schema: Type[BaseModel] = ReadFileToolInput

    def _run(self, file_path: str) -> str:
        # Reads the content of a file and returns it as a string.
        if not os.path.exists(file_path):
            return f"Error: File not found at path '{file_path}'"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"An error occurred while reading the file: {e}"
