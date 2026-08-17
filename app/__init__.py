#===========================================================
# PROJECT NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response
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
# Home page - Show all notes
#-----------------------------------------------------------
@app.get("/")
def show_notes():
    with connect_db() as db:
        show_games = 0
        sql = """
            SELECT games.id, games.name, games.description, games.store_links, games.developer_id, users.username
            FROM games
            INNER JOIN users ON games.developer_id = users.id
            ORDER BY name DESC;
        """
        params = ()
        games = db.execute(sql, params).fetchall()

        sql = """
            SELECT *
            FROM following  
        """
        params = ()
        followed_games = db.execute(sql, params).fetchall()

        sql = """
            SELECT *, users.username
            FROM posts
            INNER JOIN users ON posts.user_id = users.id
            ORDER BY title DESC
        """
        params = ()
        posts = db.execute(sql, params).fetchall()

        return render_template("pages/home.jinja", games=games, posts = posts, followed_games = followed_games, show_games = show_games)


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

