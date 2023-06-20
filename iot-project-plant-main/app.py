from datetime import datetime
from functools import wraps
import secrets
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from models import Post, User, db, Plant, MyPlant
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///realDB.db' 
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)
app.secret_key = secrets.token_hex(16)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Custom middleware to check if the user is logged in
@app.before_request
def require_login():
    protected_routes = ['index', 'add-plant']  # Add the names of your protected routes here

    if request.endpoint in protected_routes and 'user_id' not in session:
        return redirect(url_for('login'))
    
@app.route('/')
def index():
    plants = Plant.query.all()
    user = User.query.filter_by(id=session['user_id']).first()
    # aleen mijnPlanten van de ingelogde user
    mijn_planten = MyPlant.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', plants=plants, mijn_planten=mijn_planten, user=user)

@app.route('/add-plant')
def add_plant():
    plants = Plant.query.all()
    user = User.query.filter_by(id=session['user_id']).first()
    return render_template('addPlant.html', plants=plants, user=user)

# detail pagina van een plant
@app.route('/plant/<int:plant_id>')
def plant(plant_id):
    my_plant = MyPlant.query.filter_by(id=plant_id).first()
    user = User.query.filter_by(id=session['user_id']).first()
    return render_template('plantDetail.html', my_plant=my_plant, user=user)

@app.route('/feed')
def feed():
    user = User.query.filter_by(id=session['user_id']).first()
    # desc
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('feed.html', user=user, posts=posts)

@app.route('/add-post')
def add_post():
    user = User.query.filter_by(id=session['user_id']).first()
    return render_template('addPost.html', user=user)

@app.route('/create-post', methods=['POST'])
def create_post():
    form_data = request.form
    title = form_data['title']
    content = form_data['content']
    user_id = session['user_id']
    created_at = datetime.now()
    updated_at = datetime.now()

    post = Post(title=title, content=content, user_id=user_id, created_at=created_at, updated_at=updated_at)
    db.session.add(post)
    db.session.commit()

    return jsonify({'message': 'Post created successfully'})




@app.route('/save-plant', methods=['POST'])
def save_plant():
    form_data = request.form
    plant_location = form_data['loc']
    plant_id = int(form_data['plant_id'])
    user_id = session['user_id']
    last_watered = datetime.now()
    plant_watering = True  # Assuming it should always be True based on your code
    
    # Get the current timestamp
    created_at = datetime.now()
    updated_at = datetime.now()
    
    # Save the plant name to the 'mijnPlanten' database
    my_plant = MyPlant(location=plant_location, plant_id=plant_id, user_id=user_id, last_watered=last_watered, automatic_watering=plant_watering, created_at=created_at, updated_at=updated_at)
    db.session.add(my_plant)
    db.session.commit()

    return jsonify({'message': 'Plant added successfully'})


# Route om de plantnaam op te halen uit de 'mijnplanten' database
@app.route('/get-plant', methods=['GET'])
def get_plant():
    # Haal de meest recente plantnaam op uit de 'mijnplanten' database
    my_plant = MyPlant.query.order_by(MyPlant.id.desc()).first()
    if my_plant:
        return jsonify({'name': my_plant.name})
    else:
        return jsonify({'name': None})


# login

# Define your User model and database setup here



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username exists in the database
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # Store user ID in session to maintain login state
            session['user_id'] = user.id
            return redirect(url_for('index'))

        return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print("Register route accessed")
    if request.method == 'POST':
        print("Register route accessed POST ")
        username = request.form['username']
        password = request.form['password']

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template('register.html', error='Username already exists')

        # Create a new user and add it to the database
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, created_at=datetime.now(), updated_at=datetime.now())
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
