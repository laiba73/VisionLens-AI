
import io
import time

import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# ---------- CONFIG ----------
MODELS = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]

# PASTE YOUR REAL KEY HERE (inside the quotes)
API_KEY = "AQ.Ab8RN6IWBu3_bBBSrQri4_v4ane97hOIx4birOhkfH2zgqd9pAit"

BASE_PROMPT = (
    "You are an expert image analyst. Use short, clear bullet points under simple headings. "
    "Answer follow-up questions about the image accurately."
)
MODE_PROMPTS = {
    "Full Analysis": "Describe in detail: main subjects, actions, colors, background, nearby objects, visible text, lighting and mood.",
    "Extract Text (OCR)": "Extract all visible text exactly as written. If none, say 'No text found'.",
    "Summarize Image": "Give a short summary of this image in 3-5 bullet points.",
    "Ask Your Image": "Answer the user's question about this image.",
}
MODE_INFO = {
    "Full Analysis": ("🔬", "A detailed breakdown of subjects, colors, background, lighting and mood."),
    "Extract Text (OCR)": ("📝", "Extracts all visible text from your image."),
    "Summarize Image": ("⚡", "A short and clear summary of the image."),
    "Ask Your Image": ("💬", "Ask any question about your image."),
}

st.set_page_config(page_title="VisionLens AI", page_icon="🔍", layout="wide")

