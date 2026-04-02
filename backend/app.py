from flask import Flask, jsonify
from safe_web_mvp import run_all_tests_live

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify({"status": "ok", "message": "Safe Web backend is running"})

@app.get("/run-tests")
def run_tests():
    data = run_all_tests_live()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
