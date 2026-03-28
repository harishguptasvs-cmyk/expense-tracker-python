import sqlite3

# Connect to database (this will create file if not exists)
conn = sqlite3.connect("expenses.db")

# Create cursor
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT
)
""")

# Save changes
conn.commit()

# Close connection
conn.close()

print("Database created successfully!")
