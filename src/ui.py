import streamlit as st
import os
import re
import base64
from datetime import datetime

try:
    from src.tools.image import get_artifact as get_image_artifact
except Exception:
    def get_image_artifact(_):
        return ""
try:
    from src.tools.office import get_artifact as get_file_artifact
except Exception:
    def get_file_artifact(_):
        return ""

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.agent.react_agent import get_graph

# Import tab components
from src.ui_tabs.jsonsql import render_jsonsql_tab
from src.ui_tabs.codec import render_codec_tab
from src.ui_tabs.diff import render_diff_tab
from src.ui_tabs.jsonpath import render_jsonpath_tab
from src.ui_tabs.markdown_editor import render_markdown_tab
from src.ui_tabs.request import render_request_tab

def extract_image_base64(text):
    """Extract base64 image data from tool output."""
    match1 = re.search(r"\[IMAGE_DATA: (.+?)\]", text)
    if match1:
        return ("png", match1.group(1).strip())
    match2 = re.search(r"\[IMAGE:([a-zA-Z0-9]+):(.+?)\]", text)
    if match2:
        return (match2.group(1).lower(), match2.group(2).strip())
    match3 = re.search(r"\[IMAGE_ID:([a-f0-9]+):([a-zA-Z0-9]+)\]", text)
    if match3:
        aid = match3.group(1)
        mime = match3.group(2).lower()
        b64 = get_image_artifact(aid)
        if b64:
            return (mime, b64)
        # Fallback: check office tools artifact cache
        b64 = get_file_artifact(aid)
        if b64:
            return (mime, b64)
    
    return None

def extract_file_artifact(text):
    """Extract downloadable file artifact from tool output."""
    match = re.search(r"\[FILE:([a-zA-Z0-9]+):(.+?):([^\]]+)\]", text)
    if match:
        ext = match.group(1).lower()
        b64 = match.group(2)
        fname = match.group(3)
        return (ext, b64, fname)
    match2 = re.search(r"\[FILE_ID:([a-f0-9]+):([a-zA-Z0-9]+):([^\]]+)\]", text)
    if match2:
        aid = match2.group(1)
        ext = match2.group(2).lower()
        fname = match2.group(3)
        b64 = get_file_artifact(aid)
        if b64:
            return (ext, b64, fname)
    return None


