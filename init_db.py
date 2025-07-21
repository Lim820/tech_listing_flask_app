import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    type TEXT NOT NULL,
    address TEXT NOT NULL,
    description TEXT,
    area TEXT,
    photo TEXT,
    created_by TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS property_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    FOREIGN KEY(property_id) REFERENCES properties(id)
)
''')

# Add area and photo columns if they do not exist (for migration)
def add_column_if_not_exists(cursor, table, column, coltype):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

add_column_if_not_exists(cursor, 'properties', 'area', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'photo', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'listing_type', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'terrace_house_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'semi_d_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'bangalow_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'land_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'high_rise_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'residential_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'size_unit', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'commercial_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'factory_subtype', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'factory_building_type', 'TEXT')
add_column_if_not_exists(cursor, 'properties', 'created_at', 'TEXT')

add_column_if_not_exists(cursor, 'users', 'login_count', 'INTEGER DEFAULT 0')

cursor.execute('INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)', ('agent@example.com', '123456'))

conn.commit()
conn.close()

print("✅ Database initialized with users and properties table.")
