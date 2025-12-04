import streamlit as st
import difflib
import html

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

def render_diff_tab():
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
