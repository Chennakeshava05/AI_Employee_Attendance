
from datetime import datetime

from database.db_connection import get_connection


def process_attendance_event(
        employee_id,
        event_type,
        has_bag,
        event_time=None,
):
    """
    Process a simulated entrance or exit event.

    Rules:
    - ENTRY: before 12 PM, with a bag.
    - EXIT: at or after 12 PM, with a bag.
    - Other events are ignored.
    - Duplicate entries are prevented while a session is open.
    """

    if event_time is None:
        event_time = datetime.now()

    event_type = event_type.upper()

    if event_type not in ("ENTRY", "EXIT"):
        return False, "Invalid event type."

    # Apply the manager's initial business rules.
    if not has_bag:
        return False, "Event ignored: bag condition not satisfied."

    if event_type == "ENTRY" and event_time.hour >= 12:
        return False, "Entry ignored: entry must occur before noon."

    if event_type == "EXIT" and event_time.hour < 12:
        return False, "Exit ignored: departure must occur after noon."

    connection = get_connection()
    cursor = None

    try:
        connection.start_transaction()
        cursor = connection.cursor()

        # Check whether this employee already has an open session.
        cursor.execute(
            """
            SELECT session_id
            FROM attendance_sessions
            WHERE employee_id = %s AND status = 'OPEN'
            ORDER BY entry_time DESC
                LIMIT 1
            FOR UPDATE
            """,
            (employee_id,),
        )

        open_session = cursor.fetchone()

        if event_type == "ENTRY":
            if open_session:
                connection.rollback()
                return False, "Entry ignored: employee is already present."

            cursor.execute(
                """
                INSERT INTO attendance_events
                    (employee_id, event_type, event_time, source)
                VALUES (%s, 'ENTRY', %s, 'SIMULATION')
                 """,
                (employee_id, event_time),
            )

            cursor.execute(
                """
                INSERT INTO attendance_sessions
                    (employee_id, entry_time, status)
                VALUES (%s, %s, 'OPEN')
                """,
                (employee_id, event_time),
            )

            connection.commit()
            return True, "Employee entry recorded."

        # EXIT: an open session must exist.
        if not open_session:
            connection.rollback()
            return False, "Exit ignored: no open attendance session."

        session_id = open_session[0]

        cursor.execute(
            """
            INSERT INTO attendance_events
                (employee_id, event_type, event_time, source)
            VALUES (%s, 'EXIT', %s, 'SIMULATION')
            """,
            (employee_id, event_time),
        )

        cursor.execute(
            """
            UPDATE attendance_sessions
            SET exit_time = %s, status = 'CLOSED'
            WHERE session_id = %s
            """,
            (event_time, session_id),
        )

        connection.commit()
        return True, "Employee departure recorded."

    except Exception as error:
        connection.rollback()
        return False, f"Attendance processing failed: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


def get_attendance_events(limit=100):
    """Return the latest attendance events with employee details."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
                SELECT
                    ae.event_id,
                    e.employee_code,
                    e.full_name,
                    ae.event_type,
                    ae.event_time,
                    ae.source
                FROM attendance_events ae
                         JOIN employees e ON e.employee_id = ae.employee_id
                ORDER BY ae.event_time DESC
                    LIMIT %s \
                """

        cursor.execute(query, (limit,))
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_attendance_sessions(limit=100):
    """Return recent attendance sessions."""
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
                SELECT
                    s.session_id,
                    e.employee_code,
                    e.full_name,
                    s.entry_time,
                    s.exit_time,
                    s.status
                FROM attendance_sessions s
                         JOIN employees e ON e.employee_id = s.employee_id
                ORDER BY s.entry_time DESC
                    LIMIT %s \
                """

        cursor.execute(query, (limit,))
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_daily_summary(selected_date):
    """Get attendance totals for a selected date."""
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
                SELECT
                    (
                        SELECT COUNT(*)
                        FROM attendance_sessions
                        WHERE DATE(entry_time) = %s
                    ) AS entries_today,

                     (
                SELECT COUNT(DISTINCT employee_id)
                FROM attendance_sessions
                WHERE DATE(entry_time) = %s
                    ) AS employees_entered,

                    (
                SELECT COUNT(*)
                FROM attendance_sessions
                WHERE status = 'OPEN'
                    ) AS open_sessions,

                    (
                SELECT COUNT(*)
                FROM attendance_sessions
                WHERE DATE(exit_time) = %s
                    ) AS completed_today \
                """

        cursor.execute(
            query,
            (selected_date, selected_date, selected_date)
        )

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

