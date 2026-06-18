# 🏛️ E-Governance Complaint & Service Management Portal

A full-stack web application that enables citizens to submit, track, and manage public complaints digitally while providing administrators with powerful tools for complaint resolution, user management, analytics, and feedback monitoring.

## 🚀 Production Deployment

- Hosting: Render
- Database: Supabase PostgreSQL
- Backend: Flask (Python)
- Status: Live & Running

## 🚀 Live Project

**Live Demo:** https://egovportal-6lpv.onrender.com

---

## ✨ Key Features

### 👤 Citizen Features

* User Registration & Login
* Secure Password Authentication
* Submit Complaints with Supporting Documents
* Unique Complaint Reference Number Generation
* Real-Time Complaint Status Tracking
* Complaint History Timeline
* Profile Management
* Feedback & Rating System

### 🛡️ Admin Features

* Admin Dashboard
* Complaint Management
* Status Updates (Pending → In Progress → Resolved)
* Search & Filter Complaints
* User Management
* User Role Management
* Analytics Dashboard
* CSV/Excel Export
* Feedback Monitoring

---

## 🛠️ Tech Stack

| Category        | Technology                |
| --------------- | ------------------------- |
| Backend         | Python, Flask             |
| Database        | PostgreSQL (Supabase)     |
| Frontend        | HTML, CSS, JavaScript     |
| Charts          | Chart.js                  |
| Security        | Werkzeug Password Hashing |
| Database Driver | Psycopg2                  |
| Deployment      | Render                    |
| Version Control | Git, GitHub               |

---

## 🗄️ Database Architecture

The application uses a cloud-hosted PostgreSQL database on Supabase.

### Main Tables

| Table      | Purpose                           |
| ---------- | --------------------------------- |
| users      | Stores citizen and admin accounts |
| complaints | Stores complaint information      |
| timeline   | Tracks complaint status history   |
| feedback   | Stores ratings and feedback       |

---

## 🔐 Security Features

* Password Hashing using Werkzeug
* Role-Based Access Control
* Environment Variable Based Configuration
* Cloud Database Security
* Session Management
* Secure Authentication System

---

## ☁️ Recent Production Upgrade

### Migration: SQLite → PostgreSQL (Supabase)

The project was originally developed using SQLite and later upgraded to a production-ready cloud database architecture.

### Improvements

✅ Migrated from SQLite to PostgreSQL

✅ Integrated Supabase Cloud Database

✅ Added Psycopg2 PostgreSQL Driver

✅ Configured Environment Variable Based Database Connection

✅ Connected Application to Supabase Session Pooler

✅ Successfully Deployed on Render

### Current Architecture

Python Flask
↓
Render Cloud Hosting
↓
Supabase PostgreSQL Database

This upgrade significantly improves scalability, reliability, and real-world deployment readiness.

---

## ⚙️ Environment Variables

Required environment variables:

```env
DATABASE_URL=your_supabase_postgresql_connection_string
```

---

## 📊 Project Workflow

Citizen Registers
↓
Citizen Logs In
↓
Complaint Submitted
↓
Reference Number Generated
↓
Admin Reviews Complaint
↓
Status Updated
↓
Citizen Tracks Progress
↓
Complaint Resolved
↓
Feedback Submitted

---

## 📷 Screenshots

### Login Page

(Add Screenshot)

### Citizen Dashboard

(Add Screenshot)

### Complaint Submission Page

(Add Screenshot)

### Admin Dashboard

(Add Screenshot)

### Analytics Dashboard

(Add Screenshot)

---

## 🔮 Future Improvements

* Email Notifications
* SMS Alerts
* Multi-Language Support
* AI-Based Complaint Categorization
* Mobile Application
* Government Department Integration
* Real-Time Notifications

---

## 👨‍💻 Author

**Shivnandan Kumar**

BCA Graduate (2026)

Python Flask Developer

GitHub: https://github.com/shivnandan-kumar

LinkedIn: https://linkedin.com/in/shivnandan-kumar-27804b3a9

---

## ⭐ Project Highlights

* Production-Ready Deployment
* Cloud PostgreSQL Database
* Role-Based Authentication
* Complaint Lifecycle Tracking
* Analytics Dashboard
* Secure Password Management
* Responsive User Interface
* Real-World Government Use Case

---

## 📄 License

This project is developed for educational, learning, and portfolio purposes.
