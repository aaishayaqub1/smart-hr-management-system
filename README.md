# Smart HR Management System

A web-based **Smart HR Management System** designed to simplify employee and recruitment management through a centralized platform. The system provides role-based access, employee information management, and database-driven HR operations.

## 🚀 Features

* 🔐 **Role-Based Login System**

  * Separate access based on user roles
  * Secure session-based authentication

* 👥 **Employee Management**

  * Store and manage employee information
  * Access employee records through a centralized system

* 📄 **Recruitment & Resume Management**

  * Maintain student/candidate profiles
  * Support resume-based candidate shortlisting
  * Searchable candidate information

* 🗄️ **Oracle Database Integration**

  * Persistent storage of users and HR-related information
  * Database-driven operations using Oracle Database

* 📊 **HR Dashboard**

  * Organized interface for accessing HR-related operations
  * Different functionality based on the logged-in user's role

* 📑 **Report Generation**

  * Generate structured reports from stored information

## 🛠️ Tech Stack

**Frontend**

* HTML
* CSS
* JavaScript

**Backend**

* Python
* Flask

**Database**

* Oracle Database / Oracle XE
* Python `oracledb`

**Other Tools & Libraries**

* ReportLab
* python-dotenv
* VS Code
* Git & GitHub

## 🏗️ System Architecture

The project follows a basic web application architecture:

```text
User
  ↓
Frontend (HTML/CSS/JavaScript)
  ↓
Flask Backend
  ↓
Business Logic
  ↓
Oracle Database
  ↓
Reports / HR Information
```

## 📂 Project Structure

```text
smart-hr-management-system/
│
├── app.py
├── requirements.txt
├── .env
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
└── README.md
```

> The exact file structure may vary depending on the current version of the project.

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/aaishayaqub1/smart-hr-management-system.git
```

```bash
cd smart-hr-management-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file and add the required database configuration, for example:

```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_DSN=localhost/XE
```

Do **not** upload real passwords, credentials, or other sensitive information to GitHub.

### 5. Configure Oracle Database

Make sure Oracle Database/Oracle XE is installed and running.

Update the database configuration in the project according to your local Oracle setup.

If Oracle Instant Client is required by the environment, install and configure the appropriate version on your system.

### 6. Run the Application

```bash
python app.py
```

Open the local URL displayed by Flask in your browser.

## 🔑 Role-Based Access

The system supports different user roles, allowing functionality to be controlled according to the type of user accessing the application.

This helps provide a structured HR workflow while preventing users from accessing functionality outside their assigned role.

## 🎯 Project Objective

The main objective of this project is to develop a centralized HR management platform that combines:

* Employee information management
* Candidate/resume management
* Database-driven searching
* Role-based access control
* Report generation

The project demonstrates how a Python Flask application can interact with an Oracle database to build a practical enterprise-style management system.

## 🧠 Key Learning Outcomes

Through this project, I gained practical experience with:

* Python Flask web development
* REST-style backend routing
* Oracle database connectivity
* SQL and database operations
* Role-based authentication
* Session management
* CRUD-based application design
* Report generation
* Environment variable management
* Git and GitHub version control

## 👩‍💻 My Contribution

I worked on the development and implementation of the Smart HR Management System, including backend functionality, database integration, and project implementation.

The project also provided practical experience in connecting a Flask application with an Oracle database and building database-driven HR functionality.

## 🔮 Future Improvements

Possible future enhancements include:

* AI-based resume screening and ranking
* Automated candidate recommendations
* Advanced HR analytics dashboard
* Email notifications for recruitment workflows
* Resume parsing and skill extraction
* Cloud deployment
* Improved authentication and security

## 📌 Project Status

**Completed Academic Project**

The project was developed as an academic/educational project to demonstrate practical implementation of a database-driven HR management system.

---

### ⭐ Technologies Used

`Python` `Flask` `Oracle` `SQL` `HTML` `CSS` `JavaScript` `ReportLab` `Git` `GitHub`
