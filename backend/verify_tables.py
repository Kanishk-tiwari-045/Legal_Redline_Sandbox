from sqlalchemy import create_engine, inspect
from database import DATABASE_URL  # or however you defined it

# Create engine
engine = create_engine(DATABASE_URL)

# Use inspector to check tables
inspector = inspect(engine)
tables = inspector.get_table_names()

if tables:
    print("✅ Tables found in Cloud SQL:")
    for table in tables:
        print("-", table)
else:
    print("⚠️ No tables found in the database.")