# LATHIKHA_25BTRAD083_Python

Python lab exercises, problem-solving assignments, mini projects, and the Hospital Appointment Management System.

## Folder structure

- `25BTRAD083_Experiential Learning Activity/` – Hospital Appointment Management System (Flask + SQLite)
- `25BTRAD083_Lab_Experiments/` – Lab exercises, Parts 1–5
- `25BTRAD083_Problem_Solving/` – Unit 1 assignment and mini projects, Parts 1–3

## Open in Visual Studio Code

1. Extract or clone this repository.
2. Open the `Lathikha_25BTRAD083_Python` folder in Visual Studio Code.
3. Open the required `.py` file.
4. Select a Python interpreter using **Python: Select Interpreter**.
5. Run the file in the integrated terminal. Programs that use `input()` must be run in the terminal, not the Output panel.

## Hospital Appointment Management System

Open the project folder:

`25BTRAD083_Experiential Learning Activity/Hospital_Appointment_Management_System/`

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.venv\Scripts\activate.bat

python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

The SQLite database is generated automatically when the application is imported or started. Do not commit the database file. The demo administrator credentials are documented in the hospital project's README; change the demo password before any public deployment and set a strong `SECRET_KEY` environment variable.

For a deployment using Gunicorn, set `SECRET_KEY` in the hosting provider's environment variables and use the start command documented in the hospital project's README.

## GitHub notes

- Do not upload virtual environments (`venv/` or `.venv/`), Python cache files, local databases, or environment files.
- Install dependencies from `requirements.txt` rather than committing installed packages.
- The attendance and sales mini projects create local JSON data files when records are changed; these are intentionally excluded from Git.

## Testing

The Hospital Appointment Management System includes tests in its `tests/` folder. From that project folder, install requirements and run:

```bash
python -m pytest -q
```
