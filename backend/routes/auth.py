from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/home')
def home():
    return render_template('auth/home.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (name, phone, email, password) VALUES (%s, %s, %s, %s)",
                    (name, phone, email, hashed_password)
                )
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                flash(f'Registration failed: {str(e)}', 'danger')
            finally:
                cursor.close()
                conn.close()
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE email = %s OR phone = %s",
                (identifier, identifier)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['is_admin'] = user['is_admin']
                flash('Login successful!', 'success')
                return redirect(url_for('booking.search'))
            else:
                flash('Invalid credentials', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))