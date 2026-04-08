# app.py - Main Flask Application File
# E-Governance Complaint and Service Management Portal

from flask import Flask, render_template, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'egovportal_secret_key'

# ----------------------------------------
# DATABASE SETUP FUNCTION
# ----------------------------------------
def init_db():
    """This function creates the database and tables if they don't exist"""
    
    conn = sqlite3.connect('database.db')  # Creates database.db file
    cursor = conn.cursor()

    # Create USERS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')

    # Create COMPLAINTS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            date_submitted TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create a default ADMIN account
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password, role)
        VALUES ('admin', 'admin@egov.com', 'admin123', 'admin')
    ''')

    conn.commit()  # Save changes
    conn.close()   # Close connection
    print("✅ Database initialized successfully!")

# ----------------------------------------
# HOME ROUTE
# ----------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

# ----------------------------------------
# RUN APP
# ----------------------------------------
if __name__ == '__main__':
    init_db()   # Setup database FIRST, then start app
    app.run(debug=True)