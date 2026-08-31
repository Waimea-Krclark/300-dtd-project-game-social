#===========================================================
# PROJECT NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from io import BytesIO
import html
from app.helpers import *
import uuid
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

# Create the app
app = Flask(__name__)


#===========================================================
# App Routes Handlers
#===========================================================

#-----------------------------------------------------------
# Home page - Show all games/posts
#-----------------------------------------------------------
@app.get("/")
def show_home():
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, games.image_name, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
            ORDER BY games.id DESC;
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            ORDER BY posts.id DESC
        """
        params = ()
        posts = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM games
        """
        params = ()
        allgames = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM following  
        """
        params = ()
        followed_games = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()
        
        return render_template("pages/home.jinja", games=games, posts = posts, followed_games = followed_games, likes = likes, allgames=allgames)

#-----------------------------------------------------------
# Home search request - Search resuslts
#-----------------------------------------------------------
@app.get("/search")
def process_search():
    search_term = request.args.get('q', '')
    search_match = f"%{search_term}%"
    sort_term = request.args.get('sortby', '')
    match sort_term:
        case "0":
            Gsort = "name"
            Psort = "title"
            dir = "ASC"
        case "1":
            Gsort = "games.id"
            Psort = "posts.id"
            dir = "DESC"
        case "2":
            Gsort = "games.id"
            Psort = "posts.id"
            dir = "ASC"
    
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, games.image_name, users.username
            FROM games 
            INNER JOIN users ON games.developer_id = users.id
            WHERE name LIKE ?
            ORDER BY {sort} {dir};
        """.format(sort=Gsort, dir=dir)
        params = (search_match,)
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE title LIKE ?
            ORDER BY {sort} {dir}
        """.format(sort=Psort, dir=dir)
        params = (search_match,)
        posts = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM games
        """
        params = ()
        allgames = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM posts
        """
        params = ()
        allposts = db.execute(sql, params).fetchall()
        
        sql = """
            SELECT *
            FROM following  
        """
        params = ()
        followed_games = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()

        return render_template("pages/home.jinja", games=games, posts = posts, followed_games = followed_games, likes = likes, allgames=allgames, allposts=allposts, search_term=search_term, sort_term=sort_term)
    
#-----------------------------------------------------------
# Profile page
#-----------------------------------------------------------
@app.get("/profile/<int:id>")
def sshow_profile(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM users
            WHERE id = ?
        """
        params = (id,)
        user = db.execute(sql, params).fetchone()

        sql = """
            SELECT *
            FROM following  
            WHERE user_id = ?
        """
        params = (id,)
        followed_games = db.execute(sql, params).fetchall()

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]
        print(followed_pairs)

        sql = """
            SELECT *
            FROM games
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        return render_template("pages/profile.jinja", user = user, followed_pairs=followed_pairs, games = games)

#-----------------------------------------------------------
# Sign In page
#-----------------------------------------------------------
@app.get("/user/login")
def show_login_form():
    return render_template("pages/sign_in_form.jinja")

#-----------------------------------------------------------
# Sign Up page
#-----------------------------------------------------------
@app.get("/user/signup")
def show_signup_form():
    return render_template("pages/sign_up_form.jinja")

#-----------------------------------------------------------
# Handle User Signup
#-----------------------------------------------------------
@app.post("/signup")
def process_new_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = "SELECT id FROM users WHERE LOWER(username)=?"
        params = (username.lower(),)
        user = db.execute(sql, params).fetchone()

        if user:
            flash(f"Username '{username}' already exists", "error")
            return redirect("/user/new")

        pass_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (username, pass_hash)
            VALUES (?, ?)
        """
        params = (username, pass_hash)
        db.execute(sql, params)

        flash("Account created. Please login", "success")
        return redirect("/user/login")
    
#-----------------------------------------------------------
# Handle User Sign in
#-----------------------------------------------------------
@app.post("/login")
def login_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    with connect_db() as db:
        sql = """
            SELECT id, pass_hash, is_developer
            FROM users
            WHERE LOWER(username)=?
        """
        params = (username.lower(),)
        user = db.execute(sql, params).fetchone()

        if not user:
            flash(f"Unknown user", "error")
            return redirect("/user/login")

        if not check_password_hash(user["pass_hash"], password):
            flash(f"Incorrect password", "error")
            return redirect("/user/login")

        session["logged_in"] = True
        session["user"] = {
            "user_id": user["id"],
            "username": username,
            "is_dev": user["is_developer"]
        }

        flash(f"Login successful as {username}", "success")
        return redirect("/")

@app.route('/save-checkbox', methods=['POST'])
def save_checkbox():
    data = request.get_json()
    
    # Store the boolean (True/False) directly into the session
    session['show_games'] = data.get('checked', False)
    
    # Return a quick JSON response to let the front-end know it worked
    return jsonify({"status": "success", "session_state": session['show_games']})

#-----------------------------------------------------------
# Handle User Log Out
#-----------------------------------------------------------
@app.get("/logout")
def logout_user():
    session.clear()
    flash(f"You have been logged out", "success")
    return redirect("/")

#===========================================================
# Configure the app
#===========================================================
load_dotenv()
app.config.from_prefixed_env()
init_logging(app)
init_text_filters(app)
init_date_filters(app)
init_error_handlers(app)
init_database()
register_commands(app)

