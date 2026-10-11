#===========================================================
# Checkpoint Social
# By Kieran Clark
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response, jsonify, url_for, abort
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
from os import getenv
from io import BytesIO
import html
from app.helpers import *
import uuid
import os
import nh3
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, UnidentifiedImageError
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')


# Create the app
app = Flask(__name__)

# Sanitising Trix inputs before saving
ALLOWED_TAGS = {
    "div", "br", "strong", "em", "del", "a", "h1",
    "blockquote", "pre", "ul", "ol", "li",
    "figure", "figcaption", "img",
}

ALLOWED_ATTRIBUTES = {
    "a": {"href"},
    "img": {"src", "width", "height"},
    "figure": {"class"},
}

def sanitise_html(html: str) -> str:
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer nofollow",
    )

# Image Upload Limits and scaling
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
MAX_GIF_BYTES = 5 * 1024 * 1024  # 5 MB

# New Image handling to downscale images to appropriate sizing for profiles, posts etc.
def process_image(file_storage, dest_folder, max_dimension=1600, square=False, allow_gif=True):
    try:
        img = Image.open(file_storage.stream)
        fmt = img.format
        if fmt not in ALLOWED_FORMATS:
            raise ValueError("Unsupported image type")

        if fmt == "GIF" and allow_gif:
            # Check size of the raw upload
            file_storage.stream.seek(0, os.SEEK_END)
            size = file_storage.stream.tell()
            if size > MAX_GIF_BYTES:
                raise ValueError("GIF too large")

            # Guard against huge frame counts
            if getattr(img, "n_frames", 1) > 300:
                raise ValueError("Too many frames")

            file_storage.stream.seek(0)
            name = f"{uuid.uuid4().hex}.gif"
            file_storage.save(os.path.join(dest_folder, name))
            return name
        # Fix phone photos that are rotated via EXIF metadata
        img = ImageOps.exif_transpose(img)

        if square:
            img = ImageOps.fit(img, (max_dimension, max_dimension), Image.LANCZOS)
        else:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        # Re-encode to WEBP (small, supports transparency)
        name = f"{uuid.uuid4().hex}.webp"
        img.save(os.path.join(dest_folder, name), "WEBP", quality=82)
        return name
    except (UnidentifiedImageError, ValueError):
        return None

# Removes an image file from uploads
def delete_image(image):
    path = os.path.join(UPLOAD_FOLDER, image)
    if os.path.exists(path):
        os.remove(path)

