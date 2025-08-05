import sqlite3
from pathlib import Path

class DBManager:
    def __init__(self, db_path='games.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._connect()
        self._create_table()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None

    def _create_table(self):
        if not self.conn:
            print("Cannot create table: no database connection")
            return
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS games (
                        appid INTEGER PRIMARY KEY,
                        igdb_id INTEGER UNIQUE,
                        name TEXT NOT NULL,
                        summary TEXT,
                        genres TEXT,
                        platforms TEXT,
                        cover_path TEXT,
                        install_path TEXT,
                        cover_thumbnail_path TEXT,
                        cover_detail_path TEXT,
                        last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            print("Table 'games' checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            print("database connection closed.")
            self.conn = None

    def add_or_update_game(self, game_info):
        if not self.conn:
            print("Cannot add/update game: no database connection.")
            return
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO games (appid, name, install_path, cover_thumbnail_path, cover_detail_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    game_info.get('appid'),
                    game_info.get('name'),
                    game_info.get('full_install_path'),
                    game_info.get('cover_thumbnail_path'),
                    game_info.get('cover_detail_path')
                ))
        except sqlite3.Error as e:
            print(f"Error adding/updating game '{game_info.get('name')}': {e}")
            
    def get_all_games(self):
        if not self.conn:
            print("Cannot get games: no database connection.")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM games')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error fetching all games: {e}")
            return []

    def get_game_by_appid(self, appid):
        if not self.conn:
            print("Cannot get game: no database connection.")
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM games WHERE appid = ?', (appid,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error fetching game by appid {appid}: {e}")
            return None
            
    def update_game_metadata(self, appid, igdb_id, summary, genres, platforms, cover_path):
        if not self.conn:
            print("Cannot update game metadata: no database connection.")
            return
        
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE games 
                    SET igdb_id = ?, summary = ?, genres = ?, platforms = ?, cover_path = ?
                    WHERE appid = ?
                ''', (igdb_id, summary, genres, platforms, cover_path, appid))
            print(f"Metadata for appid {appid} updated successfully")
        except sqlite3.Error as e:
            print(f"Error updating metadata for appid {appid}: {e}")
            
    def update_game_covers(self, appid, thumbnail_path, detail_path):
        if not self.conn:
            print("Cannot update game covers: no database connection.")
            return
        
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE games 
                    SET cover_thumbnail_path = ?, cover_detail_path = ?
                    WHERE appid = ?
                ''', (thumbnail_path, detail_path, appid))
        except sqlite3.Error as e:
            print(f"Error updating covers for appid {appid}: {e}")

def get_db_manager(db_name="games.db"):
    data_dir = Path.home() / ".EchoGL"
    db_file = data_dir / db_name
    return DBManager(db_file)