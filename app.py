from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['alumni_db']

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.name = user_data['name']

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except:
        pass
    return None

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = db.users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(user)
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if db.users.find_one({'email': email}):
            flash('Email already exists')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password)
        user_data = {
            'email': email,
            'password': hashed_password,
            'name': name,
            'created_at': datetime.now()
        }
        db.users.insert_one(user_data)
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    questions = list(db.questions.find().sort('created_at', -1))
    posts = list(db.posts.find().sort('created_at', -1))
    
    # Convert ObjectId to string and add author information
    for question in questions:
        question['_id'] = str(question['_id'])
        # Get author information
        author = db.users.find_one({'_id': question['user_id']})
        question['author'] = {
            'full_name': author['name'] if author else 'Unknown User',
            'email': author['email'] if author else ''
        }
        # Process answers
        for answer in question.get('answers', []):
            if 'user_id' in answer:
                answer['user_id'] = str(answer['user_id'])
                # Get answer author information
                answer_author = db.users.find_one({'_id': answer['user_id']})
                answer['author'] = {
                    'full_name': answer_author['name'] if answer_author else 'Unknown User',
                    'email': answer_author['email'] if answer_author else ''
                }
    
    for post in posts:
        post['_id'] = str(post['_id'])
        post['user_id'] = str(post['user_id'])
        # Get post author information
        author = db.users.find_one({'_id': ObjectId(post['user_id'])})
        post['author'] = {
            'full_name': author['name'] if author else 'Unknown User',
            'email': author['email'] if author else ''
        }
    
    return render_template('dashboard.html', questions=questions, posts=posts)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        updates = {
            'graduation_year': request.form.get('graduation_year'),
            'field_of_study': request.form.get('field_of_study'),
            'industry': request.form.get('industry'),
            'location': request.form.get('location'),
            'bio': request.form.get('bio')
        }
        db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': updates}
        )
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    user_data = db.users.find_one({'_id': ObjectId(current_user.id)})
    return render_template('profile.html', user=user_data)

@app.route('/ask_question', methods=['POST'])
@login_required
def ask_question():
    title = request.form.get('title')
    content = request.form.get('content')
    if title and content:
        question_data = {
            'user_id': ObjectId(current_user.id),
            'title': title,
            'content': content,
            'created_at': datetime.now(),
            'answers': []
        }
        db.questions.insert_one(question_data)
        flash('Question posted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/answer_question/<question_id>', methods=['POST'])
@login_required
def answer_question(question_id):
    content = request.form.get('content')
    if content:
        answer_data = {
            'user_id': ObjectId(current_user.id),
            'content': content,
            'created_at': datetime.now()
        }
        db.questions.update_one(
            {'_id': ObjectId(question_id)},
            {'$push': {'answers': answer_data}}
        )
        flash('Answer posted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title')
    content = request.form.get('content')
    if title and content:
        post_data = {
            'user_id': ObjectId(current_user.id),
            'title': title,
            'content': content,
            'created_at': datetime.now(),
            'interested_users': []
        }
        db.posts.insert_one(post_data)
        flash('Post created successfully!')
    return redirect(url_for('dashboard'))

@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():
    if request.method == 'POST':
        amount = request.form.get('amount')
        message = request.form.get('message', '')
        donation_data = {
            'user_id': ObjectId(current_user.id),
            'amount': float(amount),
            'message': message,
            'created_at': datetime.now()
        }
        db.donations.insert_one(donation_data)
        flash(f'Thank you for your donation of ₹{amount}!')
        return redirect(url_for('dashboard'))
    return render_template('donate.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True) 