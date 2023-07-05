import sqlite3
import json

class AllFreeNovelsDB:
    def __init__(self, db):
        self.db = db
        self.books_table = 'books'
        self.pages_table = 'pages'
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db)
        self.cursor = self.conn.cursor()
        self.cursor.row_factory = sqlite3.Row
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def get_all_books(self):
        self.cursor.execute(f"SELECT * FROM {self.books_table}")
        return self.cursor.fetchall()
    
    def count_all_books(self):
        self.cursor.execute(f"SELECT COUNT(ID) FROM {self.books_table}")
        return self.cursor.fetchone()['COUNT(ID)']
    
    def count_all_books_with_infos(self):
        self.cursor.execute(f"SELECT COUNT(ID) FROM {self.books_table} WHERE INFO IS NOT NULL")
        return self.cursor.fetchone()['COUNT(ID)'] 

    def get_all_books_with_no_info(self):
        self.cursor.execute(f"SELECT * FROM {self.books_table} WHERE INFO IS NULL")
        return self.cursor.fetchall()
    
    def get_all_books_with_info(self):
        self.cursor.execute(f"SELECT * FROM {self.books_table} WHERE INFO IS NOT NULL")
        return self.cursor.fetchall()
    
    def count_saved_pages(self, book_id: int):
        self.cursor.execute(f"SELECT COUNT(ID) FROM {self.pages_table} WHERE BOOK_ID=?", [book_id])
        return self.cursor.fetchone()['COUNT(ID)']

    def is_page_saved(self, url: str):
        self.cursor.execute(f"SELECT ID FROM {self.pages_table} WHERE URL=?", [url])
        return True if self.cursor.fetchone() else False 

    def save_book_url(self, url: str, genre: str):
        self.cursor.execute(f"INSERT OR IGNORE INTO {self.books_table}(URL, GENRE) VALUES(?, ?)", [url, genre])

    def save_book_urls(self, urls: list):
        self.cursor.executemany(f"INSERT OR IGNORE INTO {self.books_table}(URL, GENRE) VALUES(?, ?)", urls)
    
    def save_book_info(self, book_id: int, info: str):
        self.cursor.execute(f"UPDATE {self.books_table} SET INFO=? WHERE ID=?", [info, book_id])

    def save_book_page(self, book_id: int, url: str, text: str):
        self.cursor.execute(f"INSERT OR IGNORE INTO {self.pages_table}(URL, TEXT, BOOK_ID) VALUES(?, ?, ?)", [url, text, book_id])
    
    def is_book_pages_complete(self, book_id: int):
        self.cursor.execute(f"SELECT * FROM {self.books_table} WHERE ID=?", [book_id])
        book = self.cursor.fetchone()
        book_info = json.loads(book['INFO'])
        pages = self.cursor.execute(f"SELECT COUNT(ID) FROM {self.pages_table} WHERE BOOK_ID=?", [book_id])['COUNT(ID)']
        if book_info['pages'] != pages:
            return False
        return True