# ---------- DESIGN ----------
st.markdown(
    """
    <style>
        [data-testid="stAppDeployButton"], #MainMenu, footer {visibility: hidden !important; display: none !important;}
        [data-testid="stDecoration"] {visibility: hidden !important; height: 0px !important;}
        [data-testid="stSidebarCollapseButton"], button[data-testid="stSidebarCollapseButton"] {
            visibility: visible !important; display: inline-flex !important; z-index: 999999 !important;}

        .stApp {background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 50%, #ecfeff 100%); color: #111827;}
        .block-container {padding-top: 2.5rem; max-width: 1000px;}

        /* ---- SIDEBAR ---- */
        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.88);
            border-right: 1px solid rgba(99,102,241,0.2);
        }
        [data-testid="stSidebar"] img {
            border-radius: 14px;
            border: 1px solid rgba(99,102,241,0.25);
            box-shadow: 0 6px 18px rgba(79,70,229,0.15);
        }
        .side-title {font-size: 1.6rem; font-weight: 800; color: #1e1b4b; margin-bottom: 14px;}

        [data-testid="stWidgetLabel"] p, [data-testid="stSidebar"] label p {
            font-size: 1.2rem !important; font-weight: 800 !important; color: #1e1b4b !important;
        }
        [data-baseweb="select"] > div {
            min-height: 54px; border: 2px solid #6366f1 !important; border-radius: 12px !important;
            background: #ffffff !important;
        }
        [data-baseweb="select"] div, [data-baseweb="select"] span {
            font-size: 1.15rem !important; font-weight: 700 !important; color: #1e1b4b !important;
        }
        [data-baseweb="popover"] li, [data-baseweb="menu"] li {font-size: 1.1rem !important; font-weight: 600 !important;}

        .mode-card {
            padding: 14px 16px; border-radius: 14px; margin: 10px 0 14px 0;
            background: linear-gradient(135deg, rgba(79,139,249,0.16), rgba(168,85,247,0.16));
            border: 1px solid rgba(99,102,241,0.3);
            font-size: 1.05rem; line-height: 1.5; color: #312e81;
        }
        .mode-card b {font-size: 1.2rem; color: #1e1b4b;}

        /* ---- HERO TITLE ---- */
        .hero {padding: 0.5rem 0 1.5rem 0;}
        .title-row {display: flex; align-items: center; gap: 14px; padding: 8px 0;}
        .title-emoji {font-size: 3.2rem; line-height: 1.3;}
        .title-text {
            font-size: 3.6rem; font-weight: 900; line-height: 1.35; padding: 6px 4px;
            background: linear-gradient(90deg, #1d4ed8, #7c3aed, #db2777);
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent; color: transparent;
            display: inline-block;
        }
        .subtitle {color: #334155; margin: 0.3rem 0 1.1rem 0; font-size: 1.3rem; font-weight: 500; line-height: 1.5;}
        .pill {
            display: inline-block; padding: 8px 18px; margin: 0 8px 8px 0;
            border-radius: 999px; font-size: 1rem; font-weight: 700;
            background: rgba(99,102,241,0.14); color: #3730a3;
            border: 1.5px solid rgba(99,102,241,0.35);
        }

        /* ---- STEP CARDS ---- */
        .step-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 0.8rem;}
        .step-card {
            padding: 22px; border-radius: 18px;
            background: rgba(255,255,255,0.95);
            border: 1px solid rgba(99,102,241,0.2);
            box-shadow: 0 8px 24px rgba(79,70,229,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .step-card:hover {transform: translateY(-4px); box-shadow: 0 14px 30px rgba(79,70,229,0.18);}
        .step-num {font-size: 2.8rem; font-weight: 900; color: #000000; line-height: 1;}
        .step-title {font-size: 1.3rem; font-weight: 800; color: #000000; margin-top: 8px;}
        .step-text {font-size: 1.05rem; color: #334155; margin-top: 4px; line-height: 1.5;}

        /* ---- CHAT ---- */
        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.95);
            border: 1px solid rgba(99,102,241,0.18);
            border-radius: 18px; padding: 1.1rem;
            box-shadow: 0 6px 22px rgba(79,70,229,0.08);
            margin-bottom: 1rem;
        }
        [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
            font-size: 1.12rem !important; line-height: 1.7; color: #111827 !important;
        }
        [data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3 {
            color: #1e1b4b !important; font-weight: 800;
        }
        [data-testid="stChatInput"] textarea {font-size: 1.1rem !important;}

        /* ---- BUTTONS ---- */
        .stButton > button {
            border-radius: 12px; padding: 0.7rem 1rem; min-height: 52px;
            transition: all 0.2s ease;
        }
        .stButton > button p {font-size: 1.15rem !important; font-weight: 800 !important;}
        .stButton > button:hover {transform: translateY(-2px); box-shadow: 0 8px 18px rgba(79,70,229,0.25);}
        button[kind="primary"], [data-testid="stBaseButton-primary"] {
            background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
            background-image: linear-gradient(90deg, #2563eb, #7c3aed) !important;
            border: none !important; color: #ffffff !important;
        }
        button[kind="primary"] p, [data-testid="stBaseButton-primary"] p {color: #ffffff !important;}

        .footer-note {text-align: center; color: #64748b; font-size: 0.95rem; margin-top: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_client() -> genai.Client:
    return genai.Client(api_key=API_KEY)


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.image_id = None


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="side-title">⚙️ Workspace Control</div>', unsafe_allow_html=True)
    analysis_mode = st.selectbox("🧠 Select Intelligence Mode", list(MODE_PROMPTS.keys()))
    icon, desc = MODE_INFO[analysis_mode]
    st.markdown(f'<div class="mode-card">{icon} <b>{analysis_mode}</b><br>{desc}</div>', unsafe_allow_html=True)
    st.divider()
    uploaded = st.file_uploader("📤 Upload target asset", type=["png", "jpg", "jpeg", "webp"])
    if uploaded:
        st.image(uploaded, use_container_width=True)
    run_clicked = st.button("🚀 Run", use_container_width=True, type="primary", disabled=not uploaded)
    clear = st.button("🗑️ Reset Application", use_container_width=True)

# ---------- Hero Header ----------
st.markdown(
    """
    <div class="hero">
        <div class="title-row">
            <span class="title-emoji">🔍</span>
            <span class="title-text">VisionLens AI</span>
        </div>
        <div class="subtitle">Multi-mode intelligence platform to unpack, scan, and converse with static images instantly.</div>
        <span class="pill">🔬 Full Analysis</span>
        <span class="pill">📝 OCR</span>
        <span class="pill">⚡ Summary</span>
        <span class="pill">💬 Ask Image</span>
    </div>
    """,
    unsafe_allow_html=True,
)

client = get_client()
if "messages" not in st.session_state or clear:
    reset_chat()

# ---------- Empty-state guide ----------
if not st.session_state.messages:
    if not uploaded:
        st.markdown(
            """
            <div class="step-grid">
                <div class="step-card"><div class="step-num">1</div>
                    <div class="step-title">Upload an image</div>
                    <div class="step-text">Choose a PNG, JPG or WEBP file from the left sidebar.</div></div>
                <div class="step-card"><div class="step-num">2</div>
                    <div class="step-title">Select a mode</div>
                    <div class="step-text">Full Analysis, OCR, Summary or Ask Your Image.</div></div>
                <div class="step-card"><div class="step-num">3</div>
                    <div class="step-title">Click Run</div>
                    <div class="step-text">Your results will stream here in real time.</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("✅ Your image is ready! Select a mode in the sidebar and click *🚀 Run*.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------- ENGINE with retry + model fallback ----------
def stream_with_fallback(contents, system_prompt):
    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.4)
    seen = set()
    last_err = None
    for model in MODELS:
        for attempt in range(3):
            got_text = False
            try:
                for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
                    if chunk.text:
                        got_text = True
                        yield chunk.text
                return
            except Exception as e:
                last_err = e
                msg = str(e)
                if got_text:
                    raise
                if "API_KEY_INVALID" in msg or "API key not valid" in msg:
                    raise RuntimeError("API_KEY_INVALID")
                if "503" in msg or "UNAVAILABLE" in msg:
                    seen.add("503")
                    time.sleep(2 ** (attempt + 1))
                    continue
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    seen.add("429")
                break  # try next model
    if "429" in seen:
        raise RuntimeError("QUOTA")
    if "503" in seen:
        raise RuntimeError("BUSY")
    raise last_err


def ask(contents, label: str, mode: str) -> None:
    st.session_state.messages.append({"role": "user", "content": label})
    with st.chat_message("user"):
        st.markdown(label)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        try:
            system_prompt = f"{BASE_PROMPT}\n\nCurrent mode: {mode}. {MODE_PROMPTS[mode]}"
            for text in stream_with_fallback(contents, system_prompt):
                full += text
                placeholder.markdown(full + "▌")
            placeholder.markdown(full)
            st.session_state.messages.append({"role": "assistant", "content": full})
        except Exception as err:
            msg = str(err)
            if "API_KEY_INVALID" in msg:
                st.error("Your API key is invalid. Please paste a valid Gemini API key in the code and restart the app.")
            elif "QUOTA" in msg:
                st.error("Daily quota reached. Please use a new API key, enable billing, or try again tomorrow.")
            elif "BUSY" in msg:
                st.error("The AI service is busy right now. Please click Run again in a few minutes.")
            else:
                st.error(f"Execution failed: {err}")


def load_image() -> Image.Image:
    return Image.open(io.BytesIO(uploaded.getvalue()))


# ---------- Run button ----------
if run_clicked and uploaded:
    reset_chat()
    st.session_state.image_id = f"{uploaded.name}-{uploaded.size}"
    ask([f"Perform mode: {analysis_mode} on this image.", load_image()],
        f"{MODE_INFO[analysis_mode][0]} {analysis_mode}", analysis_mode)

# ---------- Follow-up chat ----------
if prompt := st.chat_input("Ask a follow-up question about this image..."):
    if not uploaded:
        st.warning("Please upload an image first.")
    else:
        history = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:])
        ask([f"Previous conversation:\n{history}\n\nUser question: {prompt}", load_image()],
            prompt, "Ask Your Image")
