"""
Streamlit UI for Medical RAG Chatbot
Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import time

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
API_BASE_URL = "http://localhost:8000"
DEFAULT_TEMPERATURE = 0.3  # 🔒 medical-safe

st.set_page_config(
    page_title="Medical RAG Chatbot",
    page_icon="🏥",
    layout="wide"
)

# ------------------------------------------------------------------
# HEADER
# ------------------------------------------------------------------
st.title("🏥 Medical RAG Chatbot")
st.markdown(
    """
⚠️ **Medical Disclaimer**  
This assistant provides **medical information only**.  
It does **not** diagnose or prescribe treatment.  
Always consult a licensed healthcare professional.
"""
)

# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.header("Settings")

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = f"streamlit-{int(time.time())}"

    st.session_state.conversation_id = st.text_input(
        "Conversation ID",
        value=st.session_state.conversation_id
    )

    specialties = [
        "All",
        "cardiology",
        "endocrinology",
        "neurology",
        "oncology",
        "pediatrics",
        "gastroenterology",
        "infectious_disease",
        "pulmonology",
        "dermatology"
    ]

    specialty = st.selectbox("Medical Specialty", specialties)
    if specialty == "All":
        specialty = None

    with st.expander("Advanced (Safe Defaults)"):
        top_k = st.slider("Documents to retrieve", 1, 10, 5)
        st.slider(
            "Temperature (locked for safety)",
            0.0,
            1.0,
            DEFAULT_TEMPERATURE,
            disabled=True
        )

    st.divider()

    if st.button("Check API Health"):
        try:
            res = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if res.status_code == 200:
                st.success("API is healthy")
                st.json(res.json())
            else:
                st.error("API is unhealthy")
        except Exception as e:
            st.error(f"API not reachable: {e}")

    if st.button("New Conversation"):
        st.session_state.conversation_id = f"streamlit-{int(time.time())}"
        st.session_state.messages = []
        st.rerun()

# ------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------------------------------------------------------
# DISPLAY CHAT HISTORY
# ------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Sources"):
                for s in msg["sources"]:
                    st.markdown(
                        f"- **{s['file']}** — Relevance: {s['relevance']:.1f}%"
                    )

# ------------------------------------------------------------------
# CHAT INPUT
# ------------------------------------------------------------------
if prompt := st.chat_input("Ask a medical question..."):
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                start = time.time()

                payload = {
                    "question": prompt,
                    "conversation_id": st.session_state.conversation_id,
                    "top_k": top_k,
                    "temperature": DEFAULT_TEMPERATURE
                }

                if specialty:
                    payload["specialty"] = specialty

                res = requests.post(
                    f"{API_BASE_URL}/chat",
                    json=payload,
                    timeout=180
                )

                elapsed = time.time() - start

                if res.status_code == 200:
                    data = res.json()

                    answer = data.get("answer", "No response")
                    sources = data.get("sources", [])
                    context_used = data.get("context_used", False)
                    storage = data.get("storage", "unknown")

                    st.markdown(answer)

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Response Time", f"{elapsed:.1f}s")
                    c2.metric("Context Used", "Yes" if context_used else "No")
                    c3.metric("Storage", storage)

                    if sources:
                        with st.expander("📚 Sources"):
                            for s in sources:
                                st.markdown(
                                    f"- **{s['file']}** — Relevance: {s['relevance']:.1f}%"
                                )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    st.error(f"API Error: {res.status_code}")

            except requests.exceptions.Timeout:
                st.error("The model is taking too long. Please try again.")
            except Exception as e:
                st.error(str(e))

# ------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------
st.divider()
st.caption(
    "🏥 Medical information only. Not a substitute for professional medical advice."
)
