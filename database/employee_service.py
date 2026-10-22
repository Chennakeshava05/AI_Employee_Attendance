
from database.db_connection import get_connection


def add_employee(employee_code, full_name, department):
    """Insert a new employee into MySQL."""
    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
                INSERT INTO employees (employee_code, full_name, department)
                VALUES (%s, %s, %s) \
                """

        cursor.execute(
            query,
            (employee_code, full_name, department)
        )

        connection.commit()
        return True, "Employee registered successfully!"

    except Exception as error:
        if connection.is_connected():
            connection.rollback()

        if "1062" in str(error):
            return False, "This employee code already exists."

        return False, f"Registration failed: {error}"

    finally:
        if connection.is_connected():
            connection.close()


def get_employees():
    """Fetch all employees from MySQL."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
                       SELECT employee_id, employee_code, full_name,
                              department, is_active, created_at
                       FROM employees
                       ORDER BY employee_id DESC
                       """)

        return cursor.fetchall()

    finally:
        connection.close()


def get_employee_count():
    """Count active employees."""
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM employees WHERE is_active = TRUE"
        )

        return cursor.fetchone()[0]

    finally:
        connection.close()

