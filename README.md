Smart Exam Scheduler
Smart Exam Scheduler is a Python university project that generates exam timetables using four Constraint Satisfaction Problem (CSP) solver configurations:
1. Basic Backtracking
2. Backtracking with Minimum Remaining Values (MRV)
3. Backtracking with Forward Checking
4. Backtracking with MRV and Forward Checking
The algorithms are implemented in the project's Python files without an external CSP-solving library.
Getting started
1. Install Python 3.10 or newer and VS Code.
2. Accept the GitHub collaborator invitation if the repository is private.
3. Open a terminal and download the project:
git clone https://github.com/tavanmohammed/SmartExamScheduler.git
cd SmartExamScheduler
4. Check Python:
python --version
No additional Python packages are required for the current command-line version.
Option 1: main.py — Predefined university data and experiments
Run:
python main.py
What it does
main.py uses the university dataset already defined in the code. Teammates do not need to type exam information. It:
- Loads the predefined exams, classrooms, and available times.
- Generates synthetic student enrollments and calculates exam conflicts.
- Runs the CSP algorithms and generates schedules.
- Displays a timetable and checks whether schedules satisfy the implemented constraints.
- Prints algorithm performance results.
- Runs preliminary time-slot availability experiments in the current version.
Expected output sections
SMART EXAM SCHEDULER
Total Exams: 8
Total Classrooms: 4
Total Time Slots: 8

EXAM CONFLICTS
...

GENERATED EXAM SCHEDULE
...

AI ALGORITHM COMPARISON
...

SCHEDULE VALIDATION
...

EXPERIMENT 1: TIME SLOT AVAILABILITY
...
The exact performance times depend on the computer and the project version.
When should you use main.py?
Use it for testing, controlled experiments, comparing algorithms, and collecting results for the report. To change the predefined exam counts, rooms, or slots, edit the corresponding data in main.py and run it again.
Option 2: interactive.py — Enter your own exams and generate a schedule
Run:
python interactive.py
What it does
interactive.py asks for input in the terminal:
1. Number of exams.
2. Course code, course name, and number of students for each exam.
3. Available classroom names, physical capacities, and usable examination capacities.
4. Available examination days and time slots.
The program then runs all four CSP configurations on that input, prints their performance comparison, and displays a validated timetable if one is found. It can optionally show the timetable produced by each algorithm.
Example input
Exams
Course code	Course name	Students
SOFE302	Algorithms	70
SOFE301	Database Systems	60
ELEE301	Circuit Analysis	80


Classrooms
Room	Physical capacity	Usable exam capacity
ROOM_A	100	70
ROOM_B	150	100


Exam days: Monday, Tuesday
Times each day: 9:00 AM, 1:00 PM

When prompted for the number of exams, enter 3. Then enter each course, room, day, and time in the order requested.
Expected output
RUNNING AI ALGORITHMS
Running: Basic Backtracking
Running: MRV
Running: Forward Checking
Running: MRV + Forward Checking

AI PERFORMANCE COMPARISON
Algorithm                 Time (ms)  Attempts  Backtracks  Valid
...

FINAL EXAM TIMETABLE
Course        Day         Time       Classroom
...

SCHEDULE STATUS: SUCCESS
VALIDATION: PASSED
The exact assignments depend on the algorithm and input. If no valid schedule is possible, the program reports that no valid timetable was found.
When should you use interactive.py?
Use it for the live professor demonstration or whenever you want to test a new scheduling problem without editing Python data directly.

Important: User-entered data is currently kept in memory and is not saved automatically after the program exits. In the simplified interactive version, courses are assumed to have different students. It does not detect actual shared student enrollments; the predefined main.py dataset has separate enrollment-conflict logic.
Difference between the two programs
	main.py	interactive.py
Exam data	Already defined in Python	Entered by user in terminal
Purpose	Experiments and testing	Live demo and custom scheduling
Runs four algorithms	Yes	Yes
Displays schedule	Yes	Yes
Performance comparison	Yes	Yes
Student enrollment conflicts	Synthetic enrollment dataset	Currently assumes no cross-course students
Automatically saves entered data	Not applicable	No


Understanding the results
- Execution time: How long the algorithm took to search, in seconds or milliseconds.
- Assignments attempted: Candidate assignments counted by that implementation.
- Backtracks: Assignments undone after a failed search branch.
- Solution found: Whether the algorithm returned a complete schedule.
- Valid: Whether the separate validator accepts the returned schedule.
Experimental caution: Assignment-attempt counts are not yet fully standardized across the four implementations, and very short execution times vary from run to run. Use repeated controlled experiments and standardized counters before drawing final performance conclusions.
Troubleshooting
python is not recognized: Install Python, or try py main.py / py interactive.py on Windows.

ModuleNotFoundError: Check that you opened the project folder and the solver files (backtracking.py, mrv.py, forward_checking.py, mrv_forward_checking.py) are all in it.

No valid schedule found: Try more time slots or larger rooms. An infeasible instance is a legitimate result.

Invalid schedule: Check the capacity rules in all four solver files; each should use exam_capacity when provided. Report the error to the team rather than using that result.
