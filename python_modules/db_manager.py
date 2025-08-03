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
            self.conn = sqlite3.connect(self.db_path)
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
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    appid INTEGER PRIMARY KEY,  
                    name TEXT NOT NULL,               
                    install_path TEXT, 
                    cover_thumbnail_path TEXT, 
                    cover_detail_path TEXT,
                    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
            print("Table 'games' checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def add_or_update_game(self, game_info):
        if not self.conn:
            print("Cannot add/update game: no database connection.")
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO games (appid, name, install_path, cover_thumbnail_path, cover_detail_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                game_info.get('appid'),
                game_info.get('name'),
                game_info.get('full_install_path'),
                game_info.get('cover_thumbnail_path'),
                game_info.get('cover_detail_path')
            ))
            self.conn.commit()
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
        
    def close(self):
        if self.conn:
            self.conn.close()
            print("database connection closed.")
            self.conn = None

def get_db_manager(db_name="games.db"):
    data_dir = Path.home() / ".EchoGL"
    db_file = data_dir / db_name
    return DBManager(db_file)

if __name__ == "__main__":
    print("--- Testing DBManager ---")
    db = get_db_manager()

    game1 = {'appid': 123, 'name': 'Test Game 1', 'full_install_path': 'C:/Games/Test1', 
             'cover_thumbnail_path': 'path/to/thumb1.jpg', 'cover_detail_path': 'path/to/detail1.jpg'}
    game2 = {'appid': 456, 'name': 'Test Game 2', 'full_install_path': 'C:/Games/Test2', 
             'cover_thumbnail_path': 'path/to/thumb2.jpg', 'cover_detail_path': 'path/to/detail2.jpg'}
    game3 = {'appid': 789, 'name': 'Test Game 3', 'full_install_path': 'C:/Games/Test3', 
             'cover_thumbnail_path': 'path/to/thumb3.jpg', 'cover_detail_path': 'path/to/detail3.jpg'}

    db.add_or_update_game(game1)
    db.add_or_update_game(game2)
    db.add_or_update_game(game3)

    game1_updated = {'appid': 123, 'name': 'Test Game 1 (Updated)', 'full_install_path': 'D:/Games/Test1', 
                     'cover_thumbnail_path': 'path/to/thumb1_new.jpg', 'cover_detail_path': 'path/to/detail1_new.jpg'}
    db.add_or_update_game(game1_updated)

    all_games = db.get_all_games()
    print("\nAll games in DB:")
    for game in all_games:
        print(f"AppID: {game['appid']}, Name: {game['name']}, Path: {game['install_path']}")

    fetched_game = db.get_game_by_appid(123)
    print(f"\nFetched game 123: {fetched_game['name']} at {fetched_game['install_path']}")

    db.close()
    print("--- DBManager Test Complete ---")