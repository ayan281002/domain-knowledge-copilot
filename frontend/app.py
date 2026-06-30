import json
import os
from datetime import datetime

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Domain Knowledge Co-Pilot", page_icon="📚", layout="wide")
st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
html, body, [class*="css"]  { font-family: 'Space Grotesk', sans-serif; }
.stApp {
    background: radial-gradient(circle at 20% 10%, #f8f5ec 0%, #e8f1f2 45%, #d5e0f3 100%);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #113946 0%, #1a5f7a 100%);
}
[data-testid="stSidebar"] * { color: #f2f7fa !important; }
</style>
""",
        unsafe_allow_html=True,
)

if "token" not in st.session_state:
    st.session_state.token = None
if "selected_corpus" not in st.session_state:
    st.session_state.selected_corpus = None
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}


def api_post(path: str, json_data=None, files=None):
    return requests.post(f"{BACKEND_URL}{path}", json=json_data, files=files, headers=api_headers(), timeout=180)


def api_get(path: str):
    return requests.get(f"{BACKEND_URL}{path}", headers=api_headers(), timeout=180)


def api_delete(path: str):
    return requests.delete(f"{BACKEND_URL}{path}", headers=api_headers(), timeout=180)


def login_ui():
    st.sidebar.subheader("Authentication")
    mode = st.sidebar.radio("Mode", ["Login", "Register"], horizontal=True)

    with st.sidebar.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        email = st.text_input("Email") if mode == "Register" else None
        submit = st.form_submit_button(mode)

    if submit:
        if mode == "Register":
            payload = {"email": email, "username": username, "password": password}
            r = api_post("/auth/register", json_data=payload)
            if r.ok:
                st.sidebar.success("Registered. Please login.")
            else:
                st.sidebar.error(r.text)
        else:
            payload = {"username": username, "password": password}
            r = api_post("/auth/login", json_data=payload)
            if r.ok:
                st.session_state.token = r.json()["access_token"]
                st.sidebar.success("Logged in")
            else:
                st.sidebar.error(r.text)


def corpora_ui():
    st.sidebar.subheader("Corpora")
    r = api_get("/corpora")
    corpora = r.json() if r.ok else []
    names = {f"{c['id']} - {c['name']}": c for c in corpora}

    selected_label = st.sidebar.selectbox("Corpus selector", ["None"] + list(names.keys()))
    if selected_label != "None":
        st.session_state.selected_corpus = names[selected_label]["id"]

    with st.sidebar.expander("New corpus"):
        with st.form("new_corpus"):
            name = st.text_input("Name")
            description = st.text_area("Description")
            create = st.form_submit_button("Create")
        if create and name:
            rc = api_post("/corpora", json_data={"name": name, "description": description})
            if rc.ok:
                st.success("Corpus created")
                st.rerun()
            else:
                st.error(rc.text)

    if st.session_state.selected_corpus:
        if st.sidebar.button("Delete selected corpus"):
            rd = api_delete(f"/corpora/{st.session_state.selected_corpus}")
            if rd.status_code == 204:
                st.session_state.selected_corpus = None
                st.session_state.current_session = None
                st.session_state.chat_messages = []
                st.rerun()


def upload_ui():
    if not st.session_state.selected_corpus:
        st.sidebar.info("Select corpus first")
        return

    st.sidebar.subheader("Upload documents")
    file = st.sidebar.file_uploader("Upload PDF, DOCX, TXT, MD", type=["pdf", "docx", "txt", "md"])
    if st.sidebar.button("Index file") and file:
        files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
        r = api_post(f"/corpora/{st.session_state.selected_corpus}/upload", files=files)
        if r.ok:
            st.sidebar.success(r.json())
        else:
            st.sidebar.error(r.text)


def sessions_ui():
    st.sidebar.subheader("Chat history")
    if not st.session_state.selected_corpus:
        return

    rs = api_get(f"/sessions?corpus_id={st.session_state.selected_corpus}")
    sessions = rs.json() if rs.ok else []
    if sessions:
        options = {f"#{s['id']} - {s['title']} ({s['created_at'][:10]})": s["id"] for s in sessions}
        selected = st.sidebar.selectbox("History viewer", ["None"] + list(options.keys()))
        if selected != "None":
            st.session_state.current_session = options[selected]

    new_chat = st.sidebar.button("New chat")
    if new_chat:
        r = api_post("/sessions", json_data={"corpus_id": st.session_state.selected_corpus, "title": "New session"})
        if r.ok:
            st.session_state.current_session = r.json()["id"]
            st.session_state.chat_messages = []

    if st.session_state.current_session:
        rm = api_get(f"/sessions/{st.session_state.current_session}/messages")
        if rm.ok:
            st.session_state.chat_messages = rm.json()

        if st.sidebar.button("Delete current chat"):
            rd = api_delete(f"/sessions/{st.session_state.current_session}")
            if rd.status_code == 204:
                st.session_state.current_session = None
                st.session_state.chat_messages = []
                st.rerun()


def render_chat(debug: bool):
    st.title("Domain Knowledge Co-Pilot")
    st.caption("Chat with your private corpora using RAG")

    for message in st.session_state.chat_messages:
        role = "assistant" if message["role"] == "answer" else "user"
        with st.chat_message(role):
            st.markdown(message["content"])
            if role == "assistant" and message.get("citations_json"):
                citations = json.loads(message["citations_json"])
                for i, c in enumerate(citations, start=1):
                    label = f"[{i}] {c['source_file']} page {c['page'] if c['page'] else '-'}"
                    with st.expander(label):
                        st.write(c["excerpt"])

    question = st.chat_input("Ask a question about your selected corpus")
    if question and st.session_state.selected_corpus:
        with st.chat_message("user"):
            st.markdown(question)

        payload = {"question": question, "session_id": st.session_state.current_session}
        r = api_post(f"/corpora/{st.session_state.selected_corpus}/query", json_data=payload)
        if not r.ok:
            st.error(r.text)
            return

        data = r.json()
        st.session_state.current_session = data["session_id"]

        with st.chat_message("assistant"):
            st.markdown(data["answer"])
            for i, c in enumerate(data["citations"], start=1):
                label = f"[{i}] {c['source_file']} page {c['page'] if c['page'] else '-'}"
                with st.expander(label):
                    st.write(c["excerpt"])

            if debug:
                st.subheader("Debug")
                st.json(data["retrieved_chunks"])

        rm = api_get(f"/sessions/{st.session_state.current_session}/messages")
        if rm.ok:
            st.session_state.chat_messages = rm.json()


login_ui()

if st.session_state.token:
    corpora_ui()
    upload_ui()
    sessions_ui()
    debug_toggle = st.sidebar.toggle("Debug retrieved chunks", value=False)
    render_chat(debug_toggle)
else:
    st.title("Domain Knowledge Co-Pilot")
    st.info("Login from sidebar to continue")
