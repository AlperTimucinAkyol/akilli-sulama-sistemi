import psycopg2
from psycopg2 import pool
from config import DB_CONFIG

# Global bir pool değişkeni tanımlıyoruz
connection_pool = None

def init_db():
    global connection_pool
    print("Veritabanı bağlantı havuzu oluşturuluyor...")
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1,      
        20,     
        **DB_CONFIG
    )

def close_db():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("Tüm veritabanı bağlantıları kapatıldı.")

def get_db_connection():
    return connection_pool.getconn()

def release_db_connection(conn):
    connection_pool.putconn(conn)