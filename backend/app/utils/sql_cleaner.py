import re

def clean_sql(response:str):

    # remov markdown
    response = response.replace("```sql", "")
    response = response.replace("```", "")
    # find firt select...until seicolon

    match = re.search(
        r"(SELECT.*?;|SELECT.*$)",
        response,
        re.IGNORECASE | re.DOTALL
    )
    if match:
        sql = match.group(1).strip()
        if not sql.endswith(";"):
            sql += ";"
        return sql
    raise ValueError("No valid SQL found")

