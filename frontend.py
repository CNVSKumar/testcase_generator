import requests
import streamlit as st

st.set_page_config(
    page_title="AI Code Edge Case & Debug Platform", layout="wide"
)

st.title("💡 AI-Powered Code Edge Case Generator & Debugger")
st.markdown(
    "Submit your problem and code. Our platform generates hidden edge cases,"
    " runs your code against them, and pinpoints where you fail!"
)

# Input Section
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
  else:
    with st.spinner(
        "🤖 AI is crafting edge cases & testing your code in the sandbox..."
    ):
      try:
        # Send request to your running Flask backend
        response = requests.post(
            "http://127.0.0.1:5000/analyze-code",
            json={
                "problem_description": problem_description,
                "user_code": user_code,
            },
            timeout=30,
        )

        if response.status_code == 200:
          data = response.json()
          flaw_analysis = data.get("flaw_analysis", "")
          test_results = data.get("test_results", [])

          st.success("Analysis Complete!")

          # Display Flaw Analysis
          st.subheader("🔍 AI Flaw & Logic Analysis")
          st.info(flaw_analysis)

          # Display Test Results Breakdown
          st.subheader(
              f"🧪 Test Case Execution Results ({len(test_results)} Edge Cases"
              " Tested)"
          )

          for case in test_results:
            passed = case.get("passed", False)
            case_id = case.get("case_id")
            desc = case.get("description")

            status_icon = "✅ PASSED" if passed else "❌ FAILED"
            expander_label = (
                f"Edge Case #{case_id}: {desc}  |  Status: {status_icon}"
            )

            with st.expander(expander_label):
              col1, col2 = st.columns(2)
              with col1:
                st.markdown(
                    f"**Input Data:**\n```text\n{case.get('input')}\n```"
                )
                st.markdown(
                    f"**Expected Output:**\n```text\n{case.get('expected')}\n```"
                )
              with col2:
                received = case.get("received")
                st.markdown(
                    f"**Received Output:**\n```text\n{received if received is not None else 'None'}\n```"
                )
                if case.get("error"):
                  st.error(f"Runtime/Execution Error:\n{case.get('error')}")
        else:
          err_msg = response.json().get("error", "Unknown server error")
          st.error(f"Flask Backend Error: {err_msg}")

      except requests.exceptions.ConnectionError:
        st.error(
            "⚠️ Could not connect to Flask backend! Make sure your `app.py` is"
            " running in your terminal."
        )
      except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")