# For finding all images in provided html, used for Trix
def find_trix_images(html):
    soup = BeautifulSoup(html or "", "html.parser")
    names = []
    for img in soup.find_all("img"): #Searches trix input for <img> tags
        src = img.get("src", "")
        name = Path(urlparse(src).path).name #Gets only filename
        if name:
            names.append(name) #Save Image names to List
    return names


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
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
            ORDER BY games.id DESC;
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, games.name, games.developer_id
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            LEFT JOIN games ON posts.game_id = games.id
            ORDER BY posts.id DESC
        """
        params = ()
        posts = db.execute(sql, params).fetchall()

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

        liked_pairs = [
            (like["user_id"], like["post_id"])
            for like in likes
        ]
        
        return render_template("pages/home.jinja", games=games, posts = posts, followed_pairs=followed_pairs, liked_pairs=liked_pairs, back_url=f"/")

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
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
            FROM games 
            INNER JOIN users ON games.developer_id = users.id
            WHERE name LIKE ?
            ORDER BY {sort} {dir};
        """.format(sort=Gsort, dir=dir)
        params = (search_match,)
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, games.name, games.developer_id
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            LEFT JOIN games ON posts.game_id = games.id
            WHERE title LIKE ?
            ORDER BY {sort} {dir}
        """.format(sort=Psort, dir=dir)
        params = (search_match,)
        posts = db.execute(sql, params).fetchall()

        sql = """
            SELECT parent_id
            FROM posts
            WHERE type = 'comment'
        """
        params = ()
        comments = db.execute(sql, params).fetchall()
        
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

        liked_pairs = [
                    (like["user_id"], like["post_id"])
                    for like in likes
                ]

        return render_template("pages/home.jinja", games=games, posts = posts, followed_pairs=followed_pairs, liked_pairs=liked_pairs, comments=comments, search_term=search_term, sort_term=sort_term, back_url=f"/")


#-----------------------------------------------------------
# Game page
#-----------------------------------------------------------
@app.get("/game/<int:id>")
def show_game(id):
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
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
            SELECT parent_id
            FROM posts
            WHERE type = 'comment'
        """
        params = ()
        comments = db.execute(sql, params).fetchall()
        
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

        liked_pairs = [
            (like["user_id"], like["post_id"])
            for like in likes
        ]

        sql = """
            SELECT *
            FROM media WHERE game_id = ?
        """
        params = (id,)
        media = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM links WHERE game_id = ?
        """
        params = (id,)
        links = db.execute(sql, params).fetchall()
        


        return render_template("pages/game.jinja", game=game, posts = posts,  comments=comments, followed_pairs=followed_pairs, liked_pairs=liked_pairs, links=links, media=media,back_url=f"/")
    
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
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
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
            WHERE title LIKE ? AND game_id = ?
            ORDER BY {sort} {dir}
        """.format(sort=sort, dir=dir)
        params = (search_match, id)
        search_posts = db.execute(sql, params).fetchall()

        sql = """
            SELECT parent_id
            FROM posts
            WHERE type = 'comment'
        """
        params = ()
        comments = db.execute(sql, params).fetchall()
        
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

        liked_pairs = [
            (like["user_id"], like["post_id"])
            for like in likes
        ]

        sql = """
                    SELECT *
                    FROM media WHERE game_id = ?
        """
        params = (id,)
        media = db.execute(sql, params).fetchall()
        
        sql = """
            SELECT *
            FROM links WHERE game_id = ?
        """
        params = (id,)
        links = db.execute(sql, params).fetchall()

        return render_template("pages/game.jinja", game=game, posts = posts, comments=comments, followed_pairs=followed_pairs, liked_pairs=liked_pairs, search_posts=search_posts, search_term=search_term, sort_term=sort_term, links=links, media=media,back_url=f"/")


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
# Create Game page
#-----------------------------------------------------------
@app.get("/game/new")
@login_required
def new_game_form(id=None):
    if not session.get('user')['is_dev'] == 1:
        flash(f"Invalid Action", "error")
        return redirect('/')
    return render_template("pages/game_form.jinja")

#-----------------------------------------------------------
# Handle Game Creation
#-----------------------------------------------------------
@app.post("/game/new")
def process_new_game():
    title = request.form.get('title', '').strip()
    links = request.form.getlist('link')
    description = request.form.get('description', '')
    hero_image = request.files.get('hero', None)
    screenshots = request.files.getlist('screenshots')

    with connect_db() as db:
            sql = "SELECT id FROM games WHERE LOWER(name)=?"
            params = (title.lower(),)
            game = db.execute(sql, params).fetchone()
    
            if game:
                flash(f"Game using title '{title}' already exists", "error")
                return redirect("/game/new")
    
            if hero_image or hero_image.filename != '':
                unique_filename = process_image(hero_image, UPLOAD_FOLDER, max_dimension=1600, square=True, allow_gif=True)
                if unique_filename is None:
                    flash("That image couldn't be used. Please upload a JPG, PNG, WEBP or GIF.", "error")
                    return redirect("/user/new")
            else:
                unique_filename = None
    
            sql = """
                INSERT INTO games (name, description, image_name, developer_id)
                VALUES (?, ?, ?, ?)
            """
            params = (title, description, unique_filename, session.get('user')['user_id'])
            cursor = db.execute(sql, params)
            new_game_id = cursor.lastrowid

            for link in links:
                sql = """
                    INSERT INTO links (link, game_id)
                    VALUES (?, ?)
                """
                params = (link, new_game_id)
                db.execute(sql, params)

            for img in screenshots:
                if img or img.filename != '':
                    unique_filename = process_image(img, UPLOAD_FOLDER, max_dimension=1600, square=True, allow_gif=True)
                    if unique_filename is None:
                        flash("That image couldn't be used. Please upload a JPG, PNG, WEBP or GIF.", "error")
                        return redirect("/user/new")
                else:
                    unique_filename = None

                sql = """
                    INSERT INTO media (image_file, game_id)
                    VALUES (?, ?)
                """
                params = (unique_filename, new_game_id)
                db.execute(sql, params)

            flash("Game created", "success")
            return redirect(f"/game/{new_game_id}")

