import sqlite3

def migrate():
    conn = sqlite3.connect("games_platform.db")
    cursor = conn.cursor()
    
    try:
        print("Adding 'settings' column to 'chats' table...")
        cursor.execute("ALTER TABLE chats ADD COLUMN settings JSON DEFAULT '{}'")
        conn.commit()
        print("Migration successful!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'settings' already exists.")
        else:
            print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
