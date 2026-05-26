from app.llm.llm_client import generate_sql
import json
from app.core.logger import logger


def state_update_node(state):
    logger.info("\nState update node started")

    question = state["question"]

    prompt = f"""
You are a query state extractor.
Extract structured query information.
Return ONLY valid JSON.

CRITICAL RULE — Filter values must be primitive types only
(string, number). Never use nested dicts.
For range conditions like "longer than", "more than",
"before", "after", "greater than" — do NOT extract as filter.
Return only the intent instead.

Wrong: {{"filters": {{"duration": {{"gt": 300}}}}}}
Right: {{"intent": "track_duration_filter"}}

Allowed fields: intent, filters, limit, sort

Examples:

Question: Top 5 customers by spending
Output: {{"intent":"customer_spending","limit":5}}

Question: Only Germany
Output: {{"filters":{{"country":"Germany"}}}}

Question: Sort descending
Output: {{"sort":"DESC"}}

Question: How many tracks longer than 5 minutes
Output: {{"intent":"track_duration_filter"}}

Question: Only India
Output: {{"filters":{{"country":"India"}}}}

Current Question: {question}
"""

    response = generate_sql(prompt)
    logger.info("Extractor output:", response)

    try:
        updates = json.loads(response)
       
    except Exception:
        updates = {}
 

    # Merge new filters into existing state filters
    existing_filters = dict(state.get("filters", {}))
    new_filters = updates.get("filters", {})
    existing_filters.update(new_filters)

    # Preserve previous state values if LLM didn't return them
    intent = updates.get("intent", state.get("intent"))
    limit  = updates.get("limit",  state.get("limit"))
    sort   = updates.get("sort",   state.get("sort"))

    logger.info("Updated filters:", existing_filters)

    completed = list(state.get("completed_steps") or [])
    completed.append("state_update")

    return {
        "filters":         existing_filters,
        "intent":          intent,
        "limit":           limit,
        "sort":            sort,
        "completed_steps": completed,
    }

