# app.py - Main Flask Application File
# E-Governance Complaint and Service Management Portal

from flask import Flask, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'egovportal_secret_key'

# ----------------------------------------
# FILE UPLOAD CONFIGURATION
# ----------------------------------------
UPLOAD_FOLDER      = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1
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

    # Create FEEDBACK table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create a default ADMIN account with hashed password
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password, role, is_active)
        VALUES ('admin', 'admin@egov.com', ?, 'admin', 1)
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
                INSERT INTO users (username, email, password, role, is_active)
                VALUES (?, ?, ?, 'user', 1)
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

        # Check password matches the hash
        if user and not check_password_hash(user[3], password):
            user = None

        # Check if user is blocked
        if user and len(user) > 5 and user[5] == 0:
            flash('❌ Your account has been blocked! Contact admin.', 'danger')
            return redirect(url_for('login'))

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
    offset  = (page - 1) * per_page
    query  += f' LIMIT {per_page} OFFSET {offset}'
    cursor.execute(query, params)
    complaints = cursor.fetchall()

    # Get list of complaint IDs that already have feedback
    cursor.execute('SELECT complaint_id FROM feedback WHERE user_id = ?',
                   (session['user_id'],))
    feedback_given = [row[0] for row in cursor.fetchall()]

    conn.close()

    # Count all complaints for stats
    total      = len(all_complaints)
    pending    = sum(1 for c in all_complaints if c[5] == 'Pending')
    inprogress = sum(1 for c in all_complaints if c[5] == 'In Progress')
    resolved   = sum(1 for c in all_complaints if c[5] == 'Resolved')

    # Pagination info
    total_pages = (total_count + per_page - 1) // per_page

    return render_template('dashboard.html',
                           complaints     = complaints,
                           total          = total,
                           pending        = pending,
                           inprogress     = inprogress,
                           resolved       = resolved,
                           search         = search,
                           status         = status,
                           priority       = priority,
                           page           = page,
                           total_pages    = total_pages,
                           feedback_given = feedback_given)


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

        # Handle file upload
        filename = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                from werkzeug.utils import secure_filename
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save complaint to database
        conn   = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO complaints
            (user_id, title, description, category, status, priority, date_submitted, filename)
            VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?)
        ''', (session['user_id'], title, description,
              category, priority, date_submitted, filename))

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
    offset    = (page - 1) * per_page
    paginated = query + f' LIMIT {per_page} OFFSET {offset}'
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
# EXPORT COMPLAINTS TO CSV
# ----------------------------------------
@app.route('/export-csv')
def export_csv():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    import csv
    import io
    from flask import Response

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT complaints.id, users.username, complaints.title,
               complaints.category, complaints.priority,
               complaints.status, complaints.date_submitted
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        ORDER BY complaints.id DESC
    ''')
    complaints = cursor.fetchall()
    conn.close()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow([
        'ID', 'Citizen Name', 'Title',
        'Category', 'Priority', 'Status', 'Date Submitted'
    ])

    # Write data rows
    for complaint in complaints:
        writer.writerow(complaint)

    output.seek(0)

    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=complaints_report.csv'
        }
    )


