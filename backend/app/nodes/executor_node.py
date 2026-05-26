from app.core.logger import logger

def executor_node(state):
    plan      = state.get("execution_plan", {})
    steps     = plan.get("steps", [])
    completed = state.get("completed_steps") or []

    for step in steps:
        if step not in completed:
            logger.info(f"Executor → next step: {step}")
            return {"next_step": step}
    

    logger.info("Executor → all steps complete")
    return {"next_step": "END"}
