from app.llm.llm_client import generate_sql as call_llm
from app.core.logger import logger

SCHEMA_KEYWORDS = [
    "which table", "what table", "what column", "which column",
    "what columns", "schema", "table definition", "relationship",
    "foreign key", "primary key", "join path", "describe",
    "how are tables", "what is the structure", "metadata",
    "what does the", "which tables", "how does",
]

SHORT_FOLLOWUP_KEYWORDS = [
    "only", "sort", "top", "limit", "filter",
    "descending", "ascending", "asc", "desc",
    "by country", "by year", "by month", "by genre",
]

PLANS = {
    "SCHEMA_QUERY": {
        "steps":       ["rag", "rag_answer","answer"],
        "max_retries": 0,
    },
    "RAG_THEN_SQL": {
        "steps":       ["rag", "state_update", "sql", "answer"],
        "max_retries": 3,
    },
    "DATA_QUERY": {
        "steps":       ["state_update", "sql","answer"],
        "max_retries": 3,
    },
    "CLARIFY": {
        "steps":       ["clarify","answer"],
        "max_retries": 0,
    },
}


def supervisor_node(state):
    logger.info("\nSupervisor node started")

    question  = state.get("question", "")
    history   = state.get("chat_history", [])
    retrieved = state.get("retrieved_context")
    q_lower   = question.lower()

    # Rule 1 — schema/metadata question → RAG only, no SQL needed
    if any(kw in q_lower for kw in SCHEMA_KEYWORDS):
        logger.info("Supervisor → SCHEMA_QUERY")
        return {
            "thought":         "Question is about schema or table structure — routing to RAG for a direct answer.",
            "action":          "SCHEMA_QUERY",
            "completed_steps": [],
            "next_step":       None,
            "sql_query": None,
            "execution_plan":  {
                "question_type": "SCHEMA_QUERY",
                "steps":         PLANS["SCHEMA_QUERY"]["steps"],
                "max_retries":   PLANS["SCHEMA_QUERY"]["max_retries"],
            },
            "chat_history":    [{"role": "user", "content": question}],
        }

    # Rule 2 — no schema context in state yet → fetch via RAG, then run SQL
   # Rule 2 — no schema context in state yet
    if not retrieved:

        # Validate if question is a real data query before fetching schema
        validation_prompt = f"""
            You are a query classifier.
            Return ONLY the single word DATA or CLARIFY.
            No explanation. No punctuation. No other words.

            DATA    = valid database question (customers, sales,
                    revenue, tracks, artists, genres, employees,
                    invoices, playlists, albums, spending, count,
                    top, show, list, how many, which, who)
            CLARIFY = gibberish, unclear, or unrelated question

            Question: {question}
            """
        validation = call_llm(validation_prompt).strip().upper()
        logger.info(f"Supervisor Rule 2 validation: {validation!r}")

        if "CLARIFY" in validation:
            logger.info("Supervisor → CLARIFY (invalid data question)")
            return {
                "thought":         "Question is not a recognisable data query.",
                "action":          "CLARIFY",
                "completed_steps": [],
                "next_step":       None,
                "sql_query": None,
                "execution_plan":  {
                    "question_type": "CLARIFY",
                    "steps":         PLANS["CLARIFY"]["steps"],
                    "max_retries":   PLANS["CLARIFY"]["max_retries"],
                },
                "chat_history": [{"role": "user", "content": question}],
            }

        # Valid data question — fetch schema first, then run SQL
        logger.info("Supervisor → RAG_THEN_SQL (no retrieved_context)")
        return {
            "thought":         "Valid data question. Schema not yet retrieved — fetching via RAG first.",
            "action":          "RAG_THEN_SQL",
            "completed_steps": [],
            "next_step":       None,
            "sql_query": None,
            "execution_plan":  {
                "question_type": "RAG_THEN_SQL",
                "steps":         PLANS["RAG_THEN_SQL"]["steps"],
                "max_retries":   PLANS["RAG_THEN_SQL"]["max_retries"],
            },
            "chat_history": [{"role": "user", "content": question}],
        }

    # Rule 3 — short follow-up with history → straight to SQL
    is_followup = len(history) > 0
    is_short    = any(kw in q_lower for kw in SHORT_FOLLOWUP_KEYWORDS)

    if is_followup and is_short:
        logger.info("Supervisor → DATA_QUERY (short follow-up)")
        return {
            "thought":         "Short follow-up question with existing chat history — routing directly to SQL.",
            "action":          "DATA_QUERY",
            "completed_steps": [],
            "next_step":       None,
            "sql_query": None,
            "execution_plan":  {
                "question_type": "DATA_QUERY",
                "steps":         PLANS["DATA_QUERY"]["steps"],
                "max_retries":   PLANS["DATA_QUERY"]["max_retries"],
            },
            "chat_history":    [{"role": "user", "content": question}],
        }

    # Rule 4 — LLM decides between DATA_QUERY and CLARIFY
    routing_context = {
        "intent":  state.get("intent"),
        "filters": state.get("filters", {}),
        "limit":   state.get("limit"),
        "sort":    state.get("sort"),
    }

    prompt = f"""
You are a SQL routing supervisor.
Schema is already retrieved. Choose: DATA_QUERY or CLARIFY.

DATA_QUERY — question asks for data:
analytics, filtering, aggregation, counts, revenue, top N,
comparisons, trends, customer data, spending.

CLARIFY — question is completely unresolvable even with
chat history and state. Use very rarely.

Never choose RAG — schema is already available.

STRUCTURED STATE:
{routing_context}

CHAT HISTORY:
{history}

CURRENT QUESTION:
{question}

Return ONLY:
THOUGHT: <one line reasoning>
ACTION: DATA_QUERY/CLARIFY
"""

    response = call_llm(prompt)
    logger.info("Supervisor LLM response:", response)

    thought = ""
    action  = "CLARIFY"

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("THOUGHT:"):
            thought = line.replace("THOUGHT:", "").strip()
        if line.startswith("ACTION:"):
            action = line.replace("ACTION:", "").strip().upper()

    if action not in ("DATA_QUERY", "CLARIFY"):
        logger.info(f"Supervisor → unexpected '{action}', defaulting to CLARIFY")
        action = "CLARIFY"

    logger.info(f"Supervisor → {action} | Thought: {thought}")

    return {
        "thought":         thought,
        "action":          action,
        "completed_steps": [],
        "next_step":       None,
        "sql_query": None,
        "execution_plan":  {
            "question_type": action,
            "steps":         PLANS[action]["steps"],
            "max_retries":   PLANS[action]["max_retries"],
        },
        "chat_history":    [{"role": "user", "content": question}],
    }
