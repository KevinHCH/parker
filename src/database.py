import sqlite3


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=True)
        self.conn.execute("PRAGMA foreign_keys = 1")  # Enable foreign keys, if needed
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        """Create the messages table if it doesn't exist."""
        with self.conn:  # Using a context manager ensures the commit
            self.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                title TEXT,
                url TEXT UNIQUE,
                posted_at TEXT,
                price TEXT,
                job_type TEXT,
                duration TEXT,
                experience_level TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
            )

    def get_job(self, url: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE url = ?",
            (url,),
        )
        result = cursor.fetchone()
        conn.close()
        return result

    def save_job(self, job):
        with self.conn:
            self.cursor.execute(
                """
              INSERT OR IGNORE INTO jobs (category, title, url, posted_at, price, job_type, duration, experience_level, description)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
          """,
                (
                    job.category,
                    job.title,
                    job.url,
                    job.posted_at,
                    job.price,
                    job.job_type,
                    job.duration,
                    job.experience_level,
                    job.description,
                ),
            )
        return self.cursor.lastrowid

    def close(self):
        """Close the database connection."""
        self.conn.close()
