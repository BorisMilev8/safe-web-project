🛡️ Safe Web: Browser Safety & Performance Analyzer

A system for evaluating web browsers using real CPU, memory, and performance metrics during actual website usage.

🚀 Overview

Safe Web compares browsers by measuring:

⚡ CPU Usage
🧠 Memory Usage
⏱️ Page Load Time
🔒 Safety & Privacy Context (report component)

Instead of theoretical comparisons, this project collects real system-level data during browser execution.

🧠 Technologies Used
Python (Backend)
React + Vite (Frontend)
Playwright (Browser Automation)
psutil (System Metrics)
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
Outputs:
CSV (raw data)
JSON (dashboard-ready)
📊 Frontend (React Dashboard)
Interactive UI
Filter by browser
Displays:
Summary statistics
Full test results
Clean, responsive layout

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
  1. Launch browser using Playwright
  2. Detect browser processes using psutil
  3. Track CPU & memory during page load
  4. Aggregate results
  5. Export to JSON
  6. Display in dashboard

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

For hosted/public demos, point the frontend to the backend API:

```bash
VITE_API_BASE_URL+https://safe-web-project-1.onrender.com npm run build

Then in the dashboard, use **Run live test URL** (for example `https://example.com`) to trigger real backend data collection instead of only static JSON.


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
