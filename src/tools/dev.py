import time
import json
import hashlib
import base64
import qrcode
import io
import urllib.parse
from typing import Literal
from langchain_core.tools import tool
import sqlparse

@tool
def json_formatter(data: str, action: Literal["format", "compress", "escape", "unescape"] = "format") -> str:
    """Handles JSON data: format (pretty print), compress (minify), escape, or unescape."""
    try:
        if action == "format":
            parsed = json.loads(data)
            return json.dumps(parsed, indent=4, ensure_ascii=False)
        elif action == "compress":
            parsed = json.loads(data)
            return json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        elif action == "escape":
            return json.dumps(data).strip('"')
        elif action == "unescape":
            return json.loads(f'"{data}"')
        return "Invalid action."
    except json.JSONDecodeError:
        return "Error: Invalid JSON string."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def hash_generator(text: str, algorithm: Literal["md5", "sha1", "sha256"] = "md5") -> str:
    """Generates a hash (MD5, SHA1, SHA256) for the given text."""
    text_bytes = text.encode('utf-8')
    if algorithm == "md5":
        return hashlib.md5(text_bytes).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text_bytes).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text_bytes).hexdigest()
    return "Invalid algorithm."

@tool
def encoding_tool(text: str, mode: Literal["base64_encode", "base64_decode", "url_encode", "url_decode"]) -> str:
    """Handles text encoding and decoding: Base64 or URL."""
    try:
        if mode == "base64_encode":
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        elif mode == "base64_decode":
            return base64.b64decode(text).decode('utf-8')
        elif mode == "url_encode":
            return urllib.parse.quote(text)
        elif mode == "url_decode":
            return urllib.parse.unquote(text)
        return "Invalid mode."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def timestamp_converter(value: str, action: Literal["to_date", "to_timestamp"]) -> str:
    """Converts between Unix timestamp and date string."""
    try:
        if action == "to_date":
            # value is timestamp (seconds)
            ts = float(value)
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        elif action == "to_timestamp":
            # value is date string "YYYY-MM-DD HH:MM:SS"
            # Try to guess format or assume standard
            return str(int(time.mktime(time.strptime(value, "%Y-%m-%d %H:%M:%S"))))
    except Exception as e:
        return f"Error: {str(e)}. For to_timestamp, ensure format is YYYY-MM-DD HH:MM:SS."

@tool
def qrcode_generator(text: str) -> str:
    """Generates a QR code for the given text and returns it as a Base64 string to be displayed directly."""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO instead of file
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Return special markers the UI can parse
        return f"QR Code generated successfully. [IMAGE:png:{img_str}]"
    except Exception as e:
        return f"Error generating QR code: {str(e)}"

@tool
def sql_formatter(sql: str) -> str:
    """Format SQL string using sqlparse."""
    try:
        return sqlparse.format(sql, reindent=True, keyword_case='upper')
    except Exception as e:
        return f"Error formatting SQL: {str(e)}"
