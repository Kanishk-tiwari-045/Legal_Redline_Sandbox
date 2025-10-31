from sqlalchemy import text
from database import engine

def test_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful! Result:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed:", e)

if __name__ == "__main__":
    test_connection()