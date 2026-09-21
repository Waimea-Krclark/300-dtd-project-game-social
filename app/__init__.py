#===========================================================
# PROJECT NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response, jsonify, url_for
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

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()
        
        return render_template("pages/home.jinja", games=games, posts = posts, followed_games=followed_games, followed_pairs=followed_pairs, likes = likes, allgames=allgames)

#-----------------------------------------------------------
# Home search request - Search resuslts
#-----------------------------------------------------------
@app.get("/search")
def home_process_search():
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

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()

        return render_template("pages/home.jinja", games=games, posts = posts, followed_games=followed_games, followed_pairs=followed_pairs, likes = likes, allgames=allgames, allposts=allposts, search_term=search_term, sort_term=sort_term)

#-----------------------------------------------------------
# Game page
#-----------------------------------------------------------
@app.get("/game/<int:id>")
def show_game(id):
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, games.image_name, users.username
            FROM games 
            INNER JOIN users ON games.developer_id = users.id
            WHERE games.id = ?
        """
        params = (id,)
        game = db.execute(sql, params).fetchone()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, users.profile_image, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE game_id = ?
        """
        params = (id,)
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

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()

        return render_template("pages/game.jinja", game=game, posts = posts, followed_games=followed_games, followed_pairs=followed_pairs, likes = likes, allgames=allgames, allposts=allposts)
    
#-----------------------------------------------------------
# Game page
#-----------------------------------------------------------
@app.get("/game/<int:id>/search")
def game_process_search(id):
    search_term = request.args.get('q', '')
    search_match = f"%{search_term}%"
    sort_term = request.args.get('sortby', '')
    match sort_term:
        case "0":
            sort = "title"
            dir = "ASC"
        case "1":
            sort = "posts.id"
            dir = "DESC"
        case "2":
            sort = "posts.id"
            dir = "ASC"
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, games.image_name, users.username
            FROM games 
            INNER JOIN users ON games.developer_id = users.id
            WHERE games.id = ?
        """
        params = (id,)
        game = db.execute(sql, params).fetchone()
        
        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, users.profile_image, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE game_id = ?
        """
        params = (id,)
        posts = db.execute(sql, params).fetchall()
        
        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, users.profile_image, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE title LIKE ?
            ORDER BY {sort} {dir}
        """.format(sort=sort, dir=dir)
        params = (search_match,)
        search_posts = db.execute(sql, params).fetchall()

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

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()

        return render_template("pages/game.jinja", game=game, posts = posts, followed_games=followed_games, followed_pairs=followed_pairs, likes = likes, allgames=allgames, allposts=allposts, search_posts=search_posts, search_term=search_term, sort_term=sort_term)


#-----------------------------------------------------------
# Follow Game page
#-----------------------------------------------------------
@login_required
@app.get("/game/<int:id>/follow")
def follow_game(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM following  
            WHERE user_id = ? AND game_id = ?
        """
        params = (session.get("user")["user_id"], id)
        followed_games = db.execute(sql, params).fetchall()

        if not followed_games:
            sql = """
                INSERT INTO following (user_id, game_id)
                VALUES (?, ?)
            """
            params = (session.get("user")["user_id"], id)
            db.execute(sql, params)
        else:
            flash(f"Already Following", "error")

        return redirect(request.referrer or "/")
    
