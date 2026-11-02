import sqlite3
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def init_db():
    conn = sqlite3.connect("database.db")
    with open("banco.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    senha = bcrypt.generate_password_hash("senha123").decode("utf-8")
    conn.execute(
        "INSERT OR IGNORE INTO logs (username, password_hash) VALUES (?, ?)",
        ("admin", senha))
    conn.commit()
    conn.close()
    print("Banco inicializado!")

if __name__ == "__main__":
    init_db()

