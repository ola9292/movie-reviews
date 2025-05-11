from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Float, desc
from sqlalchemy.orm import Mapped, mapped_column
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
load_dotenv()
import os

tmdb_api_key = ''
bearer_token = os.getenv("BEARER_TOKEN")

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
# initialize the app with the extension
db.init_app(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'

with app.app_context():
    db.create_all()
 
#add new movie manually   
# new_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

#forms
class MovieForm(FlaskForm):
    rating = StringField('Movie Rating', validators=[DataRequired()])
    review = StringField('Movie Review', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(desc(Movie.ranking))).scalars()
    return render_template("index.html", movies=movies)

#add movie
@app.route("/add",  methods=["POST", "GET"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        print(request.form['title'])
        movie_name = request.form['title']
        url = f"https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1&query={movie_name}"

        headers = {
            "accept": "application/json",
            "Authorization": bearer_token
        }

        response = requests.get(url, headers=headers)

        # print(response.text)
        data = response.json()
        movies = data['results']
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=form)

#fetch single file from tmdb
@app.route("/single_movie/<int:id>")
def single_movie(id):
    
    url = f"https://api.themoviedb.org/3/movie/{id}?language=en-US"

    headers = {
        "accept": "application/json",
        "Authorization": bearer_token
    }
    try:
        response = requests.get(url, headers=headers)
    
        movie_data = response.json()
        # print(movie_data['original_title'])
        # print(movie_data['belongs_to_collection']['poster_path'])
        # print(movie_data['release_date'].split('-')[0])
        # print(movie_data['overview'])
        title = movie_data.get('original_title', 'Unknown Title')
        
        mg_url = None
        if movie_data.get('belongs_to_collection') and movie_data['belongs_to_collection'].get('poster_path'):
            img_url = f"https://image.tmdb.org/t/p/w500{movie_data['belongs_to_collection']['poster_path']}"
        else:
            img_url = "https://via.placeholder.com/500x750?text=No+Image+Available"
            
        year = None
        if movie_data.get('release_date'):
            parts = movie_data['release_date'].split('-')
            year = parts[0] if parts else 'Unknown'
        else:
            year = 'Unknown'
            
        description = movie_data.get('overview', 'No description available')
        #add the retrieved movie to db
        movie = Movie(
            title=title,
            img_url=img_url,
            year=year,
            description=description
        )
        db.session.add(movie)
        db.session.commit()
    except requests.exceptions.RequestException as e:
        # Handle API request errors
        print(f"API request error: {e}")
        return redirect(url_for('home'))
        
    except Exception as e:
        # Handle any other errors
        print(f"Error: {e}")
        db.session.rollback()  # Roll back the transaction in case of error
        return redirect(url_for('home'))
  
    return redirect(url_for('edit_movie', id=movie.id))

#update a movie
@app.route("/movies/edit/<int:id>", methods=["POST", "GET"])
def edit_movie(id):
    form = MovieForm()
    movie = db.get_or_404(Movie, id)
    
    if form.validate_on_submit():
        print(True)
        movie.rating = request.form['rating']
        movie.review = request.form['review']
        
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html",movie=movie, form=form)

#delete movie
@app.route("/movies/<int:id>/delete", methods=["GET", "POST"])
def delete_movie(id):
    movie = db.get_or_404(Movie, id)
    print(movie)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))