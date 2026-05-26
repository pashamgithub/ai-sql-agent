from app.llm.llm_client import generate_sql
from app.core.logger import logger

def planner_node(state):
    logger.info("\nPlanner node started")

    question    = state.get("question", "")
    history     = state.get("chat_history", [])
    error       = state.get("error")
    retry_count = state.get("retry_count", 0)
    retrieved   = state.get("retrieved_context")
    intent      = state.get("intent")
    filters     = state.get("filters", {})
    limit       = state.get("limit")
    sort        = state.get("sort")

    # ── LAYER 1: Rule-based routing (fast, free, deterministic) ──────────────

    # Rule 1 — Too many retries → stop immediately, no LLM call needed
    if retry_count >= 3:
        logger.info("Planner → END (retry limit reached)")
        return {
            "thought": "Retry limit reached. Stopping.",
            "action":  "END",
            "chat_history": [{"role": "user", "content": question}],
        }

    # Rule 2 — Schema not retrieved yet → always go to RAG first
    if not retrieved:
        logger.info("Planner → RAG (no schema in state yet)")
        return {
            "thought": "Schema not retrieved yet. Fetching via RAG.",
            "action":  "RAG",
            "chat_history": [{"role": "user", "content": question}],
        }

    # Rule 3 — Previous SQL error exists → retry SQL with error context
    if error:
        logger.info("Planner → SQL (retrying after error)")
        return {
            "thought": f"Previous error detected: {error}. Retrying SQL.",
            "action":  "SQL",
            "chat_history": [{"role": "user", "content": question}],
        }

    # Rule 4 — State already has full context → follow-up is always SQL
    has_full_context = intent and filters
    is_followup      = len(history) > 0
    short_followup_keywords = [
        "only", "sort", "top", "limit", "filter",
        "descending", "ascending", "asc", "desc"
    ]
    is_short_followup = (
        is_followup and
        any(kw in question.lower() for kw in short_followup_keywords)
    )

    if has_full_context and is_short_followup:
        logger.info("Planner → SQL (short follow-up with full context)")
        return {
            "thought": "Follow-up filter with full context in state. Routing to SQL.",
            "action":  "SQL",
            "chat_history": [{"role": "user", "content": question}],
        }



    routing_context = {
        "intent":  intent,
        "filters": filters,
        "limit":   limit,
        "sort":    sort,
    }

    prompt = f"""
You are an intelligent SQL routing agent.
Schema is already retrieved. Decide: SQL, RAG_ANSWER, or CLARIFY.

RULES:
1. Use chat history and structured state for context.
2. If question relates to analytics, filtering, aggregation,
   trends, counts, revenue, or follow-ups → SQL.
3. Use RAG_ANSWER if user is asking ABOUT the database structure:
   - "what columns exist in X table"
   - "which table stores X"
   - "describe the schema"
   - "what tables are available"
   Answer comes from retrieved schema, not the database.
4. Use CLARIFY only if the question is completely impossible
   to resolve even with chat history and state context.

STRUCTURED STATE:
{routing_context}

CHAT HISTORY:
{history}

CURRENT QUESTION:
{question}

Return ONLY:
THOUGHT: <your reasoning>
ACTION: SQL/RAG_ANSWER/CLARIFY
"""

    response = generate_sql(prompt)
    logger.info("Planner LLM response:", response)

    thought = ""
    action  = "CLARIFY"  # safe default

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("THOUGHT:"):
            thought = line.replace("THOUGHT:", "").strip()
        if line.startswith("ACTION:"):
            action = line.replace("ACTION:", "").strip().upper()  # normalise case

    # Guard against unexpected LLM output
    if action not in ("SQL", "CLARIFY"):
        logger.info(f"Planner → unexpected action '{action}', defaulting to CLARIFY")
        action = "CLARIFY"

    logger.info(f"Planner → {action} | Thought: {thought}")

    return {
        "thought":      thought,
        "action":       action,
        "chat_history": [{"role": "user", "content": question}],
    }