import os
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import tools and config
from src.tools import get_tools
from src.core.config import get_llm

# 1. 初始化 LLM (moved to get_graph)
# llm = get_llm()

# 2. 获取工具集 (moved to get_graph)
# tools = get_tools()

# 3. 创建 ReAct Agent
system_prompt = """You are a helpful AI assistant capable of using various tools to solve problems.
You have access to the following tools:
- web_search: Robust web search (Tavily/SerpAPI/DDG fallback).
- calculator: Calculate mathematical expressions.
- current_time: Get the current local time.
- python_interpreter: Execute Python code for complex tasks. You can use pandas, matplotlib, etc.
- list_uploaded_files: Check which files the user has uploaded.
- json_formatter: Handle JSON data (format/pretty-print, compress/minify, escape, unescape).
- hash_generator: Generate hash (MD5, SHA1, SHA256) for text.
- encoding_tool: Handle text encoding/decoding (Base64, URL).
- timestamp_converter: Convert between Unix timestamp and date string.
- qrcode_generator: Generate QR code images from text (UI displays directly via Base64).
- sql_formatter: Format SQL queries.
- excel_to_csv_from_upload: Convert uploaded Excel to CSV (returns CSV or Base64).
- csv_to_excel_from_upload: Convert uploaded CSV to Excel (returns Base64 + filename).
- markdown_to_html: Convert Markdown to HTML.
- image_resize_base64: Resize base64-encoded image and return base64.
- image_convert_base64: Convert base64-encoded image format.
 - image_crop_base64: Crop to rectangle by x,y,width,height.
 - image_compress_base64: Compress with quality to JPEG/WEBP.
 - image_rotate_base64: Rotate by degrees.
 - image_add_text_watermark_base64: Add semi-transparent text watermark.
 - image_add_image_watermark_base64: Overlay image watermark with opacity and scale.
 - image_remove_watermark_base64: Blur or pixelate a selected rectangle.
- image_upload_to_base64: Load an uploaded image from 'uploads/' into base64.
 - image_upload_to_base64: Load an uploaded image from 'uploads/' into base64.
 - image_*_upload: Operate directly on files in 'uploads/' and return base64 for UI.

Process:
1. Analyze the user's request and break it into sub-tasks when needed.
2. For multi-step tasks, call multiple tools in sequence until all subtasks are done.
3. First call 'list_uploaded_files' to discover available files. For image operations, ALWAYS prefer the '*_upload' tools to operate directly on files in 'uploads/'.
   - If the user does NOT specify a filename, choose the MOST RECENT uploaded image (extensions: png, jpg, jpeg, webp, bmp, gif).
   - DO NOT use base64 image tools unless the user provides base64 explicitly.
4. For file processing (CSV/Excel), prefer 'excel_to_csv_from_upload' and 'csv_to_excel_from_upload' over Python unless custom logic is needed.
5. For images, produce and consume Base64 (prefer WEBP to keep outputs compact), never write to disk; the UI will render markers [IMAGE:mime:base64].
6. Execute tools, observe outputs, and continue the loop until the full solution is ready.
7. Finally summarize results clearly.

Always answer in the same language as the user's request (mostly Chinese).
"""

graph = None

def get_graph():
    """Create and return the ReAct agent graph with fresh configuration."""
    # 1. 初始化 LLM (uses current env vars)
    llm = get_llm()
    
    # 2. 获取工具集
    tools = get_tools()
    
    return create_react_agent(llm, tools, prompt=system_prompt)

if __name__ == "__main__":
    # 简单测试
    print("Start testing ReAct Agent...")
    # Set a dummy key for testing if not set
    if not os.environ.get("DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = "sk-test-key"
        
    graph = get_graph()
    inputs = {"messages": [HumanMessage(content="现在几点了？")]}
    for s in graph.stream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        if hasattr(message, "content"):
             print(message.content)
