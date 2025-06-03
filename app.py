from flask import Flask, request, jsonify
import os
from google import genai
from google.genai import types

app = Flask(__name__)

# Read the API key from GOOGLE_API_KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

client = None
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)

@app.route("/ask", methods=["POST"])
def ask_gemini():
    data = request.get_json()
    prompt = data.get("question", "").strip()
    if not prompt:
        return jsonify({"error": "No question provided"}), 400

    if not client:
        return jsonify({"answer": f"[mocked answer] You asked: “{prompt}”"}), 200

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",            # or whatever model you confirmed exists
            contents=[prompt],
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                temperature=0.1
            )
        )
        answer = response.text
    except Exception as e:
        return (
            jsonify({
                "error": "Gemini API request failed",
                "message": str(e)
            }),
            502,
        )

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
