import streamlit as st
import base64
import urllib.parse
import html
import re

def render_codec_tab():
    if "codec_output_display" not in st.session_state:
        st.session_state.codec_output_display = ""
    if "codec_input" not in st.session_state:
        st.session_state.codec_input = ""
        
    st.markdown("#### 编解码工具")
    
    codec_mode = st.radio("选择模式", ["Base64", "URL", "Hex", "HTML", "Unicode"], horizontal=True)
    
    c1, c2, c3 = st.columns([4, 1, 4])
    with c1:
        st.text_area("输入文本", height=200, key="codec_input")
        
    with c2:
        st.write("")
        st.write("")
        if st.button("编码 / 加密"):
            try:
                txt = st.session_state.codec_input
                if codec_mode == "Base64":
                    res = base64.b64encode(txt.encode("utf-8")).decode("utf-8")
                elif codec_mode == "URL":
                    res = urllib.parse.quote(txt, safe="")
                elif codec_mode == "Hex":
                    res = txt.encode("utf-8").hex()
                elif codec_mode == "HTML":
                    res = html.escape(txt)
                elif codec_mode == "Unicode":
                    res = txt.encode("unicode_escape").decode("utf-8")
                else:
                    res = ""
                st.session_state["codec_output_display"] = res
            except Exception as e:
                st.session_state["codec_output_display"] = f"Error: {str(e)}"
            st.rerun()
            
        st.write("")
        if st.button("解码 / 解密"):
            try:
                txt = st.session_state.codec_input
                if codec_mode == "Base64":
                    res = base64.b64decode(txt.encode("utf-8")).decode("utf-8")
                elif codec_mode == "URL":
                    res = urllib.parse.unquote(txt)
                elif codec_mode == "Hex":
                    clean_txt = re.sub(r"\s+", "", txt)
                    res = bytes.fromhex(clean_txt).decode("utf-8")
                elif codec_mode == "HTML":
                    res = html.unescape(txt)
                elif codec_mode == "Unicode":
                    res = txt.encode("utf-8").decode("unicode_escape")
                else:
                    res = ""
                st.session_state["codec_output_display"] = res
            except Exception as e:
                st.session_state["codec_output_display"] = f"Error: {str(e)}"
            st.rerun()

    with c3:
        st.text_area("结果", height=200, key="codec_output_display")
