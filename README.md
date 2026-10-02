# 💡 AI-Powered Code Edge Case Generator & Debugger

An advanced, web-based GenAI platform designed for coding students and developers. This application automatically generates hidden edge cases and boundary conditions for programming problems, executes user code against them in a secure sandbox, and provides line-by-line debugging feedback to pinpoint logical or syntax flaws.

---

## 🚀 Key Features

* **AI-Driven Edge Case Generation:** Leverages high-speed LLMs (via the Groq API) to craft complex, hidden boundary test cases that standard test suites often miss.
* **Automated Code Flaw Analysis:** Inspects the user's code to diagnose syntax errors, logical bugs, and incorrect assumptions, offering clear explanations on how to fix them.
* **Secure Sandbox Execution:** Safely runs user-submitted Python code locally or in the cloud using Python's `subprocess` module with strict timeouts.
* **Interactive Web UI:** Built with **Streamlit** for a seamless, user-friendly dashboard featuring visual pass/fail badges, expandable test details, and real-time execution results.

---

## 🛠️ Tech Stack

* **Frontend & Backend UI:** [Streamlit](https://streamlit.io/)
* **AI Provider / LLM:** Groq API (`openai/gpt-oss-20b`) via the OpenAI Python Client
* **Execution Environment:** Python `subprocess` & `tempfile` modules
* **Configuration:** `python-dotenv` for environment variable management

---

## ⚙️ Project Architecture & Workflow

1. **Input:** The user provides a problem description and their Python implementation.
2. **LLM Prompting:** The system sends a structured prompt to the Groq API enforcing a strict JSON output schema containing test cases and a potential flaw breakdown.
3. **Sandbox Testing:** A secure temporary file is created for the user code, which is then executed against each generated edge case input using isolated subprocess calls.
4. **Diagnostic Rendering:** The Streamlit dashboard visualizes whether each test passed or failed, alongside the AI's core debugging insights.

---

## 📦 Getting Started Locally

### Prerequisites
* Python 3.8 or higher installed on your machine.
* A free API key from [Groq Console](https://console.groq.com/).

### Installation Steps

1.Clone the repository:
   ```bash
   git clone [https://github.com/CNVSKumar/testcase_generator.git](https://github.com/CNVSKumar/testcase_generator.git)
   cd testcase_generator
   Install the required dependencies:

2.Install the required dependencies:
    pip install -r requirements.txt
3.Configure your Environment Variables:
    Create a .env file in the root directory of your project and add your Groq API key:
    GROQ_API_KEY=your_actual_groq_api_key_here
4.Run the Application:
    streamlit run frontend.py
5.Open your browser and navigate to http://localhost:8501.

🌐 Cloud Deployment
This application is fully optimized for cloud deployment on Streamlit Community Cloud:

1.Connect your GitHub repository to Streamlit Cloud.

2.Set the main file path to frontend.py.

3.Add your GROQ_API_KEY in the app's Secrets settings configuration (TOML format).

👨‍💻 Author
Developed as part of an advanced AI/ML engineering portfolio and internship project.