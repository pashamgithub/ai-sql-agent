from app.agent.graph import graph
from app.core.logger import logger
import time


def process_query(question: str):
    logger.info(
        f"Processing query: {question}"
    )
    start_time = time.time()

    state = graph.invoke({
        "question": question,
        "chat_history": []
    })
    execution_time = round(
        time.time() - start_time,
        2
    )

    logger.info(
        f"Query completed in "
        f"{execution_time} sec"
    )

    return {
        "completed_steps": state.get("completed_steps"),
        "next_step": state.get("next_step"),
        "final_answer": state.get("final_answer"),
        "sql_query": state.get("sql_query"),
        "result": state.get("result"),
        "error": state.get("error"),
        "execution_time_sec": execution_time
    }
