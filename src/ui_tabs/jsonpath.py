import streamlit as st
import json

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

def render_jsonpath_tab():
    if "jp_output" not in st.session_state:
        st.session_state.jp_output = ""
    
    c1, c2, c3 = st.columns([4, 1, 4])
    with c1:
        if "jp_json" not in st.session_state:
            st.session_state.jp_json = """{ 
   "store": { 
     "book": [ 
       { 
         "category": "reference", 
         "author": "Nigel Rees", 
         "title": "Sayings of the Century", 
         "price": 8.95 
       }, 
       { 
         "category": "fiction", 
         "author": "Evelyn Waugh", 
         "title": "Sword of Honour", 
         "price": 12.99 
       } 
     ], 
     "bicycle": { 
       "color": "red", 
       "price": 19.95 
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
