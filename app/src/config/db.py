import sqlite3
import os
def __init__(self):
    self.conn = sqlite3.connect('database.db')
    self.cursor = self.conn.cursor()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'survey.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn