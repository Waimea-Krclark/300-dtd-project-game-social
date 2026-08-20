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
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
            ORDER BY name DESC;
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.type, posts.user_id, posts.parent_id, users.username
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            ORDER BY title DESC
        """
        params = ()
        posts = db.execute(sql, params).fetchall()

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
        
        return render_template("pages/home.jinja", games=games, posts = posts, followed_games = followed_games, likes = likes)

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
            sort = "name"
            dir = "DESC"
        case "1":
            sort = "id"
            dir = "DESC"
        case "2":
            sort = "id"
            dir = "ASC"
    
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, users.username
            FROM games 
            INNER JOIN users ON games.developer_id = users.id
            WHERE name LIKE ?
            ORDER BY {sort} {dir};
        """.format(sort=sort, dir=dir)
        params = (search_match,)
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.type, posts.user_id, posts.parent_id, users.username
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            ORDER BY title DESC
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
    return jsonify({"status": "success", "session_state": session['my_checkbox']})

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

