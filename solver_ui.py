import streamlit as st
import requests

# Backend API URLs
API_URL = "https://jee-solver-agent.onrender.com/api/ask"
FEEDBACK_URL = "https://jee-solver-agent.onrender.com/api/feedback"

# --- Page Configuration ---
st.set_page_config(page_title="JEE Solver Agent", page_icon="🚀", layout="wide")

# Custom CSS for Title
st.markdown("""
<style>
.main-title { font-size: 36px; font-weight: bold; color: #333; margin-bottom: 0px;}
.sub-title { font-size: 16px; color: #666; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ SIDEBAR (CONTROL PANEL)
# ==========================================
st.sidebar.title("⚙️ Control Panel")
selected_subject = st.sidebar.selectbox(
    "📚 Select Subject Module",
    ["Physics", "Chemistry", "Mathematics"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 System Information")
st.sidebar.info("🤖 Answer generation: Gemini 2.5 Flash")
st.sidebar.caption("Reference search uses MongoDB Atlas when relevant database entries are available.")
st.sidebar.caption("Repeated text questions may be served from an in-memory cache.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p style='font-size: 0.9em; color: #555;'>🔥 Powered by <b>IIT Delhi EE Project Group</b></p>",
    unsafe_allow_html=True
)

# ==========================================
# 🖥️ MAIN CHAT INTERFACE
# ==========================================
st.markdown('<p class="main-title">JEE Complete Solver Agent 🚀</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Multimodal Hackathon Submission Pipeline</p>', unsafe_allow_html=True)
st.markdown("---")

st.info("🤖 Hello! I am your AI JEE Tutor. Type a question, upload a photo, or send a voice note below.")

st.markdown("📎 **Attach Media (Optional)**")
col1, col2 = st.columns(2)
with col1:
    image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
with col2:
    audio_file = st.audio_input("Record Voice Note")

st.markdown("<br><br>", unsafe_allow_html=True)

# --- CHAT INPUT & LOGIC ---
student_query = st.chat_input("Ask your JEE doubt here...")

if student_query:
    with st.spinner("AI is analyzing your doubt..."):
        try:
            data = {
                "subject": selected_subject,
                "student_query": student_query
            }

            files = {}
            if image_file:
                files["image"] = (image_file.name, image_file, image_file.type)
            if audio_file:
                files["audio"] = (audio_file.name, audio_file, audio_file.type)

            response = requests.post(API_URL, data=data, files=files, timeout=120)

            if response.status_code == 200:
                result = response.json()

                st.session_state["last_query"] = student_query
                st.session_state["last_answer"] = result.get("answer", "")

                st.success("✅ Solution Ready!")
                st.markdown(result.get("answer", "No answer received."))
            else:
                st.error(f"Backend Error ({response.status_code}): {response.text}")

        except requests.Timeout:
            st.error("The solver is taking longer than expected. Please try again in a moment.")
        except requests.RequestException as e:
            st.error(f"Could not reach the solver backend: {e}")
        except Exception as e:
            st.error(f"Something went wrong while preparing your request: {e}")

# --- Feedback System ---
if "last_answer" in st.session_state and st.session_state["last_answer"]:
    st.markdown("---")
    st.write("**Was this solution helpful?**")

    fb_col1, fb_col2 = st.columns(2)
    with fb_col1:
        if st.button("👍 Yes, it's correct!"):
            try:
                feedback_response = requests.post(
                    FEEDBACK_URL,
                    json={
                        "student_query": st.session_state["last_query"],
                        "ai_answer": st.session_state["last_answer"],
                        "status": "Correct"
                    },
                    timeout=30
                )
                feedback_response.raise_for_status()
                st.success("Thanks for your feedback! Data saved.")
            except requests.RequestException:
                st.error("Feedback could not be saved. Please try again later.")

    with fb_col2:
        if st.button("👎 No, it's wrong"):
            try:
                feedback_response = requests.post(
                    FEEDBACK_URL,
                    json={
                        "student_query": st.session_state["last_query"],
                        "ai_answer": st.session_state["last_answer"],
                        "status": "Incorrect"
                    },
                    timeout=30
                )
                feedback_response.raise_for_status()
                st.success("Thanks for reporting. We will improve our AI.")
            except requests.RequestException:
                st.error("Feedback could not be saved. Please try again later.")
