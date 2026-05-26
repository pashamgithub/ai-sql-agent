import operator

from typing import Annotated, TypedDict, Optional, List

class AgentState(TypedDict):
    # user input
    question : str

    # Memory
    chat_history: Annotated[List[dict], operator.add] 
    

    # routing
    thought: Optional[str]
    action: Optional[str]
    #observation: Optional[str]
    # planner 
    required_table: Optional[List[str]]
    join_path: Optional[str]
    intent_summary: Optional[str]

    #sql

    sql_query: Optional[str]
    db_schema: Optional[str]

    #rag
    retrieved_context: Optional[str]
    source_docs: Optional[list]

    #excution
    result: Optional[dict]

    #recovery
    error: Optional[str]
    retry_count: Optional[int]

    # Structured query state
    filters: Annotated[dict,operator.or_]

    intent: Optional[str]
   
    limit: Optional[int]
    sort:Optional[str]

    # gaurdrails
    is_safe_input: Optional[bool]
    guardrail_reason: Optional[str]
    validation_errors:Optional[List[str]]

    execution_plan:  Optional[dict]  
    completed_steps: Optional[list]   
    next_step:       Optional[str]    
    final_answer: Optional[str]
