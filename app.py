
from flask import Flask, render_template, request, redirect
import sqlite3
import threading
import subprocess

app = Flask(__name__)

# Home route - Login Page
@app.route('/')
def home():
    return render_template('login.html')

# Signup route - for new user registration
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Save the user to the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            return "Username already exists, please choose a different username."

        # Insert new user
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')  # Redirect to login page after successful signup

    return render_template('signup.html')

# Login route - for existing users
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists in the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Successful login, redirect to dashboard
            return redirect('/dashboard')
        else:
            return "Invalid credentials, please try again."

    return render_template('login.html')

# Dashboard route (after successful login)
@app.route('/dashboard')
def dashboard():
    # Start the gcs.py script in a separate thread so it doesn't block the web server
    thread = threading.Thread(target=run_gcs_script)
    thread.start()
    
    # Render a custom Spiderman-themed dashboard
    return render_template('dashboard.html')

# Function to run the gcs.py script
def run_gcs_script():
    try:
        # Ensure that the gcs.py script is in the same directory as this Flask app or provide the full path
        subprocess.run(["python", "gcs.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running gcs.py: {e}")

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create the users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run the app
if __name__ == '__main__':
    init_db()  # Initialize database when the app starts
    app.run(debug=True)
