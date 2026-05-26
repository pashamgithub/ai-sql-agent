from app.llm.llm_client import generate_sql
from app.utils.sql_cleaner import clean_sql
from app.core.logger import logger


def retry_node(state):
    logger.info("\nRetry node started")

    retry_count  = state.get("retry_count", 0)
    previous_sql = state.get("sql_query")
    error        = state.get("error", "")
    question     = state.get("question", "")
    intent       = state.get("intent", "")
    filters      = state.get("filters", {})
    limit        = state.get("limit")

    # Build named params context for LLM
    params = dict(filters)
    if limit is not None:
        params["limit"] = limit
    else:
        params["limit"] = 100

    # Handle case where sql_query was cleared (None)
    if previous_sql:
        sql_section = f"Previous SQL to fix:\n{previous_sql}"
    else:
        sql_section = (
            "No previous SQL available — generate fresh correct SQL.\n"
            f"Previous attempt failed with: {error}"
        )

    prompt = f"""
You generated invalid SQLite SQL. Fix it.

Original question: {question}
Original intent:   {intent}

{sql_section}

Error to fix:
{error}

Available named params:
{params}

Schema:
{state.get("db_schema", "")}

STRICT RULES:
1. Use ONLY tables and columns from schema.
2. SQLite syntax only — use LIMIT not TOP.
3. Return ONLY SQL — no explanation, no markdown.
4. Clause order: SELECT → FROM → JOIN → WHERE → GROUP BY → ORDER BY → LIMIT
5. Preserve the original query structure and joins.
6. Fix ONLY the specific error — do not change business logic.
7. Never use WHERE 1 or WHERE 1=1.

PARAMETER RULES:
8. Use SQLite named placeholders (:key).
9. Only add WHERE clause for filters in params above.
10. If error says "Remove WHERE conditions for [x]" →
    DELETE that WHERE condition entirely.
11. If error says "Active filters [x] not applied" →
    ADD WHERE clause using :filter_name placeholder.
12. Never replace placeholders with literal values.
"""

    corrected_sql = clean_sql(generate_sql(prompt))
    logger.info("Corrected SQL:", corrected_sql)

    return {
        "sql_query":   corrected_sql,
        "error":       None,
        "retry_count": retry_count + 1,
    }