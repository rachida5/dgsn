# auth.py
def authenticate_user(cursor, username, password):
    if not cursor: return None
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    return cursor.fetchone()