
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# Load the .env file from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def get_connection():
    """Create and return a MySQL database connection."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "employee_attendance"),
        connection_timeout=5,
    )


if __name__ == "__main__":
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        database_name, mysql_version = cursor.fetchone()

        print("MySQL connection successful!")
        print(f"Database: {database_name}")
        print(f"MySQL version: {mysql_version}")

        cursor.close()

    except mysql.connector.Error as error:
        print(f"MySQL connection failed: {error}")

    finally:
        if connection is not None and connection.is_connected():
            connection.close()