#-----------------------------------------------------------
# Unfollow Game page
#-----------------------------------------------------------
@login_required
@app.get("/game/<int:id>/unfollow")
def unfollow_game(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM following  
            WHERE user_id = ? AND game_id = ?
        """
        params = (session.get("user")["user_id"], id)
        followed_games = db.execute(sql, params).fetchall()

        if followed_games:
            sql = """
                DELETE FROM following WHERE user_id = ? AND game_id = ?
            """
            params = (session.get("user")["user_id"], id)
            db.execute(sql, params)
        else:
            flash(f"Already Unfollowed", "error")

        return redirect(request.referrer or "/")
    
#-----------------------------------------------------------
# Post page
#-----------------------------------------------------------
@app.get("/post/<int:id>")
def show_post(id):
    with connect_db() as db:
        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, users.profile_image, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE posts.id = ?
        """
        params = (id,)
        post = db.execute(sql, params).fetchone()

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

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]

        sql = """
            SELECT *
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM media WHERE post_id = ?
        """
        params = (id,)
        media = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.content, posts.type, posts.user_id, posts.parent_id, users.username, users.profile_image
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            WHERE parent_id IS NOT NULL
        """
        params = ()
        comments = db.execute(sql, params).fetchall()

        return render_template("pages/post.jinja", post = post, followed_games=followed_games, followed_pairs=followed_pairs, likes = likes, allposts=allposts, media = media, comments=comments)

#-----------------------------------------------------------
# Profile page
#-----------------------------------------------------------
@app.get("/user/profile/<int:id>")
def show_profile(id):
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

        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, games.image_name, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        return render_template("pages/profile.jinja", user = user,followed_games=followed_games, followed_pairs=followed_pairs, games = games)

#-----------------------------------------------------------
# Profile page
#-----------------------------------------------------------
@login_required
@app.get("/user/profile/<int:id>/edit")
def edit_profile(id):
    with connect_db() as db:
        if session.get("user")["user_id"] != id:
            flash("Invalid action", "error")
            return redirect("/")
        sql = """
            SELECT *
            FROM users
            WHERE id = ?
        """
        params = (id,)
        user = db.execute(sql, params).fetchone()

        return render_template("pages/user_edit_form.jinja", user = user)

#-----------------------------------------------------------
# Handle Profile Edit
#-----------------------------------------------------------
@login_required
@app.post("/profile/edit/<int:id>")
def edit_user_details(id):
    username = request.form.get('username', '').strip()
    old_password = request.form.get('password', '').strip()
    new_password = request.form.get('new_password', None).strip()
    image_file = request.files.get('image', None)
    bio = request.form.get('bio', '').strip()

    with connect_db() as db:
            sql = "SELECT id FROM users WHERE LOWER(username)=?"
            params = (username.lower(),)
            user = db.execute(sql, params).fetchone()

            print(username.lower())
            print(session["user"].get("username").lower())

            if user and username.lower() != (session["user"].get("username")).lower():
                flash(f"Username '{username}' already exists", "error")
                return redirect(f"/user/profile/{id}")
 
            if image_file:
                # Sanitise filename and make it unique
                filename = secure_filename(image_file.filename)
                random_prefix = uuid.uuid4().hex[:12]
                unique_filename = f"{random_prefix}_{filename}"
        
                # Get the path of the upload folder
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
                # Save file to disk
                image_file.save(filepath)
            else:
                sql = "SELECT profile_image FROM users WHERE id=?"
                params = (id,)
                image_name = db.execute(sql, params).fetchone()
                unique_filename = image_name["profile_image"]
 
            sql = "SELECT pass_hash FROM users WHERE id=?"
            params = (id,)
            current_hash = db.execute(sql, params).fetchone()
            hash_string = current_hash["pass_hash"]

            if check_password_hash(current_hash["pass_hash"], old_password):
                if new_password:
                    pass_hash = generate_password_hash(new_password)
                    flash(f"Password changed")
                else:
                    pass_hash = hash_string
            else:
                flash(f"Incorrect password", "error")
                return redirect("/user/login")

            sql = """
                UPDATE users SET username = ?, pass_hash = ?, profile_image = ?, bio =? WHERE id =?
            """
            params = (username, pass_hash, unique_filename, bio, id)
            db.execute(sql, params)
            session["user"]['username'] = username
            flash("Updated Profile", "success")
            return redirect(f"/user/profile/{id}")

#-----------------------------------------------------------
# Delete User page
#-----------------------------------------------------------
@app.get("/user/<int:id>/delete")
@login_required
def delete_user(id):
    with connect_db() as db:
        if session.get("user")["user_id"] == id:
            sql = """
                DELETE FROM users WHERE id = ?
            """
            params = (id,)
            db.execute(sql, params)

            session.clear()
            flash(f"You have been logged out", "success")
            flash("Deleted User", "success")
        else:
            flash("Invalid action", "error")
    return redirect("/")

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
    image_file = request.files.get('image', None)
    bio = request.form.get('bio', '').strip()

    with connect_db() as db:
        sql = "SELECT id FROM users WHERE LOWER(username)=?"
        params = (username.lower(),)
        user = db.execute(sql, params).fetchone()

        if user:
            flash(f"Username '{username}' already exists", "error")
            return redirect("/user/new")

        if image_file or image_file.filename != '':
            # Sanitise filename and make it unique
            filename = secure_filename(image_file.filename)
            random_prefix = uuid.uuid4().hex[:12]
            unique_filename = f"{random_prefix}_{filename}"
    
            # Get the path of the upload folder
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
            # Save file to disk
            image_file.save(filepath)
        else:
            unique_filename = None
        

        pass_hash = generate_password_hash(password)

        sql = """
            INSERT INTO users (username, pass_hash, profile_image, bio)
            VALUES (?, ?, ?, ?)
        """
        params = (username, pass_hash, unique_filename, bio)
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
@login_required
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

