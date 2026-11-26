# KanMind – Backend

A Django REST Framework backend for **KanMind**, a Kanban board application similar to Trello/Join. This repository contains the backend API only; the frontend is provided separately by the Developer Akademie and is not part of this repo.

## Tech Stack

- Python 3 / Django
- Django REST Framework (DRF)
- Token Authentication (`rest_framework.authtoken`)
- SQLite (development)
- `django-environ` for configuration via `.env`
- `coverage.py` for test coverage reporting

## Features

- User registration & login with token-based authentication
- Boards with owners and members
- Tasks with status, priority, assignee, reviewer and due dates
- Comments on tasks
- Fine-grained permissions (board owner vs. member vs. task creator vs. comment author)

## Getting Started

### Prerequisites

- Python 3.14.4
- pip

### Installation

**macOS / Linux**

```bash
# Clone the repository
git clone https://github.com/Xargall/KanMind-Backend.git
cd KanMind-Backend

# Create and activate a virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Windows (PowerShell)**

```powershell
# Clone the repository
git clone https://github.com/Xargall/KanMind-Backend.git
cd KanMind-Backend

# Create and activate a virtual environment
python -m venv env
env\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Windows (cmd.exe)**

```bat
:: Clone the repository
git clone https://github.com/Xargall/KanMind-Backend.git
cd KanMind-Backend

:: Create and activate a virtual environment
python -m venv env
env\Scripts\activate.bat

:: Install dependencies
pip install -r requirements.txt
```

> On Windows, if `Activate.ps1` is blocked, run PowerShell as administrator once and execute `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again.

### Environment Variables

Copy the example file and adjust as needed:

```bash
cp .env.example .env
```

`.env` must define at least:

```
SECRET_KEY=your-secret-key
DEBUG=True
```

### Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Run the Development Server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`.

## API Overview

All endpoints are prefixed with `/api/`. Authentication uses a token header:

```
Authorization: Token <your-token>
```

| Area     | Endpoint                                  | Method             |
| -------- | ----------------------------------------- | ------------------ |
| Auth     | `/registration/`                          | POST               |
| Auth     | `/login/`                                 | POST               |
| Auth     | `/email-check/?email=<email>`             | GET                |
| Boards   | `/boards/`                                | GET, POST          |
| Boards   | `/boards/{board_id}/`                     | GET, PATCH, DELETE |
| Tasks    | `/tasks/`                                 | POST               |
| Tasks    | `/tasks/{task_id}/`                       | PATCH, DELETE      |
| Tasks    | `/tasks/assigned-to-me/`                  | GET                |
| Tasks    | `/tasks/reviewing/`                       | GET                |
| Comments | `/tasks/{task_id}/comments/`              | GET, POST          |
| Comments | `/tasks/{task_id}/comments/{comment_id}/` | DELETE             |

## Running Tests

```bash
coverage run manage.py test
coverage report
```

## Project Structure

```
core/              # Project settings, root URL configuration
auth_app/          # User model, registration, login, email-check
boards_app/        # Boards (model, serializers, views, permissions)
tasks_app/         # Tasks and Comments (model, serializers, views, permissions)
```

## Author

Mathias (Xargall) – Developer Akademie Backend Bootcamp
