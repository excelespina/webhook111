import os
import psycopg2
from psycopg2 import pool

db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, os.environ.get('DATABASE_URL'))
    
def init_db():
    global db_pool
    with db_pool.getconn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    recipient_id BIGINT PRIMARY KEY,
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
                    FOREIGN KEY (recipient_id) REFERENCES users (recipient_id)
                );
                """
            )
            conn.commit()
            db_pool.putconn(conn)

def store_message(recipient_id, user_message, assistant_message):
    with db_pool.getconn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (recipient_id, user_message, assistant_message) VALUES (%s, %s, %s)",
                (recipient_id, user_message, assistant_message),
            )
            conn.commit()
        db_pool.putconn(conn)

def fetch_messages(recipient_id):
    with db_pool.getconn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_message, assistant_message FROM messages WHERE recipient_id = %s ORDER BY id",
                (recipient_id,),
            )
            rows = cursor.fetchall()
            message_history = [{"role": "system", "content": os.environ.get('CHATBOT_ENGINE_PROMPT')}]
            for row in rows:
                message_history.append({"role": "user", "content": row[0]})
                message_history.append({"role": "assistant", "content": row[1]})
            db_pool.putconn(conn)
        return message_history

def update_likelihood(recipient_id, likelihood):
    with db_pool.getconn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET likelihood = %s WHERE recipient_id = %s",
                (likelihood, recipient_id),
            )
            conn.commit()
            db_pool.putconn(conn)