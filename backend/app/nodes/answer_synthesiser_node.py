from app.llm.llm_client import generate_sql
import logging


def answer_synthesiser_node(state):
    logging.info("\n Answer synthesiser started")

    result = state.get("result") or {}
    rows = result.get("rows",[])
    question = state.get("question","")
    sql      = state.get("sql_query", "")
    action   = state.get("action", "")

    if action in ("CLARIFY", "clarify"):
        answer = result.get("answer", 
                 "Could you please provide more details?")
        
    elif action in ("SCHEMA_QUERY", "rag_answer"):
        answer = result.get("answer","Schema information retrieved.")
    elif not rows:
        answer = "No results found for your query."

    else:
        prompt = f"""
Convert these database query results into a clear, 
concise natural language answer.

Question asked: {question}

SQL executed: {sql}

Results ({result.get("row_count", 0)} rows): 
{rows[:5]}

Rules:
- Be concise — 2-3 sentences maximum
- Mention the key numbers or top results
- If more than 5 rows, mention total count
- Never mention SQL or technical details
- Sound like a business analyst, not an engineer
"""
        answer = generate_sql(prompt)

    completed = list(state.get("completed_steps") or [])
    completed.append("answer")

    return {
        "final_answer":  answer,
        "completed_steps": completed,
        "chat_history":  [{"role": "assistant", "content": answer}],
    }



