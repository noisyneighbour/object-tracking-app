import psycopg2
import os
from urllib.parse import urlparse

def get_db_connection():
    p = urlparse(os.getenv("DATABASE_URL"))
    
    pg_connection_dict = {
        'dbname': p.path[1:],
        'user': p.username,
        'password': p.password,
        'port': p.port,
        'host': p.hostname
    }
    
    return psycopg2.connect(**pg_connection_dict)
