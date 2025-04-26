from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'sslg_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit


# Simulated user store (for now, no database)
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['user'] = username
            flash('✅ Logged in successfully!')
            return redirect(url_for('dashboard'))
        flash('❌ Incorrect username or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Form values
        username = request.form['username'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']
        name = request.form['name'].strip()
        age = request.form['age']
        birthday = request.form['birthday']
        education = request.form['education']
        grade = request.form.get('grade', '')
        section = request.form.get('section', '')
        batch = request.form.get('batch', '')
        role = request.form['role']
        email = request.form.get('email', '')

        # Validations
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))

        if os.path.exists('users.json'):
            with open('users.json') as f:
                users = json.load(f)
        else:
            users = {}

        if username in users:
            flash("Username already exists. Choose another.", "error")
            return redirect(url_for('register'))

        # Save user
        users[username] = {
            "password": password,
            "name": name,
            "age": age,
            "birthday": birthday,
            "education": education,
            "grade": grade,
            "section": section,
            "batch": batch,
            "role": role,
            "email": email
        }

        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("🔒 Please log in to access the dashboard.")
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user'])

@app.route('/announcements')
def announcements():
    if 'user' not in session:
        flash("🔒 Please log in first.")
        return redirect(url_for('login'))

    return render_template('announcements.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('👋 You have been logged out.')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        flash('🔒 Please login to upload files.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('⚠ No file part in the request.')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('⚠ No selected file.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f'✅ File "{filename}" uploaded successfully!')
        return redirect(url_for('upload'))

    return render_template('upload.html')

@app.route('/files')
def files():
    if 'user' not in session:
        flash("🔒 Please log in to view uploaded files.")
        return redirect(url_for('login'))

    # List all files from the uploads folder
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('files.html', files=file_list)

@app.route('/suggest', methods=['GET', 'POST'])
def suggest():
    if 'user' not in session:
        flash("🔒 Please login to submit a suggestion.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        suggestion = request.form.get('suggestion')
        if suggestion:
            with open('suggestions.txt', 'a', encoding='utf-8') as f:
                f.write(f"{session['user']}: {suggestion}\n")
            flash('✅ Thank you for your suggestion!')
            return redirect(url_for('suggest'))

    return render_template('suggest.html')

@app.route('/suggestions')
def suggestions():
    if 'user' not in session:
        flash("🔒 Please login to view suggestions.")
        return redirect(url_for('login'))

    # Only allow admin to view suggestions (for example, username == admin)
    if session['user'] != 'admin':
        flash("❌ Access denied.")
        return redirect(url_for('dashboard'))

    # Read all suggestions
    if os.path.exists('suggestions.txt'):
        with open('suggestions.txt', 'r', encoding='utf-8') as f:
            all_suggestions = f.readlines()
    else:
        all_suggestions = []

    return render_template('suggestions.html', suggestions=all_suggestions)

# --- Voting System ---

import json
import os

# Simple JSON storage
CANDIDATES_FILE = 'candidates.json'
VOTES_FILE = 'votes.json'

# Initialize candidates and votes if not exist
if not os.path.exists(CANDIDATES_FILE):
    with open(CANDIDATES_FILE, 'w') as f:
        json.dump({
            "President": ["Candidate A", "Candidate B"],
            "Vice President": ["Candidate C", "Candidate D"],
            "Secretary": ["Candidate E", "Candidate F"]
        }, f)

if not os.path.exists(VOTES_FILE):
    with open(VOTES_FILE, 'w') as f:
        json.dump([], f)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    with open(CANDIDATES_FILE, 'r') as f:
        candidates = json.load(f)

    if request.method == 'POST':
        vote_data = {}
        for position in candidates.keys():
            selected = request.form.get(position)
            if selected:
                vote_data[position] = selected

        with open(VOTES_FILE, 'r+') as f:
            votes = json.load(f)
            votes.append(vote_data)
            f.seek(0)
            json.dump(votes, f)
        
        flash('Vote submitted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('vote.html', candidates=candidates)

@app.route('/admin/votes')
def view_votes():
    with open(VOTES_FILE, 'r') as f:
        votes = json.load(f)
    return render_template('admin_votes.html', votes=votes)

@app.route('/admin/add_candidates', methods=['GET', 'POST'])
def add_candidates():
    with open(CANDIDATES_FILE, 'r+') as f:
        candidates = json.load(f)

        if request.method == 'POST':
            position = request.form['position']
            name = request.form['name']

            if position not in candidates:
                candidates[position] = []
            candidates[position].append(name)

            f.seek(0)
            json.dump(candidates, f)
            f.truncate()

            flash('Candidate added successfully!', 'success')
            return redirect(url_for('add_candidates'))

    return render_template('admin_add_candidates.html', candidates=candidates)




if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)


