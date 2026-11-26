# Smart Exam Scheduler

An AI-powered university examination scheduling system developed using **Python, FastAPI, HTML, CSS, and JavaScript**.

## Overview

Smart Exam Scheduler uses **Constraint Satisfaction Problem (CSP)** algorithms to generate university exam timetables while preventing scheduling conflicts involving students, professors, and examination rooms.

## AI Algorithms

The system implements seven algorithms:

1. Basic Backtracking
2. Minimum Remaining Values (MRV)
3. Forward Checking
4. MRV + Forward Checking
5. MRV + FC + LCV
6. MRV + FC + Degree
7. MRV + FC + Degree + Adaptive LCV

An **Auto** option selects an algorithm based on dataset characteristics.

## Features

- Upload Excel, JSON, or CSV ZIP datasets.
- Generate and validate examination timetables.
- Prevent student, professor, and room conflicts.
- Compare seven AI algorithms.
- Visualize execution times and search statistics.
- Export results to Excel and CSV.
- Use a web dashboard for scheduling.

## Installation

```bash
git clone https://github.com/tavanmohammed/SmartExamScheduler.git
cd SmartExamScheduler
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
python -m uvicorn api:app --reload
```

**Frontend:** http://127.0.0.1:8000/ui/

**API Documentation:** http://127.0.0.1:8000/docs

## Project Goal

Demonstrate how AI search algorithms can automate university examination scheduling and compare their performance across datasets of different sizes and complexities.

**Technologies:** Python · FastAPI · CSP · HTML · CSS · JavaScript

**Project:** Artificial Intelligence — Constraint-Based Scheduling
