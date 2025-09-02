import os
from dotenv import load_dotenv
from databases import Database

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER","")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD","")
DB_NAME = os.getenv("POSTGRES_DB","")
DB_HOST = os.getenv("POSTGRES_HOST","")
DB_PORT = os.getenv("POSTGRES_PORT","")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

database = Database(DATABASE_URL)


