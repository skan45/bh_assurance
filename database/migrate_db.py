import psycopg2
import os
from dotenv import load_dotenv

# --- Connect to Postgres ---
conn = psycopg2.connect(
    dbname="bh_auth",
    user="bh_user",
    password="strong_password",
    host="localhost",
    port=5432
)
cur = conn.cursor()


# --- Create users table ---
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    ref_person BIGINT,             -- optional client reference number
    matricule_fiscale NUMERIC,     -- optional tax ID (can be very long)
    created_at TIMESTAMP DEFAULT NOW()
);
""")

# --- Create chats table ---
cur.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

# --- Create conversations table ---
cur.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    chat_id INT REFERENCES chats(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    category TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
""")

# --- Commit and close ---
conn.commit()
cur.close()
conn.close()

print("Migration complete ✅")

