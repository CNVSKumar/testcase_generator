import os
import subprocess
import tempfile
from flask import Flask, jsonify, request
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client with the environment variable
client = OpenAI(api_key=os.environ.get("GROQ_API_KEY"),base_url="https://api.groq.com/openai/v1")


@app.route("/analyze-code", methods=["POST"])
def analyze_code():
  data = request.json
  if not data:
    return jsonify({"error": "No JSON payload received"}), 400

  problem_description = data.get("problem_description")
  user_code = data.get("user_code")
  existing_test_cases = data.get("existing_test_cases", "None")

  if not problem_description or not user_code:
    return (
        jsonify({"error": "Missing 'problem_description' or 'user_code'"}),
        400,
    )

  # Step 1: Prompt LLM to generate hidden edge cases in strict JSON format
  system_prompt = (
      "You are an expert code reviewer and debugging assistant. "
      "You must analyze the user's specific code snippet, find its exact logical or syntax bugs, "
      "and provide a clear explanation under 'potential_flaw_analysis'. Output strictly valid JSON."
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

  try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
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

  except Exception as e:
    return (
        jsonify({"error": f"Failed to generate edge cases from LLM: {str(e)}"}),
        500,
    )

  # Step 2: Run user code locally against every generated edge case using a safe subprocess
  test_results = []
  temp_code_path = None

  try:
    # Create a temporary file to hold the user's code safely
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as temp_code:
      temp_code.write(user_code)
      temp_code_path = temp_code.name

    for case in edge_cases:
      input_data = case.get("input_data", "")
      expected_output = case.get("expected_output", "").strip()

      try:
        # Execute the user code locally with standard input and a 3-second timeout
        result = subprocess.run(
            ["python", temp_code_path],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=3,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # Determine if it passed (comparing stdout to expected output)
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
            "status": "Accepted" if passed else "Wrong Answer / Error",
            "passed": passed,
        })

      except subprocess.TimeoutExpired:
        test_results.append({
            "case_id": case["case_id"],
            "description": case["description"],
            "error": "Time Limit Exceeded (Execution took > 3 seconds)",
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
    # Clean up the temporary file safely
    if temp_code_path and os.path.exists(temp_code_path):
      os.remove(temp_code_path)

  # Step 3: Return consolidated findings back to the Frontend
  return jsonify({
      "flaw_analysis": flaw_analysis,
      "total_edge_cases_tested": len(edge_cases),
      "test_results": test_results,
  })


if __name__ == "__main__":
  app.run(debug=True, port=5000)