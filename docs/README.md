# Urban Spark: Restaurant Franchise Reservation & Management System

**Course:** EXSM 3951 Python Project  
**Team:** Ashray Sikka, Ajay Paterson, Michael Hubel  
**Deadline:** May 25, 2026

---

## What Is This Project?

Urban Spark is a web application for a restaurant franchise. It lets customers browse the menu, make reservations, and place orders online. It also gives staff members: managers, servers, kitchen staff, delivery drivers, and owner, their own dashboards to manage day-to-day operations.

---

## What You Need Before You Start

You need to install a few things on your computer before the app will run. Don't worry if you haven't done this before, just follow each step in order.

### 1. Install Python

Python is the programming language this app is built with.

- Go to https://www.python.org/downloads/
- Download Python **3.12 or higher**
- Run the installer
- **Important:** During installation, check the box that says **"Add Python to PATH"** before clicking Install

To confirm Python installed correctly, open your Terminal (Mac) or Command Prompt (Windows) and type:
`python --version`
You should see something like `Python 3.12.x`

---

### 2. Install Git

Git is the tool that lets you download the project from GitHub.

- Go to https://git-scm.com/downloads
- Download and install for your operating system
- Leave all settings as default during installation

To confirm Git installed correctly, type:
`git --version`

---

## How to Set Up the Project

Follow these steps exactly, in order.

### Step 1: Download the project

Open your Terminal or Command Prompt and run:

```bash
git clone https://github.com/Web-Development-UAlberta/exsm-3943-3951-sp1-c-python-project-restaurant-scenario-python-project.git
```

This downloads the project to your computer. Then move into the project folder:

```bash
cd exsm-3943-3951-sp1-c-python-project-restaurant-scenario-python-project
```

---

### Step 2: Install project dependencies

The project uses several Python packages. Install them all at once by running:

```bash
pip install -r requirements.txt
```

This reads the `requirements.txt` file and installs everything the project needs Django, pytest, Pillow, and more. It may take a minute.

---

### Step 3: Move into the Django project folder

```bash
cd Python_Project
```

All the following commands need to be run from inside this folder.

---

### Step 4: Set up the database

This creates the database file and all the tables the app needs. Run:

```bash
python manage.py migrate
```

You should see a list of migrations being applied. This is normal.

---

### Step 5: Create an admin account

This creates a superuser account so you can log into the Django admin panel and add staff invite records.

```bash
python manage.py createsuperuser
```

You will be asked to enter a username, email, and password. Remember these as you will need them to log in.

---

### Step 6: Start the app

```bash
python manage.py runserver
```

You should see:
Starting development server at http://127.0.0.1:8000/

Open your browser and go to **http://127.0.0.1:8000/** and the app will be running.

To stop the server press `Ctrl + C` in your terminal.

---

## How to Run the Tests

To run all tests and see if everything is working correctly:

```bash
pytest
```

You should see all tests passing with a green summary at the end. If anything is red, something needs to be fixed before merging.

To run a specific test file:

```bash
pytest restaurant/tests/test_models.py
pytest restaurant/tests/test_forms.py
pytest restaurant/tests/test_staff.py
```

---

## How to Log In as Staff

Staff accounts cannot be created through the normal signup page. A manager or owner must first add the staff member's email address through the admin panel.

**Step 1**: Log into the Django admin panel at:
http://127.0.0.1:8000/admin/
Use the superuser account you created in Step 5.

**Step 2**: Find **Staff Invites** and click **Add Staff Invite**

**Step 3**: Enter the staff member's email address and select their role, then save

**Step 4**: The staff member can now go to:
http://127.0.0.1:8000/restaurant/staff_signup/
And sign up using the email address that was added

---

## User Roles

| Role | What They Can Do |
|---|---|
| Customer | Browse menu, make reservations, place orders, manage their profile |
| Manager | Full access to their location's inventory, orders, reservations, menu, staff |
| Server/Host | View floor plan, update table status, place orders on behalf of customers |
| Kitchen Staff | View and update order statuses on the kitchen dashboard |
| Delivery Driver | View their assigned delivery orders |
| Owner | Full access across all locations |

---

## Project Structure
    
    Project-Repo/
    ├── requirements.txt          # All Python packages needed
    ├── pytest.ini                # Pytest configuration
    ├── docs/                     # Project documentation
    │   └── README.md             # This file
    └── Python_Project/
    ├── manage.py             # Django management tool
    ├── Python_Project/       # Django settings and URL config
    │   ├── settings.py
    │   └── urls.py
    └── restaurant/           # Main app
    ├── models.py         # Database tables
    ├── views.py          # Page logic
    ├── forms.py          # Form definitions
    ├── urls.py           # URL routing
    ├── templates/        # HTML pages
    ├── static/           # CSS and images
    ├── migrations/       # Database migration history
    └── tests/            # All test files
    ├── test_models.py
    ├── test_forms.py
    └── test_staff.py

---

## Automatic Testing on GitHub

Every time code is pushed to the main branch or a pull request is opened, GitHub automatically runs the full test suite. You can see the results on the pull request page, a green checkmark means all tests passed, a red X means something failed and the code cannot be merged until it is fixed.