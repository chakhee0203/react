import streamlit as st
import markdown

def render_markdown_tab():
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
