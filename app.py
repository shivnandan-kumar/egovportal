# app.py - Main Flask Application File
# E-Governance Complaint and Service Management Portal

from flask import Flask, render_template, redirect, url_for, flash, request, session
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
# REGISTER ROUTE
# ----------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        # Get data from the form
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']
        confirm  = request.form['confirm_password']

        # Check if passwords match
        if password != confirm:
            flash('❌ Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        # Save user to database
        try:
            conn   = sqlite3.connect('database.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, 'user')
            ''', (username, email, password))

            conn.commit()
            conn.close()

            flash('✅ Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash('❌ Email already registered. Try a different one.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


# ----------------------------------------
# LOGIN ROUTE
# ----------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # Get data from the form
        email    = request.form['email']
        password = request.form['password']

        # Check user in database
        conn   = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?',
                       (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Save user info in session
            session['user_id']  = user[0]
            session['username'] = user[1]
            session['role']     = user[4]

            flash(f'✅ Welcome back, {user[1]}!', 'success')

            # Redirect based on role
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('❌ Invalid email or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# ----------------------------------------
# LOGOUT ROUTE
# ----------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('✅ You have been logged out.', 'success')
    return redirect(url_for('login'))


# ----------------------------------------
# USER DASHBOARD (placeholder for now)
# ----------------------------------------
@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('❌ Please login first!', 'danger')
        return redirect(url_for('login'))
    return f"Welcome {session['username']}! User Dashboard coming soon."


# ----------------------------------------
# ADMIN DASHBOARD (placeholder for now)
# ----------------------------------------
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))
    return f"Welcome Admin {session['username']}! Admin Dashboard coming soon."


# ----------------------------------------
# RUN APP
# ----------------------------------------
if __name__ == '__main__':
    init_db()   # Setup database FIRST, then start app
    app.run(debug=True)