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