#-----------------------------------------------------------
# Edit Game page
#-----------------------------------------------------------
@login_required
@app.get("/game/<int:id>/edit")
def edit_game_form(id):
    with connect_db() as db:
            sql = """
                SELECT *
                FROM games
                WHERE id = ?
            """
            params = (id,)
            game = db.execute(sql, params).fetchone()
            if session.get("user")["user_id"] != game["developer_id"]:
                        flash("Invalid action", "error")
                        return redirect("/")

            sql = """
                        SELECT *
                        FROM media WHERE game_id = ?
            """
            params = (id,)
            media = db.execute(sql, params).fetchall()
            
            sql = """
                SELECT *
                FROM links WHERE game_id = ?
            """
            params = (id,)
            links = db.execute(sql, params).fetchall()

    return render_template("pages/game_edit_form.jinja", game=game, media=media, links=links)

#-----------------------------------------------------------
# Handle Game Edit
#-----------------------------------------------------------
@app.post("/game/<int:id>/edit")
def process_edit_game(id):
    title = request.form.get('title', '').strip()
    links = request.form.getlist('link')
    description = request.form.get('description', '')
    hero_image = request.files.get('hero', None)
    screenshots = request.files.getlist('screenshots')
    keep_img_ids = set(request.form.getlist('keep_media', type=int))
    keep_link_ids = set(request.form.getlist('keep_link', type=int))

    with connect_db() as db:
            sql = "SELECT id FROM games WHERE LOWER(name)=?"
            params = (title.lower(),)
            game = db.execute(sql, params).fetchone()

            if game and id != game["id"]:
                flash(f"Game using title '{title}' already exists", "error")
                return redirect(f"/game/{id}/edit")
    
            if hero_image or hero_image.filename != '':
                unique_filename = process_image(hero_image, UPLOAD_FOLDER, max_dimension=1600, square=True, allow_gif=True)
                if unique_filename is None:
                    flash("That image couldn't be used. Please upload a JPG, PNG, WEBP or GIF.", "error")
                    return redirect(f"/game/{id}/edit")
            else:
                sql = "SELECT image_name FROM games WHERE id=?"
                params = (id,)
                image_name = db.execute(sql, params).fetchone()
                unique_filename = image_name["image_name"]
    
            sql = """
                UPDATE games SET name = ?, description = ?, image_name = ?, developer_id=? WHERE id =?
            """
            params = (title, description, unique_filename, session.get('user')['user_id'], id)
            db.execute(sql, params)

            sql = "SELECT id, link FROM links WHERE game_id=?"
            params = (id,)
            check_links = db.execute(sql, params).fetchall()
            for link in check_links:
                if link['id'] not in keep_link_ids:
                    sql = """
                        DELETE FROM links WHERE id = ? AND game_id = ?
                    """
                    params = (link["id"], id)
                    db.execute(sql, params)

            for link in links:
                sql = """
                    INSERT INTO links (link, game_id)
                    VALUES (?, ?)
                """
                params = (link, id)
                db.execute(sql, params)

            sql = "SELECT id, image_file FROM media WHERE game_id=?"
            params = (id,)
            images = db.execute(sql, params).fetchall()

            for image in images:
                if image['id'] not in keep_img_ids:
                    sql = """
                        DELETE FROM media WHERE id = ? AND game_id = ?
                    """
                    params = (image["id"], id)
                    db.execute(sql, params)
                    delete_image(image["image_file"])
            
            for img in screenshots:
                if img or img.filename != '':
                    unique_filename = process_image(img, UPLOAD_FOLDER, max_dimension=1600, square=True, allow_gif=True)
                    if unique_filename is None:
                        flash("That image couldn't be used. Please upload a JPG, PNG, WEBP or GIF.", "error")
                        return redirect(f"/game/{id}/edit")
                    else:
                        sql = """
                            INSERT INTO media (image_file, game_id)
                            VALUES (?, ?)
                        """
                        params = (unique_filename, id)
                        db.execute(sql, params)

            flash("Game updated", "success")
            return redirect(f"/game/{id}")

