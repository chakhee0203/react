import streamlit as st
import json
import re

def render_jsonsql_tab():
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
