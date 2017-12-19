from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Movie
import random
import string
import httplib2
import json
import requests
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(
                open('client_secrets.json', 'r').read())['web']['client_id']
# Connect to Database and create database session
engine = create_engine('sqlite:///movies.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    generate_csrf_token()
    return render_template('login.html', STATE=login_session['_csrf_token'],
                           CLIENT_ID=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['_csrf_token']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
                        "Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
                        "Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        flash('You are already signed in.', 'primary')
        response = make_responses(json.dumps(
                                    'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['email'] = data['email']
    login_session['picture'] = data['picture']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    flash('You are now signed in.', 'primary')
    return 'Success'


# CSRF Protection helper functions
def generate_csrf_token():
    if '_csrf_token' not in login_session:
        csrf_token = ''.join(random.choice(string.ascii_uppercase +
                             string.digits) for x in xrange(32))
        login_session['_csrf_token'] = csrf_token
        return login_session['_csrf_token']


# User Helper Functions
def createUser(login_session):
    newUser = User(email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
                    json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['access_token']
            del login_session['gplus_id']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['provider']
            flash('You successfully signed out.', 'primary')
            return redirect(url_for('showGenres'))
    else:
        flash('You were not signed in.', 'warning')
        return redirect(url_for('showGenres'))


# JSON APIs to view Movie information
@app.route('/genres/<int:genre_id>/movies/JSON')
def genreMoviesGenreJSON(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    movies = session.query(Movie).filter_by(genre_id=genre_id).all()
    return jsonify(movies=[i.serialize for i in movies])


@app.route('/genres/<int:genre_id>/movies/<int:movie_id>/JSON')
def movieJSON(genre_id, movie_id):
    movie = session.query(Movie).filter_by(id=movie_id,
                                           genre_id=genre_id).one()
    return jsonify(movie=movie.serialize)


@app.route('/genres/JSON')
def genresJSON():
    genres = session.query(Genre).all()
    return jsonify(genres=[i.serialize for i in genres])


@app.route('/movies/JSON')
def moviesJSON():
    movies = session.query(Movie).all()
    return jsonify(movies=[i.serialize for i in movies])


@app.route('/users/JSON')
def userJSON():
    users = session.query(User).all()
    return jsonify(users=[i.serialize for i in users])


# Show movies in all genres
@app.route('/')
@app.route('/genres/')
def showGenres():
    genres = session.query(Genre).order_by(asc(Genre.name))
    movies = session.query(Movie).order_by(asc(Movie.title))
    if 'user_id' not in login_session:
        return render_template('movies.html', genres=genres, movies=movies,
                               current_genre=None, user_id=None)
    else:
        return render_template('movies.html', genres=genres, movies=movies,
                               current_genre=None,
                               user_id=login_session['user_id'])


# Create a genre
@app.route('/genres/new/', methods=['GET', 'POST'])
def newGenre():
    if request.method == 'POST':
        # Validate state token
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            response = make_response(json.dumps('Invalid state parameter.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            return response
        newGenre = Genre(
                    name=request.form['name'],
                    user_id=login_session['user_id'])
        session.add(newGenre)
        flash('Created %s genre.' % newGenre.name, "success")
        session.commit()
        return redirect(url_for('showGenres'))
    else:
        if 'user_id' not in login_session:
            flash('Sign in to create a new genre.', 'warning')
            return redirect('/login')
        else:
            generate_csrf_token()
            return render_template('newgenre.html',
                                   csrf_token=login_session['_csrf_token'])


# Edit a genre
@app.route('/genres/<int:genre_id>/edit/', methods=['GET', 'POST'])
def editGenre(genre_id):
    editedGenre = session.query(Genre).filter_by(id=genre_id).one()
    if 'user_id' not in login_session:
        flash('Sign in to rename a genre.', 'warning')
        return redirect(url_for('showLogin'))
    if editedGenre.user_id != login_session['user_id']:
        flash('You can only rename genres you created.', 'warning')
        return redirect(url_for('showGenres'))
    if request.method == 'POST':
        # Validate state token
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            response = make_response(json.dumps('Invalid state parameter.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            return response
        if request.form['name']:
            editedGenre.name = request.form['name']
            flash('Saved %s genre.' % editedGenre.name, "success")
            return redirect(url_for('showGenres'))
    else:
        generate_csrf_token()
        return render_template('editgenre.html', genre=editedGenre,
                               csrf_token=login_session['_csrf_token'])


# Delete a genre
@app.route('/genres/<int:genre_id>/delete/', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    deletedGenre = session.query(Genre).filter_by(id=genre_id).one()
    if 'user_id' not in login_session:
        flash('Sign in to delete a genre.', 'warning')
        return redirect(url_for('showLogin'))
    if deletedGenre.user_id != login_session['user_id']:
        flash('You can only delete genres you created.', 'warning')
        return redirect(url_for('showGenres'))
    if request.method == 'POST':
        # Validate state token
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            response = make_response(json.dumps('Invalid state parameter.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            return response
        # Delete movies in deleted genre
        session.query(Movie).filter_by(genre_id=genre_id).delete()
        session.delete(deletedGenre)
        flash('Deleted %s genre.' % deletedGenre.name, "danger")
        session.commit()
        return redirect(url_for('showGenres'))
    else:
        generate_csrf_token()
        return render_template('deletegenre.html', genre=deletedGenre,
                               csrf_token=login_session['_csrf_token'])


# Show movies in a given genre
@app.route('/genres/<int:genre_id>/')
@app.route('/genres/<int:genre_id>/movies/')
def showMovies(genre_id):
    genres = session.query(Genre).order_by(asc(Genre.name))
    current_genre = session.query(Genre).filter_by(id=genre_id).one()
    movies = session.query(Movie).filter_by(
                                            genre_id=genre_id).order_by(
                                            asc(Movie.title)).all()
    if 'user_id' not in login_session:
        return render_template('movies.html', genres=genres, movies=movies,
                               current_genre=current_genre, user_id=None)
    else:
        return render_template('movies.html', genres=genres, movies=movies,
                               current_genre=current_genre,
                               user_id=login_session['user_id'])


# Create a new movie
@app.route('/genres/<int:genre_id>/movies/new/', methods=['GET', 'POST'])
def newMovie(genre_id):
    if 'user_id' not in login_session:
        flash('Sign in to create a movie.', 'warning')
        return redirect(url_for('showLogin'))
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        flash('You can only add movies to a genre you created.', 'warning')
        return redirect(url_for("showMovies", genre_id=genre_id))
    if request.method == 'POST':
        # Validate state token
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            response = make_response(json.dumps('Invalid state parameter.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            return response
        newMovie = Movie(title=request.form['title'],
                         description=request.form['description'],
                         rating=request.form['rating'],
                         year=request.form['year'], genre_id=genre_id,
                         user_id=genre.user_id)
        session.add(newMovie)
        session.commit()
        flash('Created %s movie.' % newMovie.title, 'success')
        return redirect(url_for('showMovies', genre_id=genre_id))
    else:
        generate_csrf_token()
        return render_template('newmovie.html', genre_id=genre_id,
                               csrf_token=login_session['_csrf_token'])


# Edit a movie
@app.route('/genres/<int:genre_id>/movie/<int:movie_id>/edit',
           methods=['GET', 'POST'])
def editMovie(genre_id, movie_id):
    if 'user_id' not in login_session:
        flash('Sign in to edit a movie.', 'warning')
        return redirect(url_for('showLogin'))
    editedMovie = session.query(Movie).filter_by(id=movie_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        flash('You can only edit movies that you created.', 'warning')
        return redirect(url_for("showMovies", genre_id=genre_id))
    if request.method == 'POST':
        # Validate state token
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            response = make_response(json.dumps('Invalid state parameter.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            return response
        if request.form['title']:
            editedMovie.title = request.form['title']
        if request.form['description']:
            editedMovie.description = request.form['description']
        if request.form['rating']:
            editedMovie.rating = request.form['rating']
        if request.form['year']:
            editedMovie.year = request.form['year']
        session.add(editedMovie)
        session.commit()
        flash('%s updated.' % editedMovie.title, 'success')
        return redirect(url_for('showMovies', genre_id=genre_id))
    else:
        generate_csrf_token()
        return render_template('editmovie.html', genre_id=genre_id,
                               movie_id=movie_id, movie=editedMovie,
                               csrf_token=login_session['_csrf_token'])


# Delete a movie
@app.route('/genre/<int:genre_id>/movie/<int:movie_id>/delete',
           methods=['GET', 'POST'])
def deleteMovie(genre_id, movie_id):
    if 'user_id' not in login_session:
        flash('Sign in to edit a movie.', 'warning')
        return redirect(url_for('showLogin'))
    genre = session.query(Genre).filter_by(id=genre_id).one()
    deletedMovie = session.query(Movie).filter_by(id=movie_id).one()
    if login_session['user_id'] != genre.user_id:
        flash('You can only delete movies that you created.', 'warning')
        return redirect(url_for("showMovies", genre_id=genre_id))
    if request.method == 'POST':
        # Validate state token
        token = login_session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            response = make_response(json.dumps('Invalid state parameter.'),
                                     401)
            response.headers['Content-Type'] = 'application/json'
            return response
        session.delete(deletedMovie)
        session.commit()
        flash('Deleted %s.' % deletedMovie.title, 'success')
        return redirect(url_for('showMovies', genre_id=genre_id))
    else:
        generate_csrf_token()
        return render_template('deletemovie.html', movie=deletedMovie,
                               csrf_token=login_session['_csrf_token'])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
