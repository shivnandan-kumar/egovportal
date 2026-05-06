# app.py - Main Flask Application File
# E-Governance Complaint and Service Management Portal

from flask import Flask, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'egovportal_secret_key'

# ----------------------------------------
# DATABASE SETUP FUNCTION
# ----------------------------------------
def init_db():
    """This function creates the database and tables if they don't exist"""

    conn   = sqlite3.connect('database.db')
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
            priority TEXT DEFAULT 'Medium',
            date_submitted TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create STATUS TIMELINE table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            comment TEXT,
            updated_by TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        )
    ''')

    # Create a default ADMIN account with hashed password
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password, role)
        VALUES ('admin', 'admin@egov.com', ?, 'admin')
    ''', (admin_password,))

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
# ABOUT ROUTE
# ----------------------------------------
@app.route('/about')
def about():
    return render_template('about.html')


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

            # Hash the password before saving
            hashed_password = generate_password_hash(password)

            cursor.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, 'user')
            ''', (username, email, hashed_password))

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

        # Find user by email only first
        conn   = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        # Now check if password matches the hash
        if user and not check_password_hash(user[3], password):
            user = None

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
# USER DASHBOARD
# ----------------------------------------
@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('❌ Please login first!', 'danger')
        return redirect(url_for('login'))

    if session['role'] == 'admin':
        flash('⚠️ Admins cannot access the user dashboard!', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Get search and filter values from URL
    search   = request.args.get('search', '')
    status   = request.args.get('status', '')
    priority = request.args.get('priority', '')
    page     = int(request.args.get('page', 1))
    per_page = 5

    # Build query based on filters
    query  = 'SELECT * FROM complaints WHERE user_id = ?'
    params = [session['user_id']]

    if search:
        query += ' AND (title LIKE ? OR category LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    if status:
        query += ' AND status = ?'
        params.append(status)

    if priority:
        query += ' AND priority = ?'
        params.append(priority)

    query += ' ORDER BY id DESC'

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get total count for pagination
    cursor.execute(query, params)
    all_complaints = cursor.fetchall()
    total_count    = len(all_complaints)

    # Apply pagination
    offset     = (page - 1) * per_page
    query     += f' LIMIT {per_page} OFFSET {offset}'
    cursor.execute(query, params)
    complaints = cursor.fetchall()
    conn.close()

    # Count all complaints for stats
    total      = len(all_complaints)
    pending    = sum(1 for c in all_complaints if c[5] == 'Pending')
    inprogress = sum(1 for c in all_complaints if c[5] == 'In Progress')
    resolved   = sum(1 for c in all_complaints if c[5] == 'Resolved')

    # Pagination info
    total_pages = (total_count + per_page - 1) // per_page

    return render_template('dashboard.html',
                           complaints  = complaints,
                           total       = total,
                           pending     = pending,
                           inprogress  = inprogress,
                           resolved    = resolved,
                           search      = search,
                           status      = status,
                           priority    = priority,
                           page        = page,
                           total_pages = total_pages)

# ----------------------------------------
# SUBMIT COMPLAINT ROUTE
# ----------------------------------------
@app.route('/submit-complaint', methods=['GET', 'POST'])
def submit_complaint():
    if 'user_id' not in session:
        flash('❌ Please login first!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':

        # Get data from the form
        title       = request.form['title']
        category    = request.form['category']
        description = request.form['description']
        priority    = request.form['priority']

        # Get current date
        from datetime import datetime
        date_submitted = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Save complaint to database
        conn   = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO complaints (user_id, title, description, category, status, priority, date_submitted)
            VALUES (?, ?, ?, ?, 'Pending', ?, ?)
        ''', (session['user_id'], title, description, category, priority, date_submitted))

        conn.commit()
        conn.close()

        flash('✅ Complaint submitted successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('submit_complaint.html')


# ----------------------------------------
# ADMIN DASHBOARD
# ----------------------------------------
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    # Get search and filter values from URL
    search   = request.args.get('search', '')
    status   = request.args.get('status', '')
    priority = request.args.get('priority', '')
    page     = int(request.args.get('page', 1))
    per_page = 5

    # Build query
    query  = '''SELECT complaints.*, users.username
                FROM complaints
                JOIN users ON complaints.user_id = users.id
                WHERE 1=1'''
    params = []

    if search:
        query += ' AND (complaints.title LIKE ? OR complaints.category LIKE ? OR users.username LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    if status:
        query += ' AND complaints.status = ?'
        params.append(status)

    if priority:
        query += ' AND complaints.priority = ?'
        params.append(priority)

    query += ' ORDER BY complaints.id DESC'

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get all for stats and charts
    cursor.execute(query, params)
    all_complaints = cursor.fetchall()
    total_count    = len(all_complaints)

    # Apply pagination
    offset     = (page - 1) * per_page
    paginated  = query + f' LIMIT {per_page} OFFSET {offset}'
    cursor.execute(paginated, params)
    complaints = cursor.fetchall()

    # Count by status for stats
    total      = total_count
    pending    = sum(1 for c in all_complaints if c[5] == 'Pending')
    inprogress = sum(1 for c in all_complaints if c[5] == 'In Progress')
    resolved   = sum(1 for c in all_complaints if c[5] == 'Resolved')

    # Chart data
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM complaints
        GROUP BY category
        ORDER BY count DESC
    ''')
    category_data = cursor.fetchall()

    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM complaints
        GROUP BY priority
    ''')
    priority_data = cursor.fetchall()

    conn.close()

    # Prepare chart data
    category_labels = [row[0] for row in category_data]
    category_counts = [row[1] for row in category_data]
    priority_labels = [row[0] for row in priority_data]
    priority_counts = [row[1] for row in priority_data]

    # Pagination info
    total_pages = (total_count + per_page - 1) // per_page

    return render_template('admin_dashboard.html',
                           complaints      = complaints,
                           total           = total,
                           pending         = pending,
                           inprogress      = inprogress,
                           resolved        = resolved,
                           category_labels = category_labels,
                           category_counts = category_counts,
                           priority_labels = priority_labels,
                           priority_counts = priority_counts,
                           search          = search,
                           status          = status,
                           priority        = priority,
                           page            = page,
                           total_pages     = total_pages)


# ----------------------------------------
# UPDATE COMPLAINT STATUS ROUTE
# ----------------------------------------
@app.route('/update-status', methods=['POST'])
def update_status():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    # Get data from form
    complaint_id = request.form['complaint_id']
    new_status   = request.form['status']

    # Update status in database
    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE complaints SET status = ? WHERE id = ?',
                   (new_status, complaint_id))

    conn.commit()
    conn.close()

    flash(f'✅ Complaint status updated to "{new_status}"!', 'success')
    return redirect(url_for('admin_dashboard'))

# ----------------------------------------
# 404 ERROR PAGE
# ----------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# ----------------------------------------
# RUN APP
# ----------------------------------------
if __name__ == '__main__':
    init_db()   # Setup database FIRST, then start app
    app.run(debug=True)