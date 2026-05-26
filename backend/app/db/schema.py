from app.db.connection import get_connection

def get_schema():
    conn = get_connection()
    cursor  = conn.cursor()

    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()

    schema_text  = ""
    for table in tables:
        table_name = table[0]

        columns = cursor.execute(
            f"PRAGMA table_info({table_name});"
        ).fetchall()

        cols = [col[1] for col in columns]

        schema_text += f"{table_name}({', '.join(cols)})\n"

    return schema_text


