import streamlit as st
import requests
import shlex
import json

def _parse_curl_cmd(cmd):
    if not cmd: return
    try:
        cmd = cmd.strip()
        
        # Handle Windows CMD curl copy (often has caret ^ for line continuation)
        if "^" in cmd:
            cmd = cmd.replace("^\n", " ").replace("^", "")
        
        # Handle Bash line continuation
        if "\\" in cmd:
            cmd = cmd.replace("\\\n", " ").replace("\\", "")
            
        # Clean up newlines
        cmd = cmd.replace("\n", " ")
        
        if cmd.startswith("curl "):
            cmd = cmd[5:]
        
        tokens = shlex.split(cmd)
        
        method = "GET"
        url = ""
        headers = {}
        data = None
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token in ("-X", "--request"):
                if i + 1 < len(tokens):
                    method = tokens[i+1].upper()
                    i += 2
                else: i += 1
            elif token in ("-H", "--header"):
                if i + 1 < len(tokens):
                    h = tokens[i+1]
                    if ":" in h:
                        k, v = h.split(":", 1)
                        headers[k.strip()] = v.strip()
                    i += 2
                else: i += 1
            elif token in ("--cookie", "-b"):
                if i + 1 < len(tokens):
                    cookie_val = tokens[i+1]
                    # curl can pass filename or string. Here we assume string format "k=v; k2=v2"
                    # We add it to Cookie header
                    if "Cookie" in headers:
                        headers["Cookie"] += "; " + cookie_val
                    else:
                        headers["Cookie"] = cookie_val
                    i += 2
                else: i += 1
            elif token in ("-d", "--data", "--data-raw", "--data-binary"):
                if i + 1 < len(tokens):
                    data = tokens[i+1]
                    if method == "GET": method = "POST"
                    i += 2
                else: i += 1
            elif token == "--compressed":
                    # Ignored but supported to not break parsing
                    i += 1
            elif token.startswith("http") or token.startswith("www"):
                url = token
                i += 1
            else:
                if not url and not token.startswith("-"):
                    url = token
                i += 1
        
        st.session_state.req_method = method
        st.session_state.req_url = url
        st.session_state.req_headers = json.dumps(headers, indent=2, ensure_ascii=False)
        st.session_state.req_body = data if data else ""
        
    except Exception as e:
        st.error(f"解析 cURL 失败: {str(e)}")

def render_request_tab():
    st.markdown("#### HTTP 模拟请求")
    
    if "req_url" not in st.session_state:
        st.session_state.req_url = ""
    if "req_method" not in st.session_state:
        st.session_state.req_method = "GET"
    if "req_headers" not in st.session_state:
        st.session_state.req_headers = "{}"
    if "req_body" not in st.session_state:
        st.session_state.req_body = ""
    if "req_response" not in st.session_state:
        st.session_state.req_response = None

    curl_input = st.text_area("输入 cURL 命令或 URL", height=100, placeholder="curl -X POST https://api.example.com ...", key="curl_input")
    if st.button("解析并填充"):
        _parse_curl_cmd(curl_input)
        st.rerun()
        
    st.divider()
    
    c1, c2 = st.columns([1, 4])
    with c1:
        new_method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], 
                                    index=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"].index(st.session_state.req_method) 
                                    if st.session_state.req_method in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] else 0,
                                    key="req_method_select")
        st.session_state.req_method = new_method
    with c2:
        new_url = st.text_input("URL", value=st.session_state.req_url, key="req_url_input")
        st.session_state.req_url = new_url
        
    c3, c4 = st.columns(2)
    with c3:
        new_headers = st.text_area("Headers (JSON)", value=st.session_state.req_headers, height=150, key="req_headers_input")
        st.session_state.req_headers = new_headers
    with c4:
        new_body = st.text_area("Body", value=st.session_state.req_body, height=150, key="req_body_input")
        st.session_state.req_body = new_body
        
    if st.button("发送请求", type="primary"):
        try:
            headers_dict = {}
            if st.session_state.req_headers.strip():
                headers_dict = json.loads(st.session_state.req_headers)
            
            resp = requests.request(
                method=st.session_state.req_method,
                url=st.session_state.req_url,
                headers=headers_dict,
                data=st.session_state.req_body.encode('utf-8') if st.session_state.req_body else None,
                timeout=30
            )
            st.session_state.req_response = resp
        except Exception as e:
            st.error(f"请求失败: {str(e)}")
            
    if st.session_state.req_response:
        resp = st.session_state.req_response
        st.markdown(f"**Status:** `{resp.status_code} {resp.reason}`")
        
        r1, r2 = st.tabs(["Response Body", "Response Headers"])
        with r1:
            try:
                st.json(resp.json())
            except:
                st.text(resp.text)
        with r2:
            st.json(dict(resp.headers))
