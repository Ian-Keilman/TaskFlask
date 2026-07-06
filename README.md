# TaskFlask

## Install and Run Locally

From the project folder, create a virtual environment.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the local database on a first run:

```bash
python -m flask --app run init-db
```

Run the app:

```bash
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Existing Local Database

To update an existing local database without resetting its data:

```bash
python -m flask --app run migrate-db
```

To reset the local database:

```bash
python -m flask --app run init-db
```