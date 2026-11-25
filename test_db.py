from sqlalchemy import text

from db_config import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Test result:", result.scalar())

    print("Successfully connected to MySQL!")

except Exception as error:
    print("Database connection failed!")
    print(error)