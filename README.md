# Student Information System

## About Us

We, the students of CS4D Group, created this Student Information System as our final year project.

## Overview

The **Student Information System (SIS)** is a web application designed to manage academic records and interactions for students, lecturers, and administrators. It simplifies data management, role-based access, and communication within an educational institution.

## Key Features

* **Authentication System:** Secure login for Students, Lecturers, and Admins (Email or IC number)  
* **Password Reset:** Email-based password reset for all users  
* **Role-Based Dashboards:**
  * **Student Dashboard:** View courses, attendance, achievements, disciplinary records, and profile information  
  * **Lecturer Dashboard:** Manage attendance (bulk and individual), student grades, class groups, and achievements  
  * **Admin Dashboard:** Manage users, courses, class groups, announcements, and finance  
* **Profile Management:** Update personal details (name, IC, phone, address, department, profile picture)  
* **Parent/Guardian Records:** Link students with parents/guardians and emergency contacts  
* **Course Management:** Departments, courses, subjects, class groups, and enrollments  
* **Attendance Management:** Mark, filter, and export attendance records  
* **Achievements and Disciplinary Records:** Track student progress and actions  
* **Fee Management:** Create student fee plans, generate installments, and track payments  
* **Responsive Design:** Mobile-friendly UI using Tailwind CSS  

## Latest Addition

* Lecturer dashboard with real stats and quick actions  
* Export lists (students, lecturers, attendance) to CSV  
* Bulk and individual attendance marking with filters  
* Fee plan & installment system with auto-generated schedules  

## Tech Stack

* **Frontend:** HTML, Tailwind CSS, JavaScript (Alpine.js)  
* **Backend:** Django (Python 3.13)  
* **Database:** SQLite (default, can switch to MariaDB/PostgreSQL for production)  
* **Authentication:** CustomUser model with roles (Student, Lecturer, Admin)  
* **Admin Interface:** Django Admin, Django Templates  
* **Deployment Ready:** WhiteNoise for static files, environment-based settings, email integration  

---

## Quick Start

### 1. Clone the Repository
```
git clone https://github.com/CaptainSparky20/Student_Information_System.git
```

### 2. Navigate to working directory
```
cd Student_Information_System\SIS\
```

### 3. Create and activate a virtual environment
```
python -m venv venv
```

Windows PowerShell:
```
Set-ExecutionPolicy Unrestricted -Scope Process
.\venv\Scripts\activate
```

Linux/macOS:
```
source venv/bin/activate
```

### 4. Install dependencies
```
pip install -r requirements.txt
```

### 5. Run migrations
```
python manage.py migrate
```

### 6. Run the server
```
python manage.py runserver
```

---

## Recreate the virtual environment

### 1. Navigate to directory
```
cd SIS
```

### 2. Remove existing venv (if broken) and create new one
```
python -m venv venv
```

### 3. Activate the virtual environment
```
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS
```

### 4. Install requirements
```
pip install -r requirements.txt
```