# ----------------------------------------
# UPDATE COMPLAINT STATUS ROUTE
# ----------------------------------------
@app.route('/update-status', methods=['POST'])
def update_status():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    from datetime import datetime

    # Get data from form
    complaint_id = request.form['complaint_id']
    new_status   = request.form['status']
    updated_at   = datetime.now().strftime('%Y-%m-%d %H:%M')

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Update complaint status
    cursor.execute('UPDATE complaints SET status = ? WHERE id = ?',
                   (new_status, complaint_id))

    # Save to timeline
    cursor.execute('''
        INSERT INTO timeline (complaint_id, status, comment, updated_by, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (complaint_id, new_status,
          f'Status updated to {new_status}',
          session['username'],
          updated_at))

    conn.commit()
    conn.close()

    flash(f'✅ Status updated to "{new_status}"!', 'success')
    return redirect(url_for('admin_dashboard'))


# ----------------------------------------
# VIEW COMPLAINT TIMELINE
# ----------------------------------------
@app.route('/timeline/<int:complaint_id>')
def view_timeline(complaint_id):
    if 'user_id' not in session:
        flash('❌ Please login first!', 'danger')
        return redirect(url_for('login'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get complaint details
    cursor.execute('''
        SELECT complaints.*, users.username
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        WHERE complaints.id = ?
    ''', (complaint_id,))
    complaint = cursor.fetchone()

    # Get timeline entries
    cursor.execute('''
        SELECT * FROM timeline
        WHERE complaint_id = ?
        ORDER BY id ASC
    ''', (complaint_id,))
    timeline = cursor.fetchall()

    conn.close()

    if not complaint:
        flash('❌ Complaint not found!', 'danger')
        return redirect(url_for('user_dashboard'))

    # Security - users can only view their own complaints
    if session['role'] != 'admin' and complaint[1] != session['user_id']:
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('user_dashboard'))

    return render_template('timeline.html',
                           complaint = complaint,
                           timeline  = timeline)


# ----------------------------------------
# USER MANAGEMENT (ADMIN)
# ----------------------------------------
@app.route('/admin/users')
def manage_users():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT users.*, COUNT(complaints.id) as complaint_count
        FROM users
        LEFT JOIN complaints ON users.id = complaints.user_id
        GROUP BY users.id
        ORDER BY users.id DESC
    ''')
    users = cursor.fetchall()
    conn.close()

    # Count stats
    total_users   = len(users)
    active_users  = sum(1 for u in users if len(u) > 5 and u[5] == 1)
    admin_users   = sum(1 for u in users if u[4] == 'admin')
    blocked_users = sum(1 for u in users if len(u) > 5 and u[5] == 0)

    return render_template('manage_users.html',
                           users         = users,
                           total_users   = total_users,
                           active_users  = active_users,
                           admin_users   = admin_users,
                           blocked_users = blocked_users)


