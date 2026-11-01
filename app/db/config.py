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
            profile_image           TEXT,
            bio                     TEXT,
            is_developer            INTEGER DEFAULT 0
        )
    """

    SEED_DATA = """
        INSERT INTO users (username, pass_hash, profile_image, bio, is_developer)
        VALUES
            ("Dudeman", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "dudeman.jpg", "I am Dudeman, the greatest dude to exist. Professional prompt engineer and League player.", 0),
            ("Testman", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "testman.png", "I am Testman, the greatest tester to exist. Professional tester and player of good games (not league).", 0),
            ("FastTurnipGames", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "fastturnip.jpg", "I am Turnip, the greatest Turnip to exist. Professional Game Developer and Turnip.", 1),
            ("MidnightSunStudios", "scrypt:32768:8:1$n7eJTucLbaGmUpAM$c1776374a8d456a6eaf61bccc08db5e1fcc4ff3b3983d364c45ab13074255eeae0a393afb11f99a9fe63fb1d980992ace17a72ba70324523b11e92e36cbe4252", "midnightsun.png", "I am Sun, the greatest Midnight to exist. Professional Game Developer and yeah.", 1)
    """

class GamesTable:

    NAME = "games"

    SCHEMA = """
        CREATE TABLE games (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            name                    TEXT NOT NULL,
            description             TEXT NOT NULL,
            image_name              TEXT NOT NULL,
            developer_id            INTEGER NOT NULL,

            FOREIGN KEY(developer_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """

    SEED_DATA = """
        INSERT INTO games (name, description, image_name, developer_id)
        VALUES
            ("Nutdealer", "Nutdealer is the critically acclaimed game that jesus himself ressurected to play. You are the Nutdealer. After the devastating news that you have nut cancer you decide to start an business in the illegal nut trade. You must grow nuts and deal them to your customers, balancing keeping a thriving empire of dealing nuts while not becoming too notorious that the feds catch you.", "NutHero.png", 3),
            ("Flopparena", "Flopparena is a physics based fighting game set in a tabletop board game", "FlopHero.jpg", 4),
            ("Drunkpocalypse", "Drunkpocalypse is a physics based fighting game about repairing your car and espacing the zombie apocalypse before a nuke hits", "DrunkHero.jpg", 3),
            ("Dreamweave", "Dreamweave is an exploration adventure game about uncovering the remains of an abandoned city and an extinct civilisation taken over by some strange infection.", "DreamHero.png", 4)
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

            FOREIGN KEY(game_id)    REFERENCES games(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id)  REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id)    REFERENCES users(id) ON DELETE CASCADE
        )
    """

    SEED_DATA = """
        INSERT INTO posts (title, content, timestamp, game_id, parent_id, user_id, type)
        VALUES
            ("NUTDEALER 3D ANNOUNCEMENT", '<div>After weeks of wait...</div><div>Rumours have circled for the past few days, the globe has been quietly waiting, hoping...<br><br>And finally, after hours of intense development, we are proud to announce...<br><br></div><h1>NUTDEALER 3D</h1><div><figure class="attachment attachment--preview attachment--png"><a href="/static/uploads/9af36281bfb74fff8fce0c588410af0e.webp" rel="noopener noreferrer nofollow"><img src="/static/uploads/9af36281bfb74fff8fce0c588410af0e.webp" width="887" height="838"><figcaption>Screenshot 2026-04-03 165830.png 444.35 KB</figcaption></a></figure><br>Nutdealer 3D, the standalone sequel to the critically acclaimed game that jesus himself ressurected for to play. Developed in Grok Engine and making use of the latest vibe coding and asset generation technology. We have poured our lives and soul into the 13 days spend developing this game, and the several minutes of playtesting and bugfixing we have done to deliver the greatest game in the history of the universe to you!<br><br><strong>NOW, THE NITTY GRITTY:<br></strong>We don''t have a confirmed release date yet, due to the intesive care we are using to make a good game, however you can expect it in the later half of tomorrow as a general goal for release.<br><br>It has very low system requirements, which are listed below:</div><ul><li>CPU - Ryzen Threadripper</li><li>GPU - RTX 5090</li><li>RAM - 64 GB DDR5</li><li>300GB of free space</li><li>Arch Linux operating system</li></ul><div>These specs are so low because of our specialised optimising using entirely grok written code, allowing the game to be as accessible to as many billionares as possible.<br><br>We will accept out nobel prize next week (:</div>', "2026-05-1", 1, NULL ,3, "announcement"),
            ("Rat Expansion Update", "<div>The Rat Expansion is finally out!<br><strong>New Content:</strong></div><div><ul><li>New area (Sewers)</li><li>New missions</li><li>New characters</li><li>Various Bug Fixes</li><li>Cheese</li></ul></div>", "2026-5-7", 1, NULL, 3, "major update"),
            ("Flopparena Patch v1.5", "Fixed the crashes finally", "2026-05-15", 2, NULL ,4, "update"),
            ("Flopparena 2 Speculation", "Its not happening bruh", "2026-08-1", 2, NULL ,4, "news"),
            ("How do I play?", "I failed kindergarten and can't figure out how to press the play button can someone please explain?", "2026-08-11", 1,NULL ,1, "discussion"),
            (NULL, "Wow this is so cool.", "2026-07-12",NULL ,1,1, "comment"),
            (NULL, "Nutdealer made me leave my wife.", "2026-08-1",NULL ,1,2, "comment"),
            (NULL, "Hi, its the developer! You can play the game by pressing play.", "2026-10-09 22:23:18.618417",NULL ,5,3, "comment"),
            (NULL, "oh thanks", "2026-10-09 22:23:44.194723",NULL ,9,1, "comment"),
            ("Expansion Coming Soon", "<div>An expansion for Drunkpocalypse is nearly here!<br>You can expect:</div><ul><li>Dark souls rolling</li><li>Parrying</li><li>Varied Zombies</li><li>Procedural Map Generation</li></ul>", "2026-10-12", 3, NULL,3, "news")
    """

class MediaTable:

    NAME = "media"

    SCHEMA = """
        CREATE TABLE media (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            image_file              TEXT NOT NULL,
            game_id                 INTEGER NOT NULL,

            FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
        )
    """

    SEED_DATA = """
        INSERT INTO media (image_file, game_id)
        VALUES
            ("NutScreenshot1.png", 1),
            ("NutScreenshot2.png", 1),
            ("NutScreenshot3.png", 1),
            ("NutScreenshot4.png", 1),
            ("FlopScreenshot1.png", 2),
            ("FlopScreenshot2.png", 2),
            ("DrunkScreenshot1.png", 3),
            ("DrunkScreenshot2.png", 3),
            ("DrunkScreenshot3.png", 3),
            ("DreamScreenshot1.png", 4),
            ("DreamScreenshot2.png", 4),
            ("DreamScreenshot3.png", 4)
    
    """

class LinksTable:

    NAME = "links"

    SCHEMA = """
        CREATE TABLE links (
            id                           INTEGER PRIMARY KEY AUTOINCREMENT,
            link                         TEXT NOT NULL,
            game_id                      INTEGER,
            
            FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
        )
    """

    SEED_DATA = """
        INSERT INTO links (link, game_id)
        VALUES
            ("https://fasrturnipgames.itch.io/nutdealer-legacy" ,1),
            ("https://store.steampowered.com/app/2115500/Flopparena/", 2),
            ("https://fasrturnipgames.itch.io/drunkpocalypse", 3),
            ("https://www.youtube.com/watch?v=xvFZjo5PgG0", 4)

          
    """

class LikesTable:

    NAME = "likes"

    SCHEMA = """
        CREATE TABLE likes (
            user_id                      INTEGER,
            post_id                      INTEGER,
            
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,

            PRIMARY KEY (user_id, post_id)
        )
    """

    SEED_DATA = """
        INSERT INTO likes (user_id, post_id)
        VALUES
            (1,1),
            (1,4),
            (1,8),
            (2,1),
            (2,3)

            
    """

class FollowTable:

    NAME = "following"

    SCHEMA = """
        CREATE TABLE following (
            user_id                      INTEGER,
            game_id                      INTEGER,
            
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,

            PRIMARY KEY (user_id, game_id)
        )
    """

    SEED_DATA = """
        INSERT INTO following (user_id, game_id)
        VALUES
            (1,1),
            (1,2),
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
    UserTable, GamesTable, PostsTable, MediaTable, LikesTable, FollowTable, LinksTable
    # Add more tables here...
]

