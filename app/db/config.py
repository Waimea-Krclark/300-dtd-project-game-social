#============================================================================
# Database schema and seed data configuration
#============================================================================


#----------------------------------------------------------------------------
# Table definitions
#----------------------------------------------------------------------------
# Define your tables with a name, a schema and optional seed/sample data,
# using this format, and then add the tables to the Table Registry below:
#
# class TableName:
#     NAME      = "name"
#     SCHEMA    = "CREATE TABLE name (...)"
#     SEED_DATA = "INSERT INTO name (...)" or None
#----------------------------------------------------------------------------

class UserTable:

    NAME = "users"

    SCHEMA = """
        CREATE TABLE users (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            username                TEXT NOT NULL,
            pass_hash               TEXT NOT NULL,
            profile_image_name      TEXT,
            bio                     TEXT,
            is_developer            INTEGER DEFAULT 0
        )
    """

    SEED_DATA = """
        INSERT INTO users (username, pass_hash, profile_image_name, bio, is_developer)
        VALUES
            ("Dudeman", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "dudeman.png", "I am Dudeman, the greatest dude to exist. Professional prompt engineer and League player.", 0),
            ("Testman", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "testman.png", "I am Testman, the greatest tester to exist. Professional tester and player of good games (not league).", 0),
            ("FastTurnipGames", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "fastturnip.png", "I am Turnip, the greatest Turnip to exist. Professional Game Developer and Turnip.", 1),
            ("MidnightSunStudios", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "fastturnip.png", "I am Sun, the greatest Midnight to exist. Professional Game Developer and yeah.", 1)
    """

class GamesTable:

    NAME = "games"

    SCHEMA = """
        CREATE TABLE games (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            name                    TEXT NOT NULL,
            description             TEXT NOT NULL,
            hero_image              TEXT NOT NULL,
            store_links             TEXT NOT NULL,
            developer_id            INTEGER NOT NULL,

            FOREIGN KEY(developer_id) REFERENCES users(id)
        )
    """

    SEED_DATA = """
        INSERT INTO games (name, description, hero_image, store_links, developer_id)
        VALUES
            ("Nutdealer", "Nutdealer is the critically acclaimed game that jesus himself ressurected to play. You are the Nutdealer. After the devastating news that you have nut cancer you decide to start an business in the illegal nut trade. You must grow nuts and deal them to your customers, balancing keeping a thriving empire of dealing nuts while not becoming too notorious that the feds catch you.", "nutdealer.png", "https://fasrturnipgames.itch.io/nutdealer-legacy", 3),
            ("Flopparena", "Floppy game", "flopparena.png", "floparena/download.com", 4)
    """

class PostsTable:

    NAME = "posts"

    SCHEMA = """
        CREATE TABLE posts (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            title                   TEXT,
            content                 TEXT NOT NULL,
            timestamp               TEXT NOT NULL,
            game_id                 INTEGER,
            parent_id               INTEGER,
            user_id                 INTEGER NOT NULL,
            type                    TEXT NOT NULL,

            FOREIGN KEY(game_id) REFERENCES games(id),
            FOREIGN KEY(parent_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """

    SEED_DATA = """
        INSERT INTO posts (title, content, timestamp, game_id, parent_id, user_id, type)
        VALUES
            ("NUTDEALER 3D ANNOUNCEMENT", "Nutdealer 3D, the standalone sequel to the critically acclaimed game that jesus himself ressurected for to play. Developed in Grok Engine and making use of the latest vibe coding and asset generation technology. We... Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin vitae turpis iaculis ligula ullamcorper volutpat vitae sit amet lectus. Integer a nibh quis sapien tristique lobortis quis viverra est. Curabitur sed tortor viverra, feugiat orci id, scelerisque mauris. Suspendisse consectetur quam id massa accumsan, et viverra ante tempus. Praesent eleifend est mauris, in eleifend nunc accumsan et. Morbi eu lacus rutrum mi pulvinar consequat posuere vitae enim. Donec non diam in metus gravida malesuada", "12/08/2026", 0, NULL ,3, "news"),
            ("How do I play?", "I failed kindergarten and can't figure out how to press the play button can someone please explain?", "12/08/2026", 0,NULL ,1, "discussion"),
            (NULL, "Wow this is so cool.", "12/08/2026",NULL ,1,1, "comment"),
            (NULL, "Nutdealer made me leave my wife.", "12/08/2026",NULL ,1,2, "announcement")
    """

class MediaTable:

    NAME = "media"

    SCHEMA = """
        CREATE TABLE media (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            image_file              TEXT NOT NULL,
            post_id                 INTEGER NOT NULL,

            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    """

    SEED_DATA = """
    
    """

class LikesTable:

    NAME = "likes"

    SCHEMA = """
        CREATE TABLE likes (
            user_id                      INTEGER,
            post_id                      INTEGER,
            
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(post_id) REFERENCES posts(id),

            PRIMARY KEY (user_id, post_id)
        )
    """

    SEED_DATA = """
        
            
    """

class FollowTable:

    NAME = "following"

    SCHEMA = """
        CREATE TABLE following (
            user_id                      INTEGER,
            game_id                      INTEGER,
            
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(game_id) REFERENCES games(id),

            PRIMARY KEY (user_id, game_id)
        )
    """

    SEED_DATA = """
        INSERT INTO following (user_id, game_id)
        VALUES
            (1,1),
            (2,1)
            
    """


#----------------------------------------------------------------------------
# Table registry
#----------------------------------------------------------------------------
# Register all of your tables by adding them to the TABLES list here:
#
# TABLES = [
#     Table1Name,
#     Table2Name,
#     etc.
# ]
#
# Note: The table order is important - Create the tables that have
# foreign keys *after* the tables they link to have been created
#----------------------------------------------------------------------------

TABLES = [
    UserTable, GamesTable, PostsTable, MediaTable, LikesTable, FollowTable
    # Add more tables here...
]

