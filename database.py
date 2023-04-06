import os
import psycopg2
from psycopg2 import pool

db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, os.environ.get('DATABASE_URL'))
    
def init_db():
    global db_pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    recipient_id BIGINT PRIMARY KEY,
                    created_time TIMESTAMPTZ DEFAULT NOW(),
                    likelihood VARCHAR(10)
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    recipient_id BIGINT,
                    role VARCHAR(10),
                    content TEXT,
                    created_time TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (recipient_id) REFERENCES users (recipient_id)
                );
                """
            )
            conn.commit()
    finally:
        db_pool.putconn(conn)

def store_message(recipient_id, message, type):
    global db_pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            # Check if the user exists
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE recipient_id = %s",
                (recipient_id,),
            )
            user_exists = cursor.fetchone()[0] > 0

            # If the user doesn't exist, create a new user entry
            if not user_exists:
                cursor.execute(
                    "INSERT INTO users (recipient_id) VALUES (%s)",
                    (recipient_id,),
                )
            cursor.execute(
                "INSERT INTO messages (recipient_id, content, role) VALUES (%s, %s, %s)",
                (recipient_id, message, type),
            )
            conn.commit()
    finally:
        db_pool.putconn(conn)

def fetch_messages(recipient_id, n=20):
    global db_pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT content, role 
                FROM messages 
                WHERE recipient_id = %s 
                ORDER BY created_time DESC
                LIMIT %s""",
                (recipient_id, n),
            )
            rows = cursor.fetchall()
            message_history = [{"role": "system", "content": os.environ.get('CHATBOT_ENGINE_PROMPT')}]
            for row in reversed(rows):  # Reverse the order of the rows to have them in ascending order
                message_history.append({"role": row[1], "content": row[0]})
    finally:
        db_pool.putconn(conn)
    return message_history

def update_likelihood(recipient_id, likelihood):
    global db_pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET likelihood = %s WHERE recipient_id = %s",
                (likelihood, recipient_id),
            )
            conn.commit()
    finally:
        db_pool.putconn(conn)
