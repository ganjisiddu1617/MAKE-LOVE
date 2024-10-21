from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import mysql.connector
from config import db_config
import random
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


# OTP Storage
otp_storage = []


@app.route('/')
def index():
    return render_template('login.html')



# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        contact = request.form.get('contact')
        password = request.form.get('password')

        # Database connection and check
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE contact = %s AND password = %s', (contact, password))
        account = cursor.fetchone()
        conn.close()

        if account:
            # Store user details in session
            session['user_id'] = account['id']
            session['name'] = account['name']
            return redirect(url_for('profile'))
        else:
            return redirect(url_for('login'))
    msg = 'Incorrect username/password!'
    return render_template('login.html', msg = msg)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        contact = request.form['contact']
        password = request.form['password']
        profile_img = request.files['profile_img']
        
        # Convert image to binary data
        image_data = profile_img.read()

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Check if the user already exists based on contact
            cursor.execute("SELECT * FROM users WHERE contact = %s", (contact,))
            existing_user = cursor.fetchone()
            if existing_user:
                # If user already exists, show a message and redirect to login
                cursor.close()
                conn.close()
                msg = 'User already exists. Please login!'
                return render_template('login.html', msg = msg)

            # If the user does not exist, insert the new user data
            cursor.execute(
                "INSERT INTO users (name, age, email, contact, password, profile_img) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, age, email, contact, password, image_data)
            )
            conn.commit()
            cursor.close()
            conn.close()
            # Show success message and redirect to login
            msg = ('Account created successfully! Please login.')
            return render_template('login.html', msg = msg)
        
        else:
            # Handle database connection failure
            flash('Database connection failed!', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')


# Profile Route
@app.route('/profile')
def profile():
    # Check if the user is logged in by checking if 'user_id' is in session
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Retrieve user ID from the session

    # Database query to get user details
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT name, email, contact, age, profile_img FROM users WHERE id = %s', (user_id,))
    account = cursor.fetchone()
    conn.close()

    if not account:
        return "User not found", 404

    # Convert profile image to base64 if it exists
    image_base64 = None
    if account['profile_img']:
        image_base64 = base64.b64encode(account['profile_img']).decode('utf-8')

    # Render the profile page with user details
    return render_template('profile.html', account=account, image_base64=image_base64)

@app.route('/about')
def about():
    return render_template('about.html')

# session Logout

@app.route('/logout')
def logout():
    session.clear()
    msg = ''
    return render_template('login.html', msg = msg)



@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        contact = request.form['contact']
        otp = random.randint(100000, 999999)
        otp_storage[contact] = otp

        msg = Message('OTP for Password Reset', sender='your_email@gmail.com', recipients=[contact])
        msg.body = f'Your OTP for password reset is: {otp}'
        mail.send(msg)

        flash('OTP sent to your phone!', 'info')
        return redirect(url_for('verify_otp', contact=contact))
    
    return render_template('forget_password.html')



@app.route('/verify_otp/<contact>', methods=['GET', 'POST'])
def verify_otp(contact):
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if contact in otp_storage and otp_storage[contact] == int(entered_otp):
            del otp_storage[contact]
            return redirect(url_for('reset_password', contact=contact))
        else:
            flash('Invalid OTP!', 'danger')
    
    return render_template('verify_otp.html', contact=contact)



@app.route('/reset_password/<contact>', methods=['GET', 'POST'])
def reset_password(contact):
    if request.method == 'POST':
        new_password = request.form['password']
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password = %s WHERE contact = %s', (new_password, contact))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Password reset successfully!', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html')


if __name__ == '__main__':
    app.run(debug=True)
