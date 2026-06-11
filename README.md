# JEE Solver Agent 🚀

> **An Advanced Multimodal AI Tutor for JEE Aspirants, powered by Google Gemini 2.5.**

Late-night JEE preparation often leaves students stuck on complex physics and math problems with no immediate help available. The **JEE Solver Agent** is designed to bridge this gap. It acts as a 24/7 personalized, human-like tutor that doesn't just give final answers but breaks down concepts step-by-step using text, voice, and image inputs.

---

## ✨ Key Features & System Insights

* **📸 Multimodal Problem Solving:** Students can upload images of complex mechanics or calculus problems, and the AI will extract the data, format it, and solve it flawlessly.
* **🗣️ Voice & "Hinglish" Support:** Typing math is hard! Users can ask doubts using a microphone in natural "Hinglish." The agent adapts to the student's language and provides conceptual clarity with real-life examples.
* **📚 Grounded Knowledge (Verified PYQs):** The AI's responses are strictly grounded using verified Previous Year Questions (PYQs) from JEE Mains and Advanced, ensuring high accuracy and exam relevance.
* **⚡ In-Memory Latency Cache:** An active caching system that instantly retrieves previously asked questions, bypassing API limits and reducing response latency to milliseconds.
* **✍️ Textbook-Style Formatting:** Generates highly readable mathematical derivations using LaTeX and structure-driven explanations.
* **⭐ Integrated Feedback Loop:** Users can rate explanations to help continuously evaluate and improve the AI's teaching quality.
* **🎛️ Session Personalization:** Students can pre-select their study module (Physics/Math) and difficulty level (Mains/Advanced) to get highly targeted responses.

---

## 🛠️ Tech Stack & Architecture

We implemented a fully decoupled architecture for high speed and scalability:

* **🖥️ Frontend UI:** Streamlit
* **⚙️ Backend API:** FastAPI
* **🧠 Core Intelligence:** Google Gemini 2.5 API
* **🗄️ Database (Cache & Insights):** MongoDB Cloud
* **☁️ Deployment:** Streamlit Cloud (Frontend) & Render (Backend)

---

## 🔄 How It Works (The Flow)

1. **User Input:** The student interacts with the Streamlit frontend (selects module/difficulty and inputs their doubt via text, audio, or image).
2. **Secure Transmission:** The UI sends a secure request to our FastAPI backend.
3. **Smart Cache Check:** The backend checks the MongoDB Cloud for a previously cached answer. If found, the In-Memory Latency Cache returns the solution instantly.
4. **AI Processing:** If not cached, the backend processes the multimodal input and queries the Gemini 2.5 API, ensuring the response is grounded in our PYQ parameters.
5. **Output & Store:** Gemini perfectly formats the response. The backend sends it back to the UI and saves the new Q&A in the MongoDB cache for future users.

---

## 👥 Team & Contributions

### 👩‍💻 Disha
* **Frontend & UI Engineering:** Designed and built the interactive web application from scratch using Streamlit.
* **Repository & Deployment:** Managed version control, resolved full-stack integration bugs, and deployed the frontend live on Streamlit Cloud.
* **Demonstration:** Scripted, directed, and recorded the final product pitch and video demonstration.

### 👩‍💻 Kiran
* **Backend Architecture:** Developed the robust and lightweight backend server using FastAPI and deployed it live on Render.
* **AI & Database:** Handled the Google Gemini 2.5 API integration for multimodal processing and set up MongoDB Cloud for the caching system.
* **Presentation & Documentation:** Designed the official project presentation (PPT), visualizing the technical system architecture, user flow, and the market impact of our AI tutor.

---

## 📜 License

This project is open-source and available under the **MIT License**.
