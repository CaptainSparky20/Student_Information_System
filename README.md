# Student Information System

---

## About Us

We, the students of CS4D Group, created this Student Information System as our final year project.

## Overview

The **Student Information System (SIS)** is a web application designed to manage academic records and interactions for students, lecturers, and administrators. It simplifies data management, role-based access, and communication within an educational institution.

## Key Features

- **Authentication System:** Secure login for Students, Lecturers, and Admins
- **Role-Based Dashboards:**
  - **Student Dashboard:** View grades, course schedules, and profile info
  - **Lecturer Dashboard:** Manage student grades, attendance, and course materials
  - **Admin Dashboard:** Manage users, courses, and announcements
- **Profile Management:** Update personal details for all user types
- **Course Management:** Enroll in courses, assign lecturers, and view syllabi
- **Responsive Design:** Mobile-friendly UI using Tailwind CSS

## Latest Addition

- Lecturer dashboard with real stats and quick actions

* Filter and export student, lecturer, and attendance lists to CSV
* Bulk and individual attendance marking
* Past attendance lookup by course and date

## Tech Stack

- **Frontend:** HTML, Tailwind CSS, JavaScript
- **Backend:** Django (Python)
- **Database:** SQLite (default, can switch to MariaDB/PostgreSQL for production)
- **Admin Interface:** Django Admin, Django Templates

---

## Quick Start

### 1. Clone the Repository

```
git clone https://github.com/CaptainSparky20/Student_Information_System.git
```

### 2. navigate to working directory

```
cd student-information-system\SIS\
```

### 3. Setup and activate a virtual environement

```
Set-ExecutionPolicy Unrestricted -Scope Process
```

### 4. Activate the script

```
.\venv\Scripts\activate
```

### 5. Run the server

```
python manage.py runserver
```

---

## Recreate the virtual environment

### 1. Navigate to directory

```
cd \SIS\
```

### 2. Create a virtual environment

```
python -m venv venv

```

### 3. Set execution policy in windows

```
Set-ExecutionPolicy Unrestricted -Scope Process
```

### 4. Activate the virtual environment

```
.\venv\Scripts\activate

```

### 5. Install requirement file

```
pip install -r requirements.txt

```

---
