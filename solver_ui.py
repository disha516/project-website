import streamlit as st
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="JEE Rapid Solver Agent", page_icon="🚀", layout="wide")

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
    .main-title { font-size: 40px; font-weight: bold; color: #1E3A8A; }
    .sub-title { font-size: 18px; color: #6B7280; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Filters & Navigation) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg", width=50)
st.sidebar.title("Agent Controls")
selected_subject = st.sidebar.selectbox("Select Subject:", ["Physics", "Chemistry", "Mathematics"])
selected_difficulty = st.sidebar.select_slider("Difficulty Level:", options=["Easy", "Medium", "Hard", "JEE Advanced"])
st.sidebar.markdown("---")
st.sidebar.info("Backend Integration Status: Pending (Waiting for Database)")

# --- MAIN CHAT INTERFACE ---
st.markdown('<p class="main-title">JEE Complete Solver Agent 🚀</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Google Cloud Rapid Agent Hackathon Submission</p>', unsafe_allow_html=True)

# Chat history state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI JEE Tutor. Please type your question below."}
    ]

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask your JEE doubt here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Dummy Assistant Response (This is where Kiran will add her backend code)
    with st.chat_message("assistant"):
        with st.spinner("Searching Database & AI Engine..."):
            time.sleep(1.5) # Simulating loading time
            dummy_response = f"**Simulated Response:** You asked about '{prompt}' in {selected_subject}. \n\n*Note for Team: Insert MongoDB Vector Search and Gemini API integration here.*"
            st.markdown(dummy_response)
            
            # Showing off Expanders and LaTeX to Kiran
            with st.expander("View Step-by-Step Mathematical Breakdown (Sample)"):
                st.write("This section will render complex LaTeX equations once the backend is linked.")
                st.latex(r"\oint \mathbf{E} \cdot d\mathbf{a} = \frac{Q_{enc}}{\varepsilon_0}")
                
    st.session_state.messages.append({"role": "assistant", "content": dummy_response})