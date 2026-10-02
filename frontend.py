import os
import subprocess
import tempfile
from dotenv import load_dotenv  # Added to load local .env file
import streamlit as st
from openai import OpenAI

# Load local environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI Code Edge Case & Debug Platform", layout="wide"
)

st.title("💡 AI-Powered Code Edge Case Generator & Debugger")
st.markdown(
    "Submit your problem and code. Our platform generates hidden edge cases,"
    " runs your code against them, and pinpoints where you fail!"
)

# Safe API key retrieval for both local and cloud environments
api_key = None
try:
  if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
  elif "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
  pass

# Fallback to environment variables / .env if not found in secrets
if not api_key:
  api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")

# Choose client setup based on available keys
# Choose client setup based on available keys
if api_key and api_key.startswith("gsk_"):
  client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
  MODEL_NAME = "openai/gpt-oss-20b"  # Reliable Groq model name
else:
  client = OpenAI(api_key=api_key)
  MODEL_NAME = "gpt-4o-mini"
# Input Section Form
with st.form("code_form"):
  problem_description = st.text_area(
      "📝 Problem Description",
      placeholder=(
          "e.g., Check if a string can be made a valid string by removing at"
          " most one character."
      ),
      height=100,
  )

  user_code = st.text_area(
      "💻 Your Python Code",
      placeholder="def check(s):\n    # write your logic here\n    return 'YES'",
      height=200,
  )

  submitted = st.form_submit_button(
      "Analyze & Run Edge Cases", type="primary"
  )

if submitted:
  if not problem_description.strip() or not user_code.strip():
    st.warning("Please fill in both the problem description and your code.")
  elif not api_key:
    st.error(
        "⚠️ API Key not found! Please configure your `GROQ_API_KEY` or"
        " `OPENAI_API_KEY` in Streamlit Secrets or environment variables."
    )
  else:
    with st.spinner(
        "🤖 AI is crafting edge cases & testing your code in the sandbox..."
    ):
      try:
        # Step 1: Prompt LLM to generate hidden edge cases
        system_prompt = (
            "You are an expert code reviewer and debugging assistant. You must"
            " analyze the user's specific code snippet, find its exact"
            " logical or syntax bugs, and provide a clear explanation under"
            " 'potential_flaw_analysis'. Output strictly valid JSON."
        )

        user_prompt = f"""
                Problem Description:
                {problem_description}

                User's Code:
                {user_code}

                Task:
                1. Generate hidden edge cases and boundary conditions in JSON format.
                2. Analyze the user's code line-by-line. In 'potential_flaw_analysis', explicitly point out what the user wrote wrong, why it fails, and how they should fix it.

                Output JSON Schema:
                {{
                  "edge_cases": [
                    {{
                      "case_id": 1,
                      "description": "Why this edge case matters",
                      "input_data": "exact input string",
                      "expected_output": "expected output string"
                    }}
                  ],
                  "potential_flaw_analysis": "Detailed breakdown of the user's mistakes, syntax errors, or logical bugs."
                }}
                """

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        import json

        ai_response = json.loads(response.choices[0].message.content)
        edge_cases = ai_response.get("edge_cases", [])
        flaw_analysis = ai_response.get("potential_flaw_analysis", "")

        # Step 2: Run user code locally against generated edge cases using subprocess
        test_results = []
        temp_code_path = None

        try:
          with tempfile.NamedTemporaryFile(
              mode="w", suffix=".py", delete=False
          ) as temp_code:
            temp_code.write(user_code)
            temp_code_path = temp_code.name

          for case in edge_cases:
            input_data = case.get("input_data", "")
            expected_output = case.get("expected_output", "").strip()

            try:
              result = subprocess.run(
                  ["python", temp_code_path],
                  input=input_data,
                  text=True,
                  capture_output=True,
                  timeout=3,
              )

              stdout = result.stdout.strip()
              stderr = result.stderr.strip()

              if result.returncode != 0:
                passed = False
                error_message = (
                    stderr or f"Process exited with code {result.returncode}"
                )
              else:
                passed = stdout == expected_output
                error_message = None

              test_results.append({
                  "case_id": case["case_id"],
                  "description": case["description"],
                  "input": input_data,
                  "expected": expected_output,
                  "received": stdout if result.returncode == 0 else None,
                  "error": error_message,
                  "passed": passed,
              })

            except subprocess.TimeoutExpired:
              test_results.append({
                  "case_id": case["case_id"],
                  "description": case["description"],
                  "error": "Time Limit Exceeded (> 3s)",
                  "passed": False,
              })
            except Exception as exec_error:
              test_results.append({
                  "case_id": case["case_id"],
                  "description": case["description"],
                  "error": f"Execution error: {str(exec_error)}",
                  "passed": False,
              })
        finally:
          if temp_code_path and os.path.exists(temp_code_path):
            os.remove(temp_code_path)

        # Step 3: Render Results in Streamlit UI
        st.success("Analysis Complete!")

        st.subheader("🔍 AI Flaw & Logic Analysis")
        st.info(flaw_analysis)

        st.subheader(
            f"🧪 Test Case Execution Results ({len(test_results)} Edge Cases"
            " Tested)"
        )

        for case in test_results:
          passed = case.get("passed", False)
          case_id = case.get("case_id")
          desc = case.get("description")
          status_icon = "✅ PASSED" if passed else "❌ FAILED"

          with st.expander(
              f"Edge Case #{case_id}: {desc}  |  Status: {status_icon}"
          ):
            col1, col2 = st.columns(2)
            with col1:
              st.markdown(f"**Input Data:**\n```text\n{case.get('input')}\n```")
              st.markdown(
                  f"**Expected Output:**\n```text\n{case.get('expected')}\n```"
              )
            with col2:
              received = case.get("received")
              st.markdown(
                  f"**Received Output:**\n```text\n{received if received is not None else 'None'}\n```"
              )
              if case.get("error"):
                st.error(f"Error:\n{case.get('error')}")

      except Exception as e:
        st.error(f"An error occurred during execution: {str(e)}")