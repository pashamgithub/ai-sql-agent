from langgraph.graph import (
    StateGraph,
    END
)

from app.agent.state import AgentState

from app.nodes.supervisor_node import supervisor_node
from app.nodes.executor_node   import executor_node
from app.nodes.sql_node import sql_node
from app.nodes.retry_node import retry_node
from app.nodes.rag_node import rag_node
from app.nodes.state_update_node import state_update_node
from app.llm.llm_client import generate_sql
from app.nodes.answer_synthesiser_node import answer_synthesiser_node
from app.core.logger import logger


builder = StateGraph(AgentState)

def clarify_node(state):
    logger.info(
    "Clarify node triggered "
    f"for question: {state.get('question')}")
    completed = list(state.get("completed_steps") or [])
    completed.append("clarify")
    return {
        "result": {
            "status":    "clarify",
            "rows":      [],
            "row_count": 0,
            "message":   None,
            "answer":    state.get("thought", "Could you please provide more details?")
        },
        "error":           None,
        "completed_steps": completed,
    }
def rag_answer_node(state):       
    context  = state.get("retrieved_context", "")
    question = state.get("question", "")
    logger.info( "RAG answer node generating " "schema-only response")
    logger.debug(f"Retrieved context length: " f"{len(context)}")
    prompt = f"""
Answer this question using only the schema context below.
Be concise and specific.

Context:
{context}

Question: {question}

Return a direct answer only.
"""
    answer = generate_sql(prompt)

    completed = list(state.get("completed_steps") or [])
    completed.append("rag_answer")

    return {
        "result": {
            "status":    "rag_answer",
            "rows":      [],
            "row_count": 0,
            "answer":    answer,
            "message":   None,
        },
        "error":           None,
        "completed_steps": completed,
    }

def executor_router(state):
    next_step = state.get("next_step", "END")
    logger.info(
        f"Executor router ---> next_step: {next_step}"
    )
    valid = {"rag", "rag_answer", "state_update", "sql", "clarify", "answer"}
    if next_step not in valid:
        logger.error( f"Unknown graph transition: {next_step}")
    if next_step in valid:
        return next_step
   
    return END

def sql_router(state):
    error       = state.get("error")
    retry_count = state.get("retry_count", 0)
    plan        = state.get("execution_plan", {})
    max_retries = plan.get("max_retries", 3)
    logger.info(
        f"SQL router | "
        f"retry_count={retry_count} | "
        f"max_retries={max_retries} | "
        f"error={error}"
    )

    if error and retry_count < max_retries:
        logger.warning(
            f"Routing to retry node "
            f"(attempt {retry_count + 1})"
        )
        return "retry"
    logger.info("Routing back to executor")
    return "executor"

# Nodes
logger.info("Initializing workflow nodes")
builder.add_node("supervisor",   supervisor_node)
builder.add_node("executor",     executor_node)
builder.add_node("state_update", state_update_node)
builder.add_node("sql",          sql_node)
builder.add_node("retry",        retry_node)
builder.add_node("rag",          rag_node)
builder.add_node("clarify",      clarify_node)
builder.add_node("rag_answer",   rag_answer_node)
builder.add_node("answer", answer_synthesiser_node)

# Entry
builder.set_entry_point("supervisor")

# Edges
builder.add_edge("supervisor", "executor")

builder.add_conditional_edges(
    "executor",
    executor_router,
    {
        "rag":          "rag",
        "rag_answer":   "rag_answer",
        "state_update": "state_update",
        "sql":          "sql",
        "clarify":      "clarify",
        "answer":       "answer", 
        END:            END,
    }
)

builder.add_edge("rag",          "executor")
builder.add_edge("rag_answer",   "executor")
builder.add_edge("state_update", "executor")
builder.add_edge("clarify",      "executor")
builder.add_edge("answer", "executor")


builder.add_conditional_edges(
    "sql",
    sql_router,
    {
        "retry":    "retry",
        "executor": "executor",
    }
)

builder.add_edge("retry", "sql")
logger.info("Workflow edges configured")

graph = builder.compile()
logger.info("Workflow ready for execution")