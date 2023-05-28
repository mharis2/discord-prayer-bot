import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('server_configs.db')

# Create a cursor object
cursor = conn.cursor()

# Create the server_configs table
cursor.execute('''
    CREATE TABLE server_configs (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        city TEXT,
        country TEXT,
        timezone TEXT
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()
