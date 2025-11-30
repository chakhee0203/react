import streamlit as st
import os
import re
import json
import base64
import urllib.parse
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from src.agent.react_agent import get_graph

def extract_image_base64(text):
    """Extract base64 image data from tool output."""
    # Support both legacy [IMAGE_DATA: ...] and new [IMAGE:mime:...]
    match1 = re.search(r"\[IMAGE_DATA: (.+?)\]", text)
    if match1:
        return ("png", match1.group(1).strip())
    match2 = re.search(r"\[IMAGE:([a-zA-Z0-9]+):(.+?)\]", text)
    if match2:
        return (match2.group(1).lower(), match2.group(2).strip())
    return None

def extract_file_artifact(text):
    """Extract downloadable file artifact from tool output: [FILE:ext:base64:filename]"""
    match = re.search(r"\[FILE:([a-zA-Z0-9]+):(.+?):([^\]]+)\]", text)
    if match:
        ext = match.group(1).lower()
        b64 = match.group(2)
        fname = match.group(3)
        return (ext, b64, fname)
    return None

def render_ui():
    st.set_page_config(page_title="AI 智能助手", page_icon="🛠️")

    st.title("🛠️BunnyTools")

    st.divider()

    tabs = st.tabs(["JSON/SQL 工具", "Base64", "URL 编解码", "正则提取", "文本处理", "日期格式转换"])

    with tabs[0]:
        if "jsonsql_output" not in st.session_state:
            st.session_state.jsonsql_output = ""
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            jsonsql_input = st.text_area("输入文本", height=300, key="jsonsql_input")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("格式化 JSON"):
                try:
                    if jsonsql_input:
                        parsed = json.loads(jsonsql_input)
                        st.session_state.jsonsql_output = json.dumps(parsed, indent=4, ensure_ascii=False)
                    else:
                        st.session_state.jsonsql_output = ""
                except Exception as e:
                    st.session_state.jsonsql_output = f"JSON Error: {str(e)}"
                st.rerun()
            st.write("")
            if st.button("转 SQL IN"):
                if jsonsql_input:
                    items = [x.strip() for x in re.split(r'[\,\n]', jsonsql_input) if x.strip()]
                    if items:
                        quoted_items = [f"'{x.replace('\'', '\'\'')}'" for x in items]
                        st.session_state.jsonsql_output = f"IN ({', '.join(quoted_items)})"
                    else:
                        st.session_state.jsonsql_output = ""
                else:
                    st.session_state.jsonsql_output = ""
                st.rerun()
        with c3:
            st.text_area("结果", height=300, key="jsonsql_output")

    with tabs[1]:
        if "b64_output" not in st.session_state:
            st.session_state.b64_output = ""
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            b64_input = st.text_area("输入文本", height=200, key="b64_input")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("编码"):
                try:
                    st.session_state.b64_output = base64.b64encode(b64_input.encode("utf-8")).decode("utf-8") if b64_input else ""
                except Exception as e:
                    st.session_state.b64_output = f"Error: {str(e)}"
                st.rerun()
            st.write("")
            if st.button("解码"):
                try:
                    st.session_state.b64_output = base64.b64decode(b64_input.encode("utf-8")).decode("utf-8") if b64_input else ""
                except Exception as e:
                    st.session_state.b64_output = f"Error: {str(e)}"
                st.rerun()
        with c3:
            st.text_area("结果", height=200, key="b64_output")

    with tabs[2]:
        if "url_output" not in st.session_state:
            st.session_state.url_output = ""
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            url_input = st.text_area("输入文本", height=200, key="url_input")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("URL 编码"):
                try:
                    st.session_state.url_output = urllib.parse.quote(url_input, safe="") if url_input else ""
                except Exception as e:
                    st.session_state.url_output = f"Error: {str(e)}"
                st.rerun()
            st.write("")
            if st.button("URL 解码"):
                try:
                    st.session_state.url_output = urllib.parse.unquote(url_input) if url_input else ""
                except Exception as e:
                    st.session_state.url_output = f"Error: {str(e)}"
                st.rerun()
        with c3:
            st.text_area("结果", height=200, key="url_output")

    with tabs[3]:
        if "regex_output" not in st.session_state:
            st.session_state.regex_output = ""
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            regex_text = st.text_area("输入文本", height=200, key="regex_text")
            regex_pat = st.text_input("正则表达式", key="regex_pat")
            flag_i = st.checkbox("IGNORECASE", key="regex_i")
            flag_m = st.checkbox("MULTILINE", key="regex_m")
            flag_s = st.checkbox("DOTALL", key="regex_s")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("提取"):
                try:
                    flags = 0
                    if flag_i:
                        flags |= re.IGNORECASE
                    if flag_m:
                        flags |= re.MULTILINE
                    if flag_s:
                        flags |= re.DOTALL
                    if regex_pat:
                        matches = re.findall(regex_pat, regex_text or "", flags)
                        lines = []
                        for m in matches:
                            if isinstance(m, tuple):
                                lines.append("\t".join(str(x) for x in m))
                            else:
                                lines.append(str(m))
                        st.session_state.regex_output = "\n".join(lines)
                    else:
                        st.session_state.regex_output = ""
                except Exception as e:
                    st.session_state.regex_output = f"Error: {str(e)}"
                st.rerun()
        with c3:
            st.text_area("结果", height=200, key="regex_output")

    with tabs[4]:
        if "textproc_output" not in st.session_state:
            st.session_state.textproc_output = ""
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            tp_input = st.text_area("输入文本", height=200, key="tp_input")
            tp_action = st.selectbox("操作", ["去重", "去重并排序", "排序", "去空行", "去首尾空格", "转大写", "转小写", "Title Case"], key="tp_action")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("处理"):
                try:
                    lines = (tp_input or "").splitlines()
                    if tp_action == "去重":
                        st.session_state.textproc_output = "\n".join(list(dict.fromkeys(lines)))
                    elif tp_action == "去重并排序":
                        st.session_state.textproc_output = "\n".join(sorted(set(lines)))
                    elif tp_action == "排序":
                        st.session_state.textproc_output = "\n".join(sorted(lines))
                    elif tp_action == "去空行":
                        st.session_state.textproc_output = "\n".join([x for x in lines if x.strip()])
                    elif tp_action == "去首尾空格":
                        st.session_state.textproc_output = "\n".join([x.strip() for x in lines])
                    elif tp_action == "转大写":
                        st.session_state.textproc_output = "\n".join([x.upper() for x in lines])
                    elif tp_action == "转小写":
                        st.session_state.textproc_output = "\n".join([x.lower() for x in lines])
                    elif tp_action == "Title Case":
                        st.session_state.textproc_output = "\n".join([x.title() for x in lines])
                    else:
                        st.session_state.textproc_output = ""
                except Exception as e:
                    st.session_state.textproc_output = f"Error: {str(e)}"
                st.rerun()
        with c3:
            st.text_area("结果", height=200, key="textproc_output")

    with tabs[5]:
        if "date_output" not in st.session_state:
            st.session_state.date_output = ""
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            date_input = st.text_area("输入日期文本", height=200, key="date_input")
            date_in_fmt = st.text_input("输入格式", value="%Y-%m-%d", key="date_in_fmt")
            date_out_fmt = st.text_input("输出格式", value="%Y/%m/%d", key="date_out_fmt")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("转换"):
                try:
                    lines = (date_input or "").splitlines()
                    out_lines = []
                    for line in lines:
                        s = line.strip()
                        if not s:
                            continue
                        try:
                            dt = datetime.strptime(s, date_in_fmt)
                            out_lines.append(dt.strftime(date_out_fmt))
                        except Exception:
                            out_lines.append(s)
                    st.session_state.date_output = "\n".join(out_lines)
                except Exception as e:
                    st.session_state.date_output = f"Error: {str(e)}"
                st.rerun()
        with c3:
            st.text_area("结果", height=200, key="date_output")

    # Sidebar for API Key configuration
    with st.sidebar:
        st.header("配置")
        api_key = st.text_input("DeepSeek API Key", type="password")
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
        
        st.info("如果没有 API Key，请确保 .env 文件中已配置 DEEPSEEK_API_KEY。")
        
        st.divider()
        st.header("文件上传")
        uploaded_files = st.file_uploader(
            "上传文件 (CSV/Excel/文本/图片)",
            accept_multiple_files=True,
            type=["csv", "xlsx", "xls", "txt", "png", "jpg", "jpeg", "webp", "bmp", "gif"]
        )
        
        if uploaded_files:
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            for uploaded_file in uploaded_files:
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"已上传 {len(uploaded_files)} 个文件到 {upload_dir}/")

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
        if not os.environ.get("DEEPSEEK_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
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
                upload_dir = "uploads"
                uploaded_context = ""
                if os.path.exists(upload_dir):
                    files = os.listdir(upload_dir)
                    if files:
                        uploaded_context = f"\n\n[System Hint] Current uploaded files available in 'uploads/' directory: {', '.join(files)}. Use '*_upload' tools to process them."
                
                inputs = {"messages": [HumanMessage(content=user_input + uploaded_context)]}
                
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
