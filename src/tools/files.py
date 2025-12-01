import os
import re
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# 4. Python REPL Tool
python_repl = PythonREPL()

@tool
def python_interpreter(code: str) -> str:
    """Executes Python code and returns the output. 
    Use this for complex calculations, data processing, or generating code snippets.
    
    Note on file access:
    - Uploaded files are located in the 'uploads/' directory.
    - To read a CSV file: pd.read_csv('uploads/filename.csv')
    - To read an Excel file: pd.read_excel('uploads/filename.xlsx')
    """
    try:
        # Ensure imports are available in the REPL context if needed, 
        # though typically users need to import them in the code string.
        # But for convenience we can preload some.
        result = python_repl.run(code)
        return f"Output:\n{result}"
    except Exception as e:
        return f"Error executing code: {str(e)}"

@tool
def list_uploaded_files() -> str:
    """Lists files uploaded in the current session only."""
    allowed = os.environ.get("CURRENT_SESSION_UPLOADS", "")
    names = [x.strip() for x in re.split(r"[;,]", allowed) if x.strip()]
    if not names:
        return "No files uploaded yet."
    return "Uploaded files (current session):\n" + "\n".join(names)
