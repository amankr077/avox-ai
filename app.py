import streamlit as st
import requests
import re
from datetime import datetime
import tempfile
import subprocess
import sys
import os
from dotenv import load_dotenv
load_dotenv()

PROJECT_NAME = "Avox.ai"
MODEL_NAME = "llama-3.1-8b-instant"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_API_KEY = os.getenv("GROQ_API_KEY", "")

COL1 = "#A7D129" 
COL2 = "#616F39" 
COL3 = "#3E432E"  
COL4 = "#000000" 

if "messages" not in st.session_state:
    st.session_state.messages = []
st.session_state.api_key = DEFAULT_API_KEY
st.session_state.api_key_valid = True

# ---- MODERN CUSTOM GLASSMORPHIC UI ----
st.set_page_config(page_title=PROJECT_NAME, layout="wide")
st.markdown(f"""
<style>
body, [data-testid="stAppViewContainer"] {{
    background: linear-gradient(110deg, {COL4} 60%, {COL3} 100%) !important;
}}
.avox-topbanner {{
    width:100%;padding:1.35em 0 .85em 0;
    text-align:center;
    border-radius:0 0 21px 21px;
    background:linear-gradient(90deg,{COL2}B0 10%,{COL3}A0 90%);
    box-shadow:0 6px 24px 0 #191a0e38;
    margin-bottom:.95em;
    border-bottom:2.4px solid {COL1}88;
}}
.avox-title {{
    font-size:2.3rem;letter-spacing:0.037em;
    color:{COL1};font-weight:670;
    text-shadow:0 2px 22px {COL2}33;
    margin-bottom:.22em;margin-top:.08em;
    font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
}}
.sidebar-navbox {{
    background: linear-gradient(109deg,{COL2}33 60%,{COL3}B0 100%);
    border-radius: 21px;
    margin: 19px 0 30px 0;
    box-shadow: 0 2px 24px 0 #2e513922;
    padding: 22px 17px 16px 18px;
    border: 1.8px solid {COL1}55;
}}
.sb-chan {{
    border-radius: 13px;
    margin-bottom: 10px;
    background: {COL2}27;
    padding: 9px 14px 9px 15px;
    font-size: 1.09em;
    color: #ebf2cc;
}}
.sb-chan.sel {{
    background: linear-gradient(93deg,{COL1}AA 60%,{COL2} 100%);
    border-left: 5px solid {COL1}EE;
    color: {COL4};
    font-weight: 600;
}}
.sb-status {{
    font-weight:500;font-size:1.03em;margin:22px 0 13px 2px; color:{COL1};
}}
.sb-link {{
    margin-top: 24px; 
    font-size:1em;
    color:{COL1};opacity:.93;
}}
.avox-glasschatwrap {{
    flex:1 1 auto;
    overflow:auto;
    padding:.29em 0 .32em 0;
    margin-top:6px;
    min-height:430px;
}}
.glassmsg {{
    border-radius:17px;
    margin-bottom:13px;
    box-shadow:0 0 13px 0 {COL3}45;
    padding:1.11em 1.4em 1.1em 1.2em;
    max-width:84%;
    background: linear-gradient(99deg,{COL3}BB 80%, {COL2}77 100%);
    border:1.8px solid {COL1}45;
    transition:.13s;position:relative;word-break:break-word;
}}
.glassmsg.user {{
    align-self:flex-end;
    background:linear-gradient(111deg,{COL2}DD 70%,{COL1}59 100%);
    border-left:5px solid {COL1}BD;
    color:{COL4};
    margin-left:auto;
    box-shadow:0 2px 12px 0 {COL2}30;
    font-weight:520;
}}
.glassmsg.ai {{
    align-self:flex-start;
    background:linear-gradient(113deg,{COL3}D0 85%,{COL2}22 100%);
    border-left:5px solid {COL1}A2;
    color:#F7FDF0;
    margin-right:auto;
    box-shadow:0 2px 22px 0 {COL1}18;
    font-weight:520;
}}
.stChatInputContainer{{
    background:linear-gradient(99deg,{COL2}BB 86%,{COL3}68 100%);
    border-radius:14px!important;
}}
.stTextInput>div>div>input{{background:rgba(246,245,252,.18)!important;color:{COL1}!important;}}
.stButton>button{{
    background:{COL2}B0;color:{COL1};
    border-radius:14px;padding:.53em 1.33em;
    border:1.5px solid {COL1}33;
    font-weight:580;
}}
::-webkit-scrollbar-thumb{{background:{COL2} !important;}}
::-webkit-scrollbar-track{{background:{COL3} !important;}}
</style>
<div class="avox-topbanner">
    <span class="avox-title">{PROJECT_NAME}</span>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown(
        f"""
        <div class='sidebar-navbox'>
            <div style="font-weight:600;font-size:1.19em;color:{COL1};margin-bottom:1.1em;">Navigation</div>
            <div class='sb-chan sel'>Home (Chat)</div>
            <div class='sb-chan'>Stats</div>
            <div class='sb-chan'>Leaderboard</div>
            <div class='sb-status'>Status: <span style="color:{COL1};">Connected</span></div>
            <div class='sb-link'><a href='#' style='color:{COL1};text-decoration:none;'>Settings</a></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []

# ---- MAIN PANEL ----
st.markdown('<div class="avox-glasschatwrap">', unsafe_allow_html=True)

def system_prompt():
    return (
        f"You are avox.ai, a super helpful expert coding assistant.\n"
        "Reply with clear, well-commented, copy-paste ready code samples in markdown code blocks, explanations, and best practices. "
        "For coding tasks, specify the programming language and provide enough detail for a beginner to understand your solution."
    )

def call_llama(messages, api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": MODEL_NAME,
        "temperature": 0.1,
        "max_tokens": 2048,
        "messages": [{"role": "system", "content": system_prompt()}] + messages,
        "stream": False
    }
    try:
        r = requests.post(API_URL, headers=headers, json=data, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API connection error: {str(e)}")
    return None

def extract_code_blocks(text):
    matches = re.findall(r"``````", text, re.DOTALL)
    return [{"language": lang or "text", "code": code.strip()} for lang, code in matches]

def run_python_code(code):
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            f.flush()
            tmp_path = f.name
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        os.unlink(tmp_path)
        if proc.returncode == 0:
            return True, proc.stdout
        else:
            return False, proc.stderr
    except Exception as e:
        return False, f"Error during code execution:\n{e}"

def show_message(msg, is_user):
    cls = "user" if is_user else "ai"
    st.markdown(
        f"""<div class="glassmsg {cls}">
        <div style="font-size:13px;color:{COL1 if is_user else '#D8F3A2'};font-weight:540;padding-bottom:4px;letter-spacing:0.014em;">
            {"You" if is_user else "Avox.ai"}
            <span style="font-size:10.2px;float:right;color:#bab8ce;font-weight:400;">{msg.get('timestamp')}</span>
        </div>
        <div style='font-size:16px;'>{msg["content"]}</div>
        </div>""",
        unsafe_allow_html=True
    )
    if not is_user:
        for i, blk in enumerate(extract_code_blocks(msg['content'])):
            st.markdown(
                f"<span style='background:{COL2};color:{COL1};padding:1.4px 13px;border-radius:11px;"
                f"font-size:11.3px;margin-left:.5px;'>{blk['language'].upper()}</span>",
                unsafe_allow_html=True
            )
            st.code(blk['code'], language=blk['language'])
            if blk['language'].lower() == "python":
                if st.button("Run Python Code", key=f"runpy_{i}_{len(st.session_state.messages)}"):
                    success, output = run_python_code(blk['code'])
                    if success:
                        st.success("Program output:")
                        st.code(output)
                    else:
                        st.error("Error:")
                        st.code(output, language="text")

for msg in st.session_state.messages:
    show_message(msg, is_user=(msg["role"] == "user"))

prompt = st.chat_input("Type a coding question or request code...")
if prompt:
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": now})
    show_message(st.session_state.messages[-1], is_user=True)
    with st.spinner("Avox.ai is analyzing your prompt..."):
        context = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[-8:]
        ]
        answer = call_llama(context, st.session_state.api_key)
        if answer:
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "timestamp": datetime.now().strftime("%H:%M:%S")}
            )
            show_message(st.session_state.messages[-1], is_user=False)
        else:
            st.error("No response from server. Try again!")

st.markdown('</div>', unsafe_allow_html=True)

# ---- FOOTER ----
st.markdown(f"""
<hr style="margin-top:35px;">
<div style="text-align:center;font-size:13px;color:#eee;margin-bottom:15px;">
    {datetime.now().year} {PROJECT_NAME}
</div>
""", unsafe_allow_html=True)
