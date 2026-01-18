from flask import Flask, redirect, url_for , request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template_string
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ===================== MODELS =====================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    user = db.Column(db.String(50))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================== BASE TEMPLATE =====================

BASE_HTML = """
<!DOCTYPE html>
<html lang="ka">
<head>
<meta charset="UTF-8">
<title>ქართული ფილმები</title>
<style>
body { font-family: sans-serif; background:#f5f7fa; margin:0 }
nav { background:white; padding:15px }
nav a { margin-right:15px; text-decoration:none; color:#333 }
.container { background:white; margin:20px; padding:20px; border-radius:8px }
input, textarea { width:100%; padding:8px; margin:5px 0 }
button { padding:8px 15px; background:#4CAF50; color:white; border:none }
</style>
</head>
<body>


<nav>
<a href="/">მთავარი</a>
<a href="/movies">ფილმები</a>
<a href="/users">უზერები</a>
{% if current_user.is_authenticated %}
<a href="/profile">პროფილი</a>
<a href="/logout">გამოსვლა</a>
{% else %}
<a href="/login">შესვლა</a>
<a href="/register">რეგისტრაცია</a>
{% endif %}
</nav>

<div class="container">
{{ content|safe }}
</div>

</body>
</html>
"""

def render_page(content):
    return render_template_string(BASE_HTML, content=content)

# ===================== ROUTES =====================

@app.route('/')
def index():
    return render_page("<h2>ქართული ფილმების შეფასების საიტი</h2>")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_page("""
    <h2>რეგისტრაცია</h2>
    <form method="post">
        <input name="username" placeholder="მომხმარებელი">
        <input name="password" type="password" placeholder="პაროლი">
        <button>რეგისტრაცია</button>
    </form>
    """)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/profile')
        flash("არასწორი მონაცემები")

    return render_page("""
    <h2>შესვლა</h2>
    <form method="post">
        <input name="username" placeholder="მომხმარებელი">
        <input name="password" type="password" placeholder="პაროლი">
        <button>შესვლა</button>
    </form>
    """)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/profile')
@login_required
def profile():
    return render_page(f"<h2>პროფილი</h2><p>{current_user.username}</p>")

@app.route('/movies')
def movies():
    movies = Movie.query.all()
    html = "<h2>ფილმები</h2>"
    for m in movies:
        html += f'<p><a href="/movie/{m.id}">{m.title}</a></p>'
    return render_page(html)

@app.route('/movie/<int:id>', methods=['GET','POST'])
def movie(id):
    movie = Movie.query.get_or_404(id)

    if request.method == 'POST' and current_user.is_authenticated:
        r = Review(
            rating=request.form['rating'],
            comment=request.form['comment'],
            user=current_user.username,
            movie_id=id
        )
        db.session.add(r)
        db.session.commit()

    reviews = Review.query.filter_by(movie_id=id).all()

    html = f"<h2>{movie.title}</h2><p>{movie.description}</p>"

    if current_user.is_authenticated:
        html += """
        <form method="post">
            <input name="rating" placeholder="შეფასება 1-10">
            <textarea name="comment" placeholder="კომენტარი"></textarea>
            <button>დამატება</button>
        </form>
        """

    html += "<h3>შეფასებები</h3>"
    for r in reviews:
        html += f"<p>{r.user}: {r.rating}/10 – {r.comment}</p>"

    return render_page(html)

@app.route('/users')
def users():
    users_list = User.query.all()       # Query ყველა მომხმარებელს
    html = "<h2>უზერები</h2>"
    for u in users_list:
        html += f"<p>{u.username}</p>"

    return render_page(html)


# ===================== INIT =====================

with app.app_context():
    db.create_all()
    if Movie.query.count() == 0:
        db.session.add(Movie(title="ცისფერი მთები", description="ქართული კლასიკა"))
        db.session.add(Movie(title="მონანიება", description="ქართული დრამა"))
        db.session.commit()


@app.route('/all-users')
def all_users():
    users_list = User.query.all()
    html = "<h2>ყველა მომხმარებელი</h2>"
    for u in users_list:
        html += f"<p>{u.username}</p>"
    return render_page(html)

if __name__ == "__main__":
    app.run(debug=True)























































