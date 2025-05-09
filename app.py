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
    # Keep your existing code for upcoming_events
    upcoming_events = list(db.events.find({'date': {'$gte': datetime.now()}}).sort('date', 1).limit(3))
    for event in upcoming_events:
        event['_id'] = str(event['_id'])
        event['user_id'] = str(event['user_id'])
        author = db.users.find_one({'_id': ObjectId(event['user_id'])})
        event['author'] = {
            'full_name': author['name'] if author else 'Unknown User',
            'email': author['email'] if author else ''
        }

    # Get success stories from all users
    success_stories = []
    users_with_stories = db.users.find({'success_stories': {'$exists': True, '$ne': []}})
    for user in users_with_stories:
        for story in user.get('success_stories', []):
            story['user_name'] = user['name']
            success_stories.append(story)

    # Sort success stories by creation date, most recent first
    success_stories.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)

    return render_template('home.html', upcoming_events=upcoming_events, success_stories=success_stories)


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
            'created_at': datetime.now(),
             'comments': []
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
    
    # Get upcoming events (next 3)
    upcoming_events = list(db.events.find({'date': {'$gte': datetime.now()}}).sort('date', 1).limit(3))
    for event in upcoming_events:
        event['_id'] = str(event['_id'])
        event['user_id'] = str(event['user_id'])
        author = db.users.find_one({'_id': ObjectId(event['user_id'])})
        event['author'] = {
            'full_name': author['name'] if author else 'Unknown User',
            'email': author['email'] if author else ''
        }
    
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

        if 'comments' in post:
                    for comment in post['comments']:
                        comment['user_id'] = str(comment['user_id'])
                        # Get comment author information
                        comment_author = db.users.find_one({'_id': ObjectId(comment['user_id'])})
                        comment['author'] = {
                            'full_name': comment_author['name'] if comment_author else 'Unknown User',
                            'email': comment_author['email'] if comment_author else ''
                        }
    
    return render_template('dashboard.html', questions=questions, posts=posts, upcoming_events=upcoming_events)

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
@app.route('/like_post/<post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    try:
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            flash('Post not found')
            return redirect(url_for('dashboard'))

        user_id = ObjectId(current_user.id)
        interested_users = post.get('interested_users', [])

        # Check if user already liked the post
        user_liked = any(str(user) == str(user_id) for user in interested_users)

        if user_liked:
            # Unlike the post
            db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$pull': {'interested_users': user_id}}
            )
        else:
            # Like the post
            db.posts.update_one(
                {'_id': ObjectId(post_id)},
                {'$addToSet': {'interested_users': user_id}}
            )

        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/comment_post/<post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    try:
        content = request.form.get('comment')
        if not content:
            flash('Comment cannot be empty')
            return redirect(url_for('dashboard'))

        # Create comment object
        comment_data = {
            'user_id': ObjectId(current_user.id),
            'content': content,
            'created_at': datetime.now()
        }

        # Add comment to post
        db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$push': {'comments': comment_data}}
        )

        flash('Comment added successfully')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error: {str(e)}')
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

@app.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        location = request.form.get('location')
        
        event_data = {
            'user_id': ObjectId(current_user.id),
            'title': title,
            'description': description,
            'date': datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M"),
            'location': location,
            'created_at': datetime.now()
        }
        db.events.insert_one(event_data)
        flash('Event created successfully!')
        return redirect(url_for('events'))
    
    # Get all events sorted by date
    events = list(db.events.find().sort('date', 1))
    for event in events:
        event['_id'] = str(event['_id'])
        event['user_id'] = str(event['user_id'])
        author = db.users.find_one({'_id': ObjectId(event['user_id'])})
        event['author'] = {
            'full_name': author['name'] if author else 'Unknown User',
            'email': author['email'] if author else ''
        }
    
    return render_template('events.html', events=events)

@app.route('/resources', methods=['GET', 'POST'])
@login_required
def resources():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        category = request.form.get('category')
        
        resource_data = {
            'user_id': ObjectId(current_user.id),
            'title': title,
            'description': description,
            'link': link,
            'category': category,
            'created_at': datetime.now()
        }
        db.resources.insert_one(resource_data)
        flash('Resource added successfully!')
        return redirect(url_for('resources'))
    
    # Get all resources sorted by creation date
    resources = list(db.resources.find().sort('created_at', -1))
    for resource in resources:
        resource['_id'] = str(resource['_id'])
        resource['user_id'] = str(resource['user_id'])
        author = db.users.find_one({'_id': ObjectId(resource['user_id'])})
        resource['author'] = {
            'full_name': author['name'] if author else 'Unknown User',
            'email': author['email'] if author else ''
        }
    
    return render_template('resources.html', resources=resources)

@app.route('/directory')
@login_required
def directory():
    # Get all users sorted by name
    users = list(db.users.find().sort('name', 1))
    for user in users:
        user['_id'] = str(user['_id'])
        # Remove sensitive information
        user.pop('password', None)
        user.pop('email', None)
    return render_template('directory.html', users=users)

@app.route('/add_success_story', methods=['POST'])
@login_required
def add_success_story():
    title = request.form.get('title')
    content = request.form.get('content')

    if title and content:
        success_story = {
            'title': title,
            'content': content,
            'created_at': datetime.now()
        }

        db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$push': {'success_stories': success_story}}
        )
        flash('Success story added successfully!')
    else:
        flash('Title and content are required')

    return redirect(url_for('profile'))



if __name__ == '__main__':
    app.run(debug=True) 