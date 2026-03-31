🛡️ Safe Web: Browser Safety & Performance Analyzer

A system for evaluating modern web browsers based on performance, resource usage, and safety considerations across real-world web workloads.

🚀 Overview

Safe Web analyzes how different browsers behave when loading websites by measuring:

⚡ CPU Usage
🧠 Memory Usage
⏱️ Page Load Time
🔒 Browser Safety & Privacy Context (Report Component)

The system runs automated trials across multiple browsers and visualizes results in an interactive dashboard.

🧠 Key Idea

Instead of relying on theoretical comparisons, this project collects real system-level metrics using:

psutil for CPU & memory tracking
Playwright for automated browser testing
🧩 Features
🔬 Backend (Python)
Runs automated tests on:
Google Chrome
Firefox
Executes multiple trials per browser
Tracks full browser process tree
Measures:
Average CPU usage
Peak CPU usage
Average memory usage
Peak memory usage
Stores results in:
CSV (raw data)
JSON (dashboard-ready)
📊 Frontend (React + Vite)
Interactive dashboard
Filter results by browser
Displays:
Summary statistics
Full test logs
Clean, responsive UI
🏗️ Project Structure
safe-web-project/
│
├── backend/
│   ├── safe_web_mvp.py
│   └── data/
│       └── safe_web_results.csv
│
├── frontend/
│   ├── public/
│   │   └── safe_web_results_real.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── components/
│   │       └── BrowserMetricsDashboard.jsx
│   └── package.json
│
└── README.md
⚙️ How It Works
Launch browser using Playwright
Detect browser process(es) via psutil
Track CPU + memory during page load
Aggregate metrics
Export results to JSON
Render results in dashboard
▶️ How to Run
🔹 1. Run Backend
cd backend
python safe_web_mvp.py

This will:

Run tests
Generate:
safe_web_results.csv
safe_web_results_real.json
🔹 2. Run Frontend
cd frontend
npm install
npm run dev

Open in browser:

http://localhost:5173
📈 Example Output
Browser	Avg CPU	Peak CPU	Avg Memory	Peak Memory
Chrome	18.5%	82.3%	520 MB	780 MB
Firefox	15.2%	65.1%	480 MB	690 MB
🔍 What Makes This Project Strong
✅ Uses real system metrics (not simulated)
✅ Tracks entire browser process tree
✅ Measures live behavior during page load
✅ Combines software engineering + systems analysis
✅ Includes both data collection + visualization
⚠️ Limitations
CPU is measured per-core (100% = 1 core)
Results vary by hardware
Headless mode may reduce CPU usage
Short sampling window focuses on page load, not long-term usage
🧪 Future Improvements
Add more browsers (Edge, Brave, Safari)
Include energy consumption estimation
Add charts (graphs instead of tables)
Increase trial count for statistical accuracy
Add privacy scoring model
👨‍💻 Authors
Boris Milev
UMBC SENG 701 Capstone
🎯 Project Goal
To provide a data-driven comparison of browser performance and behavior, helping users and researchers better understand the real-world impact of web browsing.
