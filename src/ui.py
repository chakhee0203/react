import streamlit as st
import os
import re
import json
import base64
import urllib.parse
import difflib
import html
from datetime import datetime
import markdown
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
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from src.agent.react_agent import get_graph

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

    tabs = st.tabs(["JSON/SQL 工具", "Base64", "URL 编解码", "文本比对", "JSONPath 查询", "Markdown 编辑"])

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
        def _normalize_lines(text, ignore_ws, ignore_case):
            lines = (text or "").splitlines()
            out = []
            for s in lines:
                t = s
                if ignore_ws:
                    t = " ".join(t.split())
                if ignore_case:
                    t = t.lower()
                out.append(t)
            return out

        def _render_hunk(a_lines, b_lines, op, ctx=3):
            tag, i1, i2, j1, j2 = op
            a_start = max(0, i1 - ctx)
            a_end = min(len(a_lines), i2 + ctx)
            b_start = max(0, j1 - ctx)
            b_end = min(len(b_lines), j2 + ctx)

            def paint(line, kind):
                esc = html.escape(line)
                if kind == "equal":
                    return f"<span>{esc}</span>"
                if kind == "delete":
                    return f"<span style='background:#ffecec;'>{esc}</span>"
                if kind == "insert":
                    return f"<span style='background:#eaffea;'>{esc}</span>"
                if kind == "replace":
                    return f"<span style='background:#fff8e1;'>{esc}</span>"
                return f"<span>{esc}</span>"

            a_html_lines = []
            for idx in range(a_start, a_end):
                kind = "equal"
                if i1 <= idx < i2:
                    kind = "delete" if tag == "delete" else ("replace" if tag == "replace" else "equal")
                ln = paint(a_lines[idx], kind)
                a_html_lines.append(f"<div><span style='color:#999;'>L{idx+1}:</span> {ln}</div>")

            b_html_lines = []
            for idx in range(b_start, b_end):
                kind = "equal"
                if j1 <= idx < j2:
                    kind = "insert" if tag == "insert" else ("replace" if tag == "replace" else "equal")
                ln = paint(b_lines[idx], kind)
                b_html_lines.append(f"<div><span style='color:#999;'>L{idx+1}:</span> {ln}</div>")

            left = "".join(a_html_lines)
            right = "".join(b_html_lines)
            return f"<div style='display:flex;gap:16px;'><div style='flex:1;border:1px solid #eee;padding:8px;'><div style='font-weight:600;margin-bottom:6px;'>文本A</div><pre style='margin:0;'>{left}</pre></div><div style='flex:1;border:1px solid #eee;padding:8px;'><div style='font-weight:600;margin-bottom:6px;'>文本B</div><pre style='margin:0;'>{right}</pre></div></div>"

        if "diff_state" not in st.session_state:
            st.session_state.diff_state = {
                "ops": [],
                "cur": 0,
                "count": 0,
                "ignore_ws": True,
                "ignore_case": False,
                "a_lines": [],
                "b_lines": []
            }

        c1, c2 = st.columns([3, 2])
        with c1:
            diff_a = st.text_area("文本A", height=240, key="diff_a")
        with c2:
            diff_b = st.text_area("文本B", height=240, key="diff_b")

        opt1, opt2, opt3 = st.columns([1,1,2])
        with opt1:
            st.session_state.diff_state["ignore_ws"] = st.checkbox("忽略空白", value=st.session_state.diff_state["ignore_ws"]) 
        with opt2:
            st.session_state.diff_state["ignore_case"] = st.checkbox("忽略大小写", value=st.session_state.diff_state["ignore_case"]) 
        with opt3:
            if st.button("计算差异"):
                try:
                    a_norm = _normalize_lines(diff_a, st.session_state.diff_state["ignore_ws"], st.session_state.diff_state["ignore_case"]) 
                    b_norm = _normalize_lines(diff_b, st.session_state.diff_state["ignore_ws"], st.session_state.diff_state["ignore_case"]) 
                    sm = difflib.SequenceMatcher(None, a_norm, b_norm, autojunk=False)
                    ops = sm.get_opcodes()
                    non_equal_indices = [i for i,(t,_,_,_,_) in enumerate(ops) if t != "equal"]
                    st.session_state.diff_state["ops"] = ops
                    st.session_state.diff_state["count"] = len(non_equal_indices)
                    st.session_state.diff_state["cur"] = (non_equal_indices[0] if non_equal_indices else 0)
                    st.session_state.diff_state["a_lines"] = (diff_a or "").splitlines()
                    st.session_state.diff_state["b_lines"] = (diff_b or "").splitlines()
                except Exception as e:
                    st.warning(f"计算差异失败: {str(e)}")

        nav1, nav2, nav3 = st.columns([1,1,3])
        with nav1:
            if st.button("◀ 上一个差异"):
                cur = st.session_state.diff_state["cur"]
                ops = st.session_state.diff_state["ops"]
                prev = cur
                for i in range(cur-1, -1, -1):
                    if ops[i][0] != "equal":
                        prev = i
                        break
                st.session_state.diff_state["cur"] = prev
        with nav2:
            if st.button("下一个差异 ▶"):
                cur = st.session_state.diff_state["cur"]
                ops = st.session_state.diff_state["ops"]
                nxt = cur
                for i in range(cur+1, len(ops)):
                    if ops[i][0] != "equal":
                        nxt = i
                        break
                st.session_state.diff_state["cur"] = nxt
        with nav3:
            cnt = st.session_state.diff_state.get("count", 0)
            ops = st.session_state.diff_state.get("ops", [])
            cur = st.session_state.diff_state.get("cur", 0)
            if cnt == 0 and ops:
                st.info("两侧文本完全一致")
            elif ops:
                tag,i1,i2,j1,j2 = ops[cur]
                st.info(f"双向对比：共 {cnt} 处不同，当前第 {min([i for i,(t,_,_,_,_) in enumerate(ops) if t!='equal'].index(cur)+1 if cnt else 0, cnt)} 个 (A行 {i1+1}-{i2} / B行 {j1+1}-{j2})")

        ops = st.session_state.diff_state.get("ops", [])
        if ops:
            cur = st.session_state.diff_state["cur"]
            a_lines = st.session_state.diff_state["a_lines"]
            b_lines = st.session_state.diff_state["b_lines"]
            html_view = _render_hunk(a_lines, b_lines, ops[cur])
            st.markdown(html_view, unsafe_allow_html=True)

    with tabs[4]:
        if "jp_output" not in st.session_state:
            st.session_state.jp_output = ""
        def _jp_tokens(path: str):
            tokens = []
            i = 0
            n = len(path or "")
            while i < n:
                if path[i] == '$':
                    i += 1
                    continue
                if i + 1 < n and path[i:i+2] == '..':
                    i += 2
                    j = i
                    while j < n and path[j] not in '.[':
                        j += 1
                    name = path[i:j]
                    tokens.append(("rec", name))
                    i = j
                    continue
                if path[i] == '.':
                    i += 1
                    j = i
                    while j < n and path[j] not in '.[':
                        j += 1
                    name = path[i:j]
                    if name == '*':
                        tokens.append(("wild", None))
                    elif name:
                        tokens.append(("child", name))
                    i = j
                    continue
                if path[i] == '[':
                    j = i + 1
                    while j < n and path[j] != ']':
                        j += 1
                    content = path[i+1:j]
                    if content == '*':
                        tokens.append(("wild", None))
                    elif content.startswith("'") or content.startswith('"'):
                        name = content.strip("'\"")
                        tokens.append(("child", name))
                    elif ':' in content:
                        parts = content.split(':')
                        start = int(parts[0]) if parts[0] else None
                        end = int(parts[1]) if parts[1] else None
                        tokens.append(("slice", (start, end)))
                    else:
                        try:
                            idx = int(content)
                            tokens.append(("index", idx))
                        except Exception:
                            pass
                    i = j + 1
                    continue
                i += 1
            return tokens
        def _descend_collect(node, name):
            res = []
            stack = [node]
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    if name in cur:
                        res.append(cur[name])
                    stack.extend(cur.values())
                elif isinstance(cur, list):
                    stack.extend(cur)
            return res
        def jsonpath_query(json_text: str, path: str):
            try:
                obj = json.loads(json_text)
            except Exception as e:
                return f"JSON Error: {str(e)}"
            nodes = [obj]
            for t in _jp_tokens(path):
                kind = t[0]
                arg = t[1] if len(t) > 1 else None
                next_nodes = []
                if kind == "child":
                    for nd in nodes:
                        if isinstance(nd, dict) and arg in nd:
                            next_nodes.append(nd[arg])
                elif kind == "wild":
                    for nd in nodes:
                        if isinstance(nd, dict):
                            next_nodes.extend(list(nd.values()))
                        elif isinstance(nd, list):
                            next_nodes.extend(nd)
                elif kind == "rec":
                    for nd in nodes:
                        next_nodes.extend(_descend_collect(nd, arg))
                elif kind == "index":
                    for nd in nodes:
                        if isinstance(nd, list) and -len(nd) <= arg < len(nd):
                            next_nodes.append(nd[arg])
                elif kind == "slice":
                    start, end = arg
                    for nd in nodes:
                        if isinstance(nd, list):
                            next_nodes.extend(nd[slice(start, end)])
                nodes = next_nodes
            out_lines = []
            for v in nodes:
                if isinstance(v, (dict, list)):
                    out_lines.append(json.dumps(v, ensure_ascii=False, indent=2))
                else:
                    out_lines.append(str(v))
            return "\n".join(out_lines)
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            if "jp_json" not in st.session_state:
                st.session_state.jp_json = """{ 
   \"store\": { 
     \"book\": [ 
       { 
         \"category\": \"reference\", 
         \"author\": \"Nigel Rees\", 
         \"title\": \"Sayings of the Century\", 
         \"price\": 8.95 
       }, 
       { 
         \"category\": \"fiction\", 
         \"author\": \"Evelyn Waugh\", 
         \"title\": \"Sword of Honour\", 
         \"price\": 12.99 
       } 
     ], 
     \"bicycle\": { 
       \"color\": \"red\", 
       \"price\": 19.95 
     } 
   } 
 }"""
            jp_json = st.text_area("输入JSON", height=240, key="jp_json")
            jp_expr = st.text_input("JSONPath 表达式", value="$.store.book[*].author", key="jp_expr")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("查询"):
                st.session_state.jp_output = jsonpath_query(jp_json, jp_expr)
                st.rerun()
        with c3:
            st.text_area("结果", height=240, key="jp_output")

    with tabs[5]:
        if "md_input" not in st.session_state:
            st.session_state.md_input = "# Markdown 编辑器\n\n- 支持基本Markdown语法\n- 左侧编辑，右侧预览\n\n```python\nprint('Hello Markdown')\n```"
        if "md_html" not in st.session_state:
            st.session_state.md_html = markdown.markdown(st.session_state.md_input)
        c1, c2, c3 = st.columns([4, 1, 4])
        with c1:
            md_input = st.text_area("输入Markdown", height=300, key="md_input")
        with c2:
            st.write("")
            st.write("")
            st.write("")
            if st.button("预览"):
                st.session_state.md_html = markdown.markdown(md_input)
                st.rerun()
            html_doc = f"<!doctype html><html><head><meta charset='utf-8'><title>Markdown Export</title></head><body>{markdown.markdown(md_input)}</body></html>"
            st.download_button("导出 HTML", data=html_doc.encode("utf-8"), file_name="export.html", mime="text/html")
            st.download_button("导出 Markdown", data=md_input.encode("utf-8"), file_name="export.md", mime="text/markdown")
        with c3:
            st.markdown(st.session_state.md_html, unsafe_allow_html=True)

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
