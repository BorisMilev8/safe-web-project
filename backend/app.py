from flask import Flask, jsonify, request
from flask_cors import CORS
from safe_web_mvp import run_all_tests_live
import traceback

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Safe Web backend is running"
    })

@app.get("/run-tests")
def run_tests():
    try:
        raw_urls = request.args.get("urls", "")
         urls = [url for url in (piece.strip() for piece in raw_urls.split(",")) if url]
        data = run_all_tests_live(urls=urls)
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
