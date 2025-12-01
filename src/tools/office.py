import os
import re
import io
import base64
import pandas as pd
from langchain_core.tools import tool

def _allowed(filename: str) -> bool:
    allowed = os.environ.get("CURRENT_SESSION_UPLOADS", "")
    names = [x.strip() for x in re.split(r"[;,]", allowed) if x.strip()]
    return filename in names

@tool
def excel_to_csv_from_upload(filename: str, return_base64: bool = False) -> str:
    """Convert an uploaded Excel file to CSV and return content or Base64.
    The file must exist in 'uploads/' directory.
    """
    if not _allowed(filename):
        return "Error: File not allowed (not in current session uploads)"
    path = os.path.join("uploads", filename)
    if not os.path.exists(path):
        return "Error: File not found in uploads/"
    try:
        df = pd.read_excel(path)
        csv_str = df.to_csv(index=False)
        if return_base64:
            b64 = base64.b64encode(csv_str.encode('utf-8')).decode('utf-8')
            return f"Converted successfully. [FILE:csv:{b64}:{os.path.splitext(filename)[0]}.csv]"
        return csv_str
    except Exception as e:
        return f"Error converting Excel to CSV: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def csv_to_excel_from_upload(filename: str) -> str:
    """Convert an uploaded CSV file to Excel and return Base64 for download."""
    if not _allowed(filename):
        return "Error: File not allowed (not in current session uploads)"
    path = os.path.join("uploads", filename)
    if not os.path.exists(path):
        return "Error: File not found in uploads/"
    try:
        df = pd.read_csv(path)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"Converted successfully. [FILE:xlsx:{b64}:{os.path.splitext(filename)[0]}.xlsx]"
    except Exception as e:
        return f"Error converting CSV to Excel: {str(e)}"
    finally:
        try:
            os.remove(path)
        except Exception:
            pass

@tool
def markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    try:
        import markdown as md
        html = md.markdown(md_text)
        return html
    except Exception as e:
        return f"Error converting markdown: {str(e)}"
