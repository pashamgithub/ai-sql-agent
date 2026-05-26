def build_sql_prompt(state, schema):

    filters = state.get("filters") or {}
    limit   = state.get("limit")
    sort    = state.get("sort")
    intent    = state.get("intent")
    retrieved = state.get("retrieved_context", "")

    sql_context = {
        "intent":  intent,
        "filters": filters,
        "limit":   limit,
        "sort":    sort,
    }

    # Make filter state unmistakably clear
    if filters:
        filter_instruction = (
            f"ACTIVE FILTERS: {filters}\n"
            f"You MUST add WHERE clause for every key in filters.\n"
            f"Use named placeholder matching the key exactly:\n"
            f"country → WHERE c.Country = :country\n"
            f"genre   → WHERE g.Name = :genre\n"
            f"Never use WHERE 1=1 or WHERE 1 or WHERE true.\n"
            f"Never omit the WHERE clause when filters are active."
        )
    else:
        filter_instruction = (
            "NO ACTIVE FILTERS: filters dict is empty {}.\n"
            "Do NOT add any WHERE clause.\n"
            "Do not use WHERE 1=1, WHERE 1, or WHERE true.\n"
            "Do not copy WHERE clauses from examples.\n"
            "Do not add :country, :age, or any filter placeholder.\n"
            "Omit WHERE clause entirely."
        )

    return f"""
You are a SQLite expert.
Generate parameterized SQLite SQL using structured state.

STRICT RULES:
1. Use ONLY tables and columns from schema.
2. Return ONLY SQL — no explanation, no markdown.
3. Use SQLite named placeholders (:key).
4. Never inject literal values.
5. Use LIMIT :limit only if limit is not None.
6. Clause order: SELECT → FROM → JOIN → WHERE → GROUP BY → ORDER BY → LIMIT
7. Never put ORDER BY before GROUP BY.
8. Customer revenue = SUM(i.Total) from Invoice — never use InvoiceLine for customer-level revenue.
9. Never use WHERE 1=1, WHERE 1, or WHERE true under any circumstance.
10. Generate SQL that matches the intent in Structured State — do not default to a customer spending query.
11. Follow the Relevant Context patterns exactly if provided — use the same JOIN chains and column names shown there.

FILTER RULE — THIS OVERRIDES ALL EXAMPLES:
{filter_instruction}

RELEVANT CONTEXT — USE THIS TO WRITE CORRECT SQL:
{retrieved if retrieved else "No context retrieved."}

Structured State:
{sql_context}

Schema:
{schema}
"""