# ----------------------------------------
# TOGGLE USER STATUS (BLOCK/UNBLOCK)
# ----------------------------------------
@app.route('/admin/toggle-user/<int:user_id>')
def toggle_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    # Prevent admin from blocking themselves
    if user_id == session['user_id']:
        flash('❌ You cannot block yourself!', 'danger')
        return redirect(url_for('manage_users'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get current status
    cursor.execute('SELECT is_active, username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        new_status  = 0 if user[0] == 1 else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?',
                       (new_status, user_id))
        conn.commit()

        status_text = 'activated' if new_status == 1 else 'blocked'
        flash(f'✅ User "{user[1]}" has been {status_text}!', 'success')

    conn.close()
    return redirect(url_for('manage_users'))


# ----------------------------------------
# TOGGLE USER ROLE (PROMOTE/DEMOTE)
# ----------------------------------------
@app.route('/admin/toggle-role/<int:user_id>')
def toggle_role(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    # Prevent admin from demoting themselves
    if user_id == session['user_id']:
        flash('❌ You cannot change your own role!', 'danger')
        return redirect(url_for('manage_users'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get current role
    cursor.execute('SELECT role, username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        new_role = 'user' if user[0] == 'admin' else 'admin'
        cursor.execute('UPDATE users SET role = ? WHERE id = ?',
                       (new_role, user_id))
        conn.commit()

        action_text = 'promoted to Admin' if new_role == 'admin' else 'demoted to User'
        flash(f'✅ User "{user[1]}" has been {action_text}!', 'success')

    conn.close()
    return redirect(url_for('manage_users'))


# ----------------------------------------
# SUBMIT FEEDBACK ROUTE
# ----------------------------------------
@app.route('/feedback/<int:complaint_id>', methods=['GET', 'POST'])
def submit_feedback(complaint_id):
    if 'user_id' not in session:
        flash('❌ Please login first!', 'danger')
        return redirect(url_for('login'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get complaint details
    cursor.execute('SELECT * FROM complaints WHERE id = ? AND user_id = ?',
                   (complaint_id, session['user_id']))
    complaint = cursor.fetchone()

    if not complaint:
        flash('❌ Complaint not found!', 'danger')
        conn.close()
        return redirect(url_for('user_dashboard'))

    # Check complaint is resolved
    if complaint[5] != 'Resolved':
        flash('⚠️ You can only give feedback for resolved complaints!', 'danger')
        conn.close()
        return redirect(url_for('user_dashboard'))

    # Check if feedback already submitted
    cursor.execute('SELECT * FROM feedback WHERE complaint_id = ? AND user_id = ?',
                   (complaint_id, session['user_id']))
    existing_feedback = cursor.fetchone()

    if existing_feedback:
        flash('⚠️ You have already submitted feedback for this complaint!', 'danger')
        conn.close()
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        rating  = request.form['rating']
        comment = request.form['comment']

        from datetime import datetime
        submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M')

        cursor.execute('''
            INSERT INTO feedback (complaint_id, user_id, rating, comment, submitted_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (complaint_id, session['user_id'], rating, comment, submitted_at))

        conn.commit()
        conn.close()

        flash('✅ Thank you for your feedback!', 'success')
        return redirect(url_for('user_dashboard'))

    conn.close()
    return render_template('feedback.html', complaint=complaint)


# ----------------------------------------
# VIEW ALL FEEDBACK (ADMIN)
# ----------------------------------------
@app.route('/admin/feedback')
def view_feedback():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('❌ Access denied!', 'danger')
        return redirect(url_for('login'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT feedback.*, users.username, complaints.title
        FROM feedback
        JOIN users ON feedback.user_id = users.id
        JOIN complaints ON feedback.complaint_id = complaints.id
        ORDER BY feedback.id DESC
    ''')
    feedbacks = cursor.fetchall()

    # Calculate average rating
    avg_rating = 0
    if feedbacks:
        avg_rating = sum(f[3] for f in feedbacks) / len(feedbacks)
        avg_rating = round(avg_rating, 1)

    conn.close()

    return render_template('view_feedback.html',
                           feedbacks  = feedbacks,
                           avg_rating = avg_rating,
                           total      = len(feedbacks))


# ----------------------------------------
# USER PROFILE ROUTE
# ----------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('❌ Please login first!', 'danger')
        return redirect(url_for('login'))

    conn   = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        # ---- Update Username ----
        if action == 'update_username':
            new_username = request.form['username']

            cursor.execute('UPDATE users SET username = ? WHERE id = ?',
                           (new_username, session['user_id']))
            conn.commit()

            # Update session
            session['username'] = new_username
            flash('✅ Username updated successfully!', 'success')

        # ---- Change Password ----
        elif action == 'change_password':
            current_password = request.form['current_password']
            new_password     = request.form['new_password']
            confirm_password = request.form['confirm_password']

            # Get current password from database
            cursor.execute('SELECT password FROM users WHERE id = ?',
                           (session['user_id'],))
            user = cursor.fetchone()

            if not check_password_hash(user[0], current_password):
                flash('❌ Current password is incorrect!', 'danger')
            elif new_password != confirm_password:
                flash('❌ New passwords do not match!', 'danger')
            elif len(new_password) < 6:
                flash('❌ Password must be at least 6 characters!', 'danger')
            else:
                hashed = generate_password_hash(new_password)
                cursor.execute('UPDATE users SET password = ? WHERE id = ?',
                               (hashed, session['user_id']))
                conn.commit()
                flash('✅ Password changed successfully!', 'success')

        conn.close()
        return redirect(url_for('profile'))

    # GET request - fetch user data
    cursor.execute('''
        SELECT users.*,
               COUNT(complaints.id) as total_complaints
        FROM users
        LEFT JOIN complaints ON users.id = complaints.user_id
        WHERE users.id = ?
        GROUP BY users.id
    ''', (session['user_id'],))
    user = cursor.fetchone()

    # Get complaint stats
    cursor.execute('SELECT COUNT(*) FROM complaints WHERE user_id = ? AND status = ?',
                   (session['user_id'], 'Pending'))
    pending = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM complaints WHERE user_id = ? AND status = ?',
                   (session['user_id'], 'Resolved'))
    resolved = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM feedback WHERE user_id = ?',
                   (session['user_id'],))
    feedbacks = cursor.fetchone()[0]

    conn.close()

    return render_template('profile.html',
                           user      = user,
                           pending   = pending,
                           resolved  = resolved,
                           feedbacks = feedbacks)


# ----------------------------------------
# SERVE UPLOADED FILES
# ----------------------------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


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