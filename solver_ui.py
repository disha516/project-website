import streamlit as st
import requests

# Backend API URLs
API_URL = "https://jee-solver-agent.onrender.com/api/ask"
FEEDBACK_URL = "https://jee-solver-agent.onrender.com/api/feedback"

st.set_page_config(page_title="JEE Solver Agent", page_icon="🚀", layout="wide")

st.markdown("""
<style>
.main-title { font-size: 36px; font-weight: bold; color: #333; margin-bottom: 0px;}
.sub-title { font-size: 16px; color: #666; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Keep the existing Control Panel layout and controls intact.
st.sidebar.title("⚙️ Control Panel")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

selected_subject = st.sidebar.selectbox(
    "📚 Select Subject Module",
    ["Physics", "Chemistry", "Mathematics"]
)
selected_difficulty = st.sidebar.select_slider(
    "🎯 Set Problem Level",
    options=["Easy", "Medium", "Hard", "JEE Advanced"],
    value="Easy"
)

st.sidebar.markdown("---")
search_priority = st.sidebar.radio(
    "🔍 Search Priority",
    ["Vector Database (Fast)", "Full AI Engine Fallback"]
)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("### 📊 System Insights")
st.sidebar.info("🟡 MongoDB Atlas: connection configured; live connectivity needs verification.")
st.sidebar.info("📚 Grounded Knowledge:\nMongoDB Atlas reference search")
st.sidebar.warning("⚡ In-Memory Latency Cache:\nActive for repeated text questions")

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p style='font-size: 0.9em; color: #555;'>🔥 Powered by <b>IIT Delhi EE Project Group</b></p>",
    unsafe_allow_html=True,
)

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
student_query = st.chat_input("Ask your JEE doubt here...")

if student_query or image_file or audio_file:
    with st.spinner("AI is analyzing your doubt..."):
        try:
            data = {
                "subject": selected_subject,
                "difficulty": selected_difficulty,
                "search_priority": search_priority,
                "student_query": student_query or "",
            }
            files = {}
            if image_file:
                files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
            if audio_file:
                files["audio"] = (audio_file.name, audio_file.getvalue(), "audio/wav")

            response = requests.post(API_URL, data=data, files=files or None, timeout=150)
            response.raise_for_status()
            result = response.json()
            answer = result.get("answer", "")
            if not answer:
                st.error("The backend returned an empty answer. Please try again.")
            else:
                st.session_state["last_query"] = student_query or "[Image/voice question]"
                st.session_state["last_answer"] = answer
                st.success("✅ Solution Ready!")
                st.markdown(answer)
        except requests.Timeout:
            st.error("The solver is taking longer than expected. Please try again in a moment.")
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            st.error(f"Backend error: {detail}")
        except requests.RequestException as exc:
            st.error(f"Could not reach the solver backend: {exc}")
        except Exception as exc:
            st.error(f"Something went wrong while preparing your request: {exc}")

if st.session_state.get("last_answer"):
    st.markdown("---")
    st.write("**Was this solution helpful?**")
    fb_col1, fb_col2 = st.columns(2)
    with fb_col1:
        if st.button("👍 Yes, it's correct!"):
            try:
                feedback_response = requests.post(
                    FEEDBACK_URL,
                    json={
                        "student_query": st.session_state.get("last_query", ""),
                        "ai_answer": st.session_state["last_answer"],
                        "status": "Correct",
                    },
                    timeout=30,
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
                        "student_query": st.session_state.get("last_query", ""),
                        "ai_answer": st.session_state["last_answer"],
                        "status": "Incorrect",
                    },
                    timeout=30,
                )
                feedback_response.raise_for_status()
                st.success("Thanks for reporting. We will improve our AI.")
            except requests.RequestException:
                st.error("Feedback could not be saved. Please try again later.")
