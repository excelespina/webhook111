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
                    sunday_service_likelihood INTEGER,
                    bible_study_likelihood INTEGER,
                    bible_talk_likelihood INTEGER
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

def message_exists(recipient_id, content, created_time):
    global db_pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM messages
                WHERE recipient_id = %s AND content = %s AND created_time = %s
                """,
                (recipient_id, content, created_time),
            )
            result = cursor.fetchone()
            return result[0] > 0
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
            message_history = [{"role": "system", "content": os.environ.get('CHATBOT_ENGINE_PROMPT_WITH_PERCENT')}]
            for row in reversed(rows):  # Reverse the order of the rows to have them in ascending order
                message_history.append({"role": row[1], "content": row[0]})
    finally:
        db_pool.putconn(conn)
    return message_history

def update_likelihood(recipient_id, likelihood_data):
    global db_pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET sunday_service_likelihood = %s, bible_study_likelihood = %s, bible_talk_likelihood = %s
                WHERE recipient_id = %s
                """,
                (likelihood_data["sunday_service"], likelihood_data["bible_study"], likelihood_data["bible_talk"], recipient_id),
            )
            conn.commit()
    finally:
        db_pool.putconn(conn)

def delete_user_data(recipient_id):
    with db_pool.getconn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM messages WHERE recipient_id = %s", (recipient_id,))
            cursor.execute("DELETE FROM users WHERE recipient_id = %s", (recipient_id,))
            conn.commit()
        db_pool.putconn(conn)