def render_ui():
    st.set_page_config(page_title="AI 智能助手", page_icon="🛠️")

    st.title("🛠️BunnyTools")

    st.divider()

    tabs = st.tabs(["JSON/SQL 工具", "编解码工具", "文本比对", "JSONPath 查询", "Markdown 编辑", "模拟请求"])

    with tabs[0]:
        render_jsonsql_tab()

    with tabs[1]:
        render_codec_tab()

    with tabs[2]:
        render_diff_tab()

    with tabs[3]:
        render_jsonpath_tab()

    with tabs[4]:
        render_markdown_tab()

    with tabs[5]:
        render_request_tab()

    # Sidebar for API Key configuration
    with st.sidebar:
        st.header("配置")
        ds_key = st.text_input("DeepSeek API Key", type="password")
        if ds_key:
            os.environ["DEEPSEEK_API_KEY"] = ds_key
        zhipu_key = st.text_input("Zhipu API Key", type="password")
        if zhipu_key:
            os.environ["ZHIPU_API_KEY"] = zhipu_key
        
        st.info("可使用 DeepSeek / Zhipu；至少配置一个 API Key。")
        
        st.divider()
        st.header("文件上传")
        uploaded_files = st.file_uploader(
            "上传文件 (CSV/Excel/文本/图片/Word/PDF)",
            accept_multiple_files=True,
            type=["csv", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "webp", "bmp", "gif", "docx", "doc", "pdf"]
        )
        
        if uploaded_files:
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            current_names = []
            for uploaded_file in uploaded_files:
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                current_names.append(uploaded_file.name)
            st.session_state["uploaded_current"] = current_names
            os.environ["CURRENT_SESSION_UPLOADS"] = ";".join(current_names)
            st.success(f"已上传 {len(uploaded_files)} 个文件到 {upload_dir}/：{', '.join(current_names)}")

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            st.markdown(content)
            # Display tool outputs if any
            if "steps" in message:
                with st.expander("查看思考与工具调用过程"):
                    for step in message["steps"]:
                        st.caption(f"**Step**: {step['type']}")
                        st.code(step['content'])
                        
                        # Try to display base64 image if present in tool output
                        if step['type'] == 'tool_output':
                            img_info = extract_image_base64(step['content'])
                            if img_info:
                                mime, img_b64 = img_info
                                st.image(f"data:image/{mime};base64,{img_b64}", caption="生成的图片")
                            file_info = extract_file_artifact(step['content'])
                            if file_info:
                                ext, b64, fname = file_info
                                data = base64.b64decode(b64)
                                st.download_button("下载文件: " + fname, data=data, file_name=fname)

    # User input
    user_input = st.chat_input("请输入您的任务 (例如: 生成一个内容为 'HelloWorld' 的二维码)")

    if user_input:
        if not os.environ.get("DEEPSEEK_API_KEY") and not os.environ.get("ZHIPU_API_KEY"):
            st.error("请先配置 API Key！")
            st.stop()

        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Run the graph
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            # Create a container for steps/thinking that appears before the final answer
            # We use an expander-like structure or just a container.
            steps_container = st.container()
            
            full_response = ""
            steps_log = []
            
            # To handle non-streaming updates with waiting effect
            try:
                # Check for uploaded files to provide context
                uploaded_context = ""
                files = st.session_state.get("uploaded_current", [])
                if files:
                    uploaded_context = f"\n\n[System Hint] Current uploaded files for this session: {', '.join(files)}. Only operate on these; do not read historical files."
                
                max_len = 50000
                u = user_input or ""
                if len(u) > max_len:
                    u = u[:max_len] + "\n\n[部分输入已截断以避免超出上下文限制]"
                inputs = {"messages": [HumanMessage(content=u + uploaded_context)]}
                
                # Use stream_mode="updates" to get node-level updates (waiting effect between nodes)
                # This avoids token-by-token streaming but allows showing progress
                with st.spinner("正在思考中..."):
                    graph = get_graph()
                    for event in graph.stream(inputs, stream_mode="updates"):
                        for node_name, node_data in event.items():
                            # Log node transition
                            steps_log.append({"type": "node", "content": node_name})
                            
                            new_messages = node_data.get("messages", [])
                            if not isinstance(new_messages, list):
                                new_messages = [new_messages]
                                
                            for msg in new_messages:
                                if isinstance(msg, AIMessage):
                                    # Handle tool calls
                                    if msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            step_info = f"🛠️ **调用工具**: `{tool_call['name']}`\n参数: `{tool_call['args']}`"
                                            steps_container.markdown(step_info)
                                            steps_log.append({"type": "tool_call", "content": f"Tool: {tool_call['name']}, Args: {tool_call['args']}"})
                                    
                                    # Handle content (thought process or final answer)
                                    if msg.content:
                                        # Display as thought/reasoning block
                                        thought_preview = msg.content if len(msg.content) <= 600 else (msg.content[:600] + "...")
                                        steps_container.markdown(f"🧠 **思考**:\n```\n{thought_preview}\n```")
                                        steps_log.append({"type": "thought", "content": msg.content})
                                        
                                        # Accumulate full response
                                        full_response += msg.content
                                        # Update main message placeholder
                                        message_placeholder.markdown(full_response)
                                
                                elif isinstance(msg, ToolMessage):
                                    # Display tool output
                                    content_display = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                                    step_info = f"✅ **工具返回**: `{msg.name}`\n```\n{content_display}\n```"
                                    steps_container.markdown(step_info)
                                    
                                    img_info = extract_image_base64(msg.content)
                                    if img_info:
                                        mime, img_b64 = img_info
                                        steps_container.image(f"data:image/{mime};base64,{img_b64}", caption="生成的图片")
                                    file_info = extract_file_artifact(msg.content)
                                    if file_info:
                                        ext, b64, fname = file_info
                                        data = base64.b64decode(b64)
                                        steps_container.download_button("下载文件: " + fname, data=data, file_name=fname)
                                    
                                    steps_log.append({"type": "tool_output", "content": msg.content})

                # Final update to session state
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "steps": steps_log
                })

            except Exception as e:
                st.error(f"运行出错: {str(e)}")
