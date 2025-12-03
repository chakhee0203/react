import os
import re
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
    
    If you generate plots using matplotlib, they will be returned as images.
    """
    try:
        # Clear any previous plots
        plt.clf()
        plt.close('all')
        
        # Run the code
        result = python_repl.run(code)
        
        # Check for plots
        plot_data = ""
        if plt.get_fignums():
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            plot_data = f"\n[IMAGE:png:{b64}]"
            plt.close('all')
            
        return f"Output:\n{result}{plot_data}"
    except Exception as e:
        return f"Error executing code: {str(e)}"

@tool
def read_file_from_upload(filename: str, head: int = None) -> str:
    """Read the content of an uploaded text-based file (txt, csv, md, py, json, etc.).
    
    Args:
        filename: The name of the file in uploads/.
        head: (Optional) Number of characters to read from the beginning. Default reads full file (up to limit).
    """
    allowed = os.environ.get("CURRENT_SESSION_UPLOADS", "")
    names = [x.strip() for x in re.split(r"[;,]", allowed) if x.strip()]
    
    if filename not in names:
         # Try fuzzy match or check if it's just not in the list but exists (security risk? No, rely on list)
         return "Error: File not allowed (not in current session uploads)"
         
    path = os.path.join("uploads", filename)
    if not os.path.exists(path):
        return "Error: File not found in uploads/"
        
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if head:
                content = f.read(head)
                return f"Content of {filename} (first {head} chars):\n{content}..."
            else:
                content = f.read()
                # Truncate if too long to avoid context overflow
                if len(content) > 20000:
                    return f"Content of {filename} (truncated to first 20000 chars):\n{content[:20000]}..."
                return f"Content of {filename}:\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def list_uploaded_files() -> str:
    """Lists files uploaded in the current session only."""
    allowed = os.environ.get("CURRENT_SESSION_UPLOADS", "")
    names = [x.strip() for x in re.split(r"[;,]", allowed) if x.strip()]
    if not names:
        return "No files uploaded yet."
    return "Uploaded files (current session):\n" + "\n".join(names)
