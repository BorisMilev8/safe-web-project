# 🛡️ Safe Web Project

## Overview

This project evaluates the safety and performance of web browsers (**Safari, Chrome, Firefox**) based on:

- Privacy  
- Personal Safety  
- Sustainability (resource efficiency)  
- System Performance (CPU and memory usage)  

The system runs multiple trials per browser and aggregates results to provide reliable comparisons.

---

## Features (Alpha)

- Runs automated tests across Safari, Chrome, and Firefox  
- Executes **25 trials per browser (75 total runs)**  
- Measures CPU and memory usage  
- Stores results in CSV format  
- Exports results to JSON for dashboard visualization  
- Includes a React-based dashboard for analysis  
- Supports simulation mode for consistent execution  

---

## How to Run

### Run Backend and Frontend

```bash
cd backend
python safe_web_mvp.py

### Run Frontend
cd frontend
npm install
npm run dev

### Open in browser
http://localhost:5173

---
Example Output

Results are saved in:

backend/data/safe_web_results.csv
frontend/src/data/backendResults.json

The dashboard displays:

average CPU usage
average memory usage
total runs
browser comparison
Current Status (Alpha)
~60–70% functionality implemented
Core testing pipeline working
Backend + frontend fully integrated
Supports Safari, Chrome, Firefox
Simulation mode for stable execution
Methodology

The system uses a repeated trial approach:

Each browser is tested 25 times
Results are aggregated to reduce randomness
Averages are used for comparison
Next Steps
Add more search engines (Bing, DuckDuckGo)
Compute advanced metrics (variance, standard deviation)
Add filtering and improved charts
Integrate real-time performance tracking
Deploy as a web application
Author

Boris Milev
SENG 701 Software Engineering Capstone