#-----------------------------------------------------------
# Delete Game page
#-----------------------------------------------------------
@app.get("/game/<int:id>/delete")
@login_required
def delete_game(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM games WHERE developer_id = ? and id = ?  
        """
        params = (session.get("user")["user_id"], id)
        game = db.execute(sql, params).fetchone()

        if  game:
            delete_image(game["image_name"])
            sql = """
                DELETE FROM games WHERE id = ?
            """
            params = (id,)
            db.execute(sql, params)

            flash("Deleted game", "success")
        else:
            flash("Invalid action", "error")
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
            FROM likes  
        """
        params = ()
        likes = db.execute(sql, params).fetchall()

        liked_pairs = [
            (like["user_id"], like["post_id"])
            for like in likes
        ]

        sql = """
            SELECT posts.id, posts.content, posts.timestamp, posts.type, posts.user_id, posts.parent_id, users.username, users.profile_image
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            WHERE parent_id IS NOT NULL
        """
        params = ()
        comments = db.execute(sql, params).fetchall()
        # Check for when a post is deleted (comments will redirect to the main post page, but deleting a post redirects home)
        if not post:
            return redirect('/')
        
        return render_template("pages/post.jinja", post = post, likes = likes, liked_pairs=liked_pairs, comments=comments, back_url=f"/game/{post['game_id']}")

#-----------------------------------------------------------
# Like Post
#-----------------------------------------------------------
@login_required
@app.get("/post/<int:id>/like")
def like_post(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM likes  
            WHERE user_id = ? AND post_id = ?
        """
        params = (session.get("user")["user_id"], id)
        liked_posts = db.execute(sql, params).fetchall()

        if not liked_posts:
            sql = """
                INSERT INTO likes (user_id, post_id)
                VALUES (?, ?)
            """
            params = (session.get("user")["user_id"], id)
            db.execute(sql, params)
        else:
            flash(f"Already Liked", "error")

        return redirect(request.referrer or "/")
    
#-----------------------------------------------------------
# Unlike Post
#-----------------------------------------------------------
@login_required
@app.get("/post/<int:id>/unlike")
def unlike_post(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM likes  
            WHERE user_id = ? AND post_id = ?
        """
        params = (session.get("user")["user_id"], id)
        liked_posts = db.execute(sql, params).fetchall()

        if liked_posts:
            sql = """
                DELETE FROM likes WHERE user_id = ? AND post_id = ?
            """
            params = (session.get("user")["user_id"], id)
            db.execute(sql, params)
        else:
            flash(f"Already Unliked", "error")

        return redirect(request.referrer or "/")

#-----------------------------------------------------------
# Handle user comment
#-----------------------------------------------------------
@app.post("/post/<int:id>/comment")
def post_comment(id):
    comment = request.form.get('comment', '').strip()
    
    with connect_db() as db:
        sql = """
            INSERT INTO posts (content, timestamp, parent_id, user_id, type)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (comment, str(datetime.now()), id, session.get("user")["user_id"], 'comment')
        db.execute(sql, params)       
        flash(f"Comment Posted", "success")
        return redirect(request.referrer or "/")
    

#-----------------------------------------------------------
# Delete Post page
#-----------------------------------------------------------
@app.get("/post/<int:id>/delete")
@login_required
def delete_post(id):
    with connect_db() as db:
        sql = """
            SELECT *
            FROM posts WHERE user_id = ? AND id =?
        """
        params = (session.get("user")["user_id"], id)
        post = db.execute(sql, params).fetchone()

        if  post:
            sql = """
                DELETE FROM posts WHERE id = ?
            """
            params = (id,)
            db.execute(sql, params)

            imgs = find_trix_images(post['content'])
            for img in imgs:
                delete_image(img)
        
            flash("Deleted Post", "success")
        else:
            flash("Invalid action", "error")
    return redirect(request.referrer or "/")

#-----------------------------------------------------------
# Create Post page
#-----------------------------------------------------------
@app.get("/post/new/")
@app.get("/post/new/<int:id>")
@login_required
def new_post_form(id=None):
    with connect_db() as db:
            sql = """
                SELECT name
                FROM games
                WHERE id = ?
            """
            params = (id,)
            game_name = db.execute(sql, params).fetchone()

            sql = """
                SELECT id, name
                FROM games
                WHERE developer_id = ?
            """
            params = (session.get("user")["user_id"],)
            games = db.execute(sql, params).fetchall()
    return render_template("pages/post_form.jinja", game_id=id, game_name=game_name, games=games)

#-----------------------------------------------------------
# Handle Post Creation
#-----------------------------------------------------------
@app.post("/post/create/<int:id>")
def process_new_post(id):
    title = request.form.get('title', '').strip()
    raw_content = request.form.get('content', '')
    post_type = request.form.get('type', None)
    game_id = request.form.get('game', None)

    content = sanitise_html(raw_content)

    with connect_db() as db:
        if game_id and post_type:
            sql = """
                INSERT INTO posts (title, content, timestamp, game_id, user_id, type)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (title, content, str(datetime.now()), game_id, session.get("user")["user_id"], post_type)
            db.execute(sql, params)
        else:
            sql = """
                INSERT INTO posts (title, content, timestamp, game_id, user_id, type)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (title, content, str(datetime.now()), id, session.get("user")["user_id"], "discussion")
            db.execute(sql, params)

        flash("Post posted.", "success")
        return redirect(f"/game/{id}")

#-----------------------------------------------------------
# Edit Post page
#-----------------------------------------------------------
@login_required
@app.get("/post/<int:id>/edit")
def edit_post_form(id):
    with connect_db() as db:
            sql = """
                SELECT posts.user_id, posts.id, posts.title, posts.content, posts.type, games.name, posts.type
                FROM posts
                INNER JOIN games ON posts.game_id = games.id
                WHERE posts.id = ?
            """
            params = (id,)
            post = db.execute(sql, params).fetchone()
            if session.get("user")["user_id"] != post["user_id"]:
                        flash("Invalid action", "error")
                        return redirect("/")

    return render_template("pages/post_edit_form.jinja", post=post)

#-----------------------------------------------------------
# Handle Post Edit
#-----------------------------------------------------------
@login_required
@app.post("/post/<int:id>/edit")
def edit_post_details (id):
    title = request.form.get('title', '').strip()
    raw_content = request.form.get('content', '')

    content = sanitise_html(raw_content)

    with connect_db() as db:
        sql = """
            SELECT *
            FROM posts WHERE user_id = ? AND id =?
        """
        params = (session.get("user")["user_id"], id)
        post = db.execute(sql, params).fetchone()

        if  post:
            old_imgs = set(find_trix_images(post['content']))
            new_imgs = set(find_trix_images(content))

            removed = old_imgs - new_imgs 

            for image in removed:
                delete_image(image)

            sql = """
                UPDATE posts SET title = ?, content = ? WHERE id =?
            """
            params = (title, content, id)
            post = db.execute(sql, params)

            flash("Post updated.", "success")
        return redirect(f"/post/{id}")

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
        """
        params = ()
        followed_games = db.execute(sql, params).fetchall()

        followed_pairs = [
            (game["user_id"], game["game_id"])
            for game in followed_games
        ]

        sql = """
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        return render_template("pages/profile.jinja", user = user, followed_pairs=followed_pairs, games = games, back_url=f"/")

#-----------------------------------------------------------
# Edit Profile page
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

            if user and username.lower() != (session["user"].get("username")).lower():
                flash(f"Username '{username}' already exists", "error")
                return redirect(f"/user/profile/{id}")
 
            if image_file:
                unique_filename = process_image(image_file, UPLOAD_FOLDER, max_dimension=400, square=True, allow_gif=False)
                if unique_filename is None:
                    flash("That image couldn't be used. Please upload a JPG, PNG, WEBP or GIF.", "error")
                    return redirect("/user/profile/<int:id>")
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
# Developer Dash page
#-----------------------------------------------------------
@login_required
@app.get("/developer")
def show_dev_dash():
    if not session.get("user")["is_dev"]:
        flash("Invalid  Action", "error")
        return redirect(request.referrer or "/")
    with connect_db() as db:
        sql = """
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
            WHERE games.developer_id = ?
            ORDER BY games.id DESC;
        """
        params = (session.get("user")["user_id"],)
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE posts.user_id = ?
            ORDER BY posts.id DESC
        """
        params = (session.get("user")["user_id"],)
        posts = db.execute(sql, params).fetchall()

        sql = """
            SELECT parent_id
            FROM posts
            WHERE type = 'comment'
        """
        params = ()
        comments = db.execute(sql, params).fetchall()

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

        liked_pairs = [
            (like["user_id"], like["post_id"])
            for like in likes
        ]
        
        return render_template("pages/dev_dashboard.jinja", games=games, posts = posts, comments=comments, followed_pairs=followed_pairs, liked_pairs = liked_pairs, back_url=f"/")

#-----------------------------------------------------------
# Dev search request
#-----------------------------------------------------------
@app.get("/developer/search")
def dev_process_search():
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
            SELECT games.id, games.name, games.description, games.developer_id, games.image_name, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
            WHERE games.developer_id = ?
            ORDER BY games.id DESC;
        """
        params = (session.get("user")["user_id"],)
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT posts.id, posts.title, posts.content, posts.timestamp, posts.game_id, posts.type, posts.user_id, posts.parent_id, users.username, games.name
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            INNER JOIN games ON posts.game_id = games.id
            WHERE title LIKE ? AND posts.user_id = ?
            ORDER BY {sort} {dir}
        """.format(sort=sort, dir=dir)
        params = (search_match, session.get("user")["user_id"],)
        posts = db.execute(sql, params).fetchall()

        sql = """
            SELECT parent_id
            FROM posts
            WHERE type = 'comment'
        """
        params = ()
        comments = db.execute(sql, params).fetchall()
        
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

        liked_pairs = [
            (like["user_id"], like["post_id"])
            for like in likes
        ]

        return render_template("pages/dev_dashboard.jinja", games=games, posts = posts, followed_pairs=followed_pairs, liked_pairs = liked_pairs, comments=comments, search_term=search_term, sort_term=sort_term, back_url=f"/")


#-----------------------------------------------------------
# Delete User page
#-----------------------------------------------------------
@app.get("/user/<int:id>/delete")
@login_required
def delete_user(id):
    with connect_db() as db:
        if session.get("user")["user_id"] == id:
            sql = """
                SELECT profile_image
                FROM users
                WHERE id = ?  
            """
            params = (id,)
            user = db.execute(sql, params).fetchone()  
            if user["profile_image"] and user["profile_image"] != 'DefaultProfile.jpg':
                delete_image(user["profile_image"])

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
            unique_filename = process_image(image_file, UPLOAD_FOLDER, max_dimension=400, square=True, allow_gif=False)
            if unique_filename is None:
                flash("That image couldn't be used. Please upload a JPG, PNG, WEBP or GIF.", "error")
                return redirect("/user/new")
        else:
            unique_filename = 'DefaultProfile.jpg'
        

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

#-----------------------------------------------------------
# Handle User Log Out
#-----------------------------------------------------------
@login_required
@app.get("/logout")
def logout_user():
    session.clear()
    flash(f"You have been logged out", "success")
    return redirect("/")

#-----------------------------------------------------------
# Handle Switch for session
#-----------------------------------------------------------
@app.route('/save-checkbox', methods=['POST'])
def save_checkbox():
    data = request.get_json()
    
    # Store the boolean directly into the session
    session['show_games'] = data.get('checked', False)
    
    return jsonify({"status": "success", "session_state": session['show_games']})

#-----------------------------------------------------------
# Handle Trix Image Uploads
#-----------------------------------------------------------
@app.post("/upload-image")
def upload_image():
    file = request.files.get("file")
    if not file or not file.filename:
        abort(400)

    name = process_image(file, UPLOAD_FOLDER)
    if name is None:
        return jsonify(error="Invalid image"), 400

    return jsonify(url=url_for("static", filename=f"uploads/{name}"))

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