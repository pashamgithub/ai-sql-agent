from app.db.schema import get_schema
from app.llm.prompt_builder import build_sql_prompt
from app.llm.llm_client import generate_sql
from app.tools.sql_tool import SQLTool
from app.utils.sql_cleaner import clean_sql
import re
from app.core.logger import logger


sql_tool = SQLTool()


def validate_params(sql: str, params: dict) -> list[str]:
    """Guard 1 — SQL has :key placeholder but params has no value for it."""
    placeholders = set(re.findall(r':(\w+)', sql))
    missing      = placeholders - set(params.keys())
    return list(missing)


def validate_filters_in_sql(sql: str, filters: dict) -> list[str]:
    """Guard 2 — filters has a key but SQL has no :key placeholder for it."""
    missing = []
    for key in filters:
        if f":{key}" not in sql:
            missing.append(key)
    return missing


def sql_node(state):
    logger.info("\nSQL node started")

    # Get schema — from state if already fetched, else fetch fresh
    schema = state.get("db_schema") or get_schema()

    # Use retry's corrected SQL if available — otherwise generate fresh
    existing_sql = state.get("sql_query")
    if existing_sql:
        logger.info("Using corrected SQL from retry")
        sql_query = existing_sql
    else:
        logger.info("Generating SQL from prompt")
        prompt    = build_sql_prompt(state, schema)
        sql_query = clean_sql(generate_sql(prompt))

    logger.info("Generated SQL:")
    logger.info(sql_query)

    # Build params from state
    filters = state.get("filters") or {}
    limit   = state.get("limit")
    params  = dict(filters)
    params["limit"] = limit if limit is not None else 100

    logger.info("SQL params:", params)

    # Guard 0 — remove non-primitive param values (dict, list)
    # Catches: {"duration": {"gt": 300}} from bad filter extraction
    invalid_types = [
        key for key, val in params.items()
        if isinstance(val, (dict, list))
    ]
    if invalid_types:
        logger.info(f"Warning: removing non-primitive params: {invalid_types}")
        for key in invalid_types:
            params.pop(key)
            filters.pop(key, None)
        logger.info(f"Cleaned params: {params}")

    # Guard 1 — SQL has :key but params has no value
    missing = validate_params(sql_query, params)
    if missing:
        error_msg = (
            f"SQL contains placeholders {missing} "
            f"but state filters are {filters}. "
            f"Remove WHERE conditions for: {missing}. "
            f"Only use placeholders that exist in filters dict."
        )
        logger.info("Guard 1 failed:", error_msg)
        return {
            "error":       error_msg,
            "result":      None,
            "sql_query":   None,
            "retry_count": state.get("retry_count", 0),
        }

    # Guard 2 — filters has key but SQL doesn't use it
    missing_filters = validate_filters_in_sql(sql_query, filters)
    if missing_filters:
        error_msg = (
            f"Active filters {missing_filters} not applied in SQL. "
            f"Add WHERE clause using named placeholders: "
            + ", ".join(f":{k}" for k in missing_filters)
        )
        logger.info("Guard 2 failed:", error_msg)
        return {
            "error":       error_msg,
            "result":      None,
            "sql_query":   sql_query,
            "retry_count": state.get("retry_count", 0),
        }

    # Execute
    result = sql_tool.run(sql_query, params)
    #logger.info("\nSQL execution result:")
    #logger.info(result)

    completed = list(state.get("completed_steps") or [])
    completed.append("sql")

    return {
        "db_schema":       schema,
        "sql_query":       sql_query,
        "result":          result,
        "error":           None if result.get("status") == "success"
                           else result.get("message"),
        "retry_count":     (0 if result.get("status") == "success" else state.get("retry_count", 0)),
        "completed_steps": completed,
    }