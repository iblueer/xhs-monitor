import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "notes.db"):
        """
        初始化数据库连接
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """
        初始化数据库表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS notes (
                    note_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    published_time TEXT,
                    discovered_time TEXT NOT NULL,
                    type TEXT,
                    last_like_count INTEGER
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS hot_gate_notifications (
                    note_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    like_count INTEGER NOT NULL,
                    notified_time TEXT NOT NULL
                )
                '''
            )
            self._ensure_column(cursor, 'notes', 'published_time', 'TEXT')
            self._ensure_column(cursor, 'notes', 'last_like_count', 'INTEGER')
            conn.commit()
    
    def add_note_if_not_exists(self, note_data: dict) -> bool:
        """
        添加笔记记录
        :param note_data: 笔记数据
        :return: 是否为新笔记
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT note_id FROM notes WHERE note_id = ?',
                (note_data.get('note_id'),),
            )
            exists = cursor.fetchone()

            published_time = note_data.get('published_time', note_data.get('time', ''))
            title = note_data.get('display_title', note_data.get('title', '无标题'))
            note_type = note_data.get('type', 'normal')
            user_id = note_data.get('user', {}).get('user_id')

            like_count = note_data.get('liked_count')
            if like_count is None:
                like_count = (note_data.get('note_card') or {}).get('liked_count')
            if like_count is None:
                like_count = (note_data.get('interact_info') or {}).get('liked_count')
            if isinstance(like_count, str) and like_count.isdigit():
                like_count = int(like_count)

            if exists:
                cursor.execute(
                    '''
                    UPDATE notes
                    SET user_id = ?, title = ?, published_time = ?, type = ?
                    WHERE note_id = ?
                    ''',
                    (user_id, title, published_time, note_type, note_data.get('note_id')),
                )
                if like_count is not None:
                    cursor.execute(
                        "UPDATE notes SET last_like_count = ? WHERE note_id = ?",
                        (like_count, note_data.get('note_id')),
                    )
                conn.commit()
                return False

            cursor.execute(
                '''
                INSERT INTO notes (
                    note_id, user_id, title, published_time, discovered_time, type, last_like_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
            , (
                note_data.get('note_id'),
                user_id,
                title,
                published_time,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                note_type,
                like_count
            ))
            conn.commit()
            return True
    
    def get_user_notes_count(self, user_id: str) -> int:
        """
        获取数据库中某用户的笔记数量
        :param user_id: 用户ID
        :return: 笔记数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            return count or 0

    def get_latest_note_time(self, user_id: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(published_time) FROM notes WHERE user_id = ?",
                (user_id,),
            )
            result = cursor.fetchone()[0]
            return result or ""

    def get_note_published_time(self, note_id: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT published_time FROM notes WHERE note_id = ?",
                (note_id,),
            )
            result = cursor.fetchone()
            if result:
                return result[0] or ""
            return ""

    def update_published_time(self, note_id: str, published_time: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE notes SET published_time = ? WHERE note_id = ?",
                (published_time, note_id),
            )
            conn.commit()

    def update_last_like_count(self, note_id: str, like_count: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE notes SET last_like_count = ? WHERE note_id = ?",
                (like_count, note_id),
            )
            conn.commit()

    def get_last_like_count(self, note_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_like_count FROM notes WHERE note_id = ?",
                (note_id,),
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            return None

    def mark_hot_gate_notified(self, note_id: str, user_id: str, like_count: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO hot_gate_notifications (
                    note_id, user_id, like_count, notified_time
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    note_id,
                    user_id,
                    like_count,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ),
            )
            conn.commit()

    def is_hot_gate_notified(self, note_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM hot_gate_notifications WHERE note_id = ?",
                (note_id,),
            )
            return cursor.fetchone() is not None

    def _ensure_column(self, cursor, table: str, column: str, column_type: str):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")