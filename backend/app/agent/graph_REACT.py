# from langgraph.graph import StateGraph, END
# from agent.state import AgentState
# from nodes.planner import planner_node
# from nodes.sql_node import sql_node
# from nodes.retry_node import retry_node
# from nodes.rag_node import rag_nodes
# from nodes.state_update_node import state_update_node

# builder = StateGraph(AgentState)
# def planner_router(state):

#     if state['action']=='SQL':
#         return "state_update"
#     if state['action'] == 'RAG':
#         return "rag"
#     return END
# def sql_router(state):
#     if state['error']:
#         return "retry"
#     return END

# builder.add_node("planner",planner_node)
# builder.add_node("state_update",state_update_node)
# builder.add_node("sql",sql_node)
# builder.add_node("retry",retry_node)
# builder.add_node("rag", rag_nodes)

# builder.set_entry_point("planner")



# #builder.add_conditional_edges("planner",planner_router)
# builder.add_conditional_edges(
#     "planner",
#     planner_router,
#     {
#         "state_update":"state_update",
#         "rag":"rag",
#         END: END
#     }
# )
# builder.add_edge("state_update","sql")
# builder.add_conditional_edges(
#     "sql",
#     sql_router,
#     {
#         "retry":"retry",
#         END: END
#     }
# )

# builder.add_edge("retry","sql")
# #builder.add_conditional_edges("sql",sql_router)

# builder.add_edge("rag",END)

# graph = builder.compile()
# print(graph.get_graph().draw_mermaid())
# # graph.get_graph().draw_png(

# #     "agent_graph.png"
# # )
from langgraph.graph import (
    StateGraph,
    END
)

from agent.state import AgentState

from nodes.planner import planner_node
from nodes.sql_node import sql_node
from nodes.retry_node import retry_node
from nodes.rag_node import rag_node
from nodes.state_update_node import state_update_node
from llm.llm_client import generate_sql



builder = StateGraph(AgentState)

def clarify_node(state):
    return {
        "result": {
            "status":  "clarify",
            "rows":[],
            "row_count":0,
            "message": None,
            "answer":  state.get("thought", "Could you please provide more details?")
        },
        "error": None
    }
def rag_answer_node(state):       # ← add this right after clarify_node
    context  = state.get("retrieved_context", "")
    question = state.get("question", "")

    prompt = f"""
Answer this question using only the schema context below.
Be concise and specific.

Context:
{context}

Question: {question}

Return a direct answer only.
"""
    answer = generate_sql(prompt)

    return {
        "result": {
            "status":    "rag_answer",
            "rows":      [],
            "row_count": 0,
            "answer":    answer,
            "message":   None,
        },
        "error": None,
    }

def planner_router(state):
    action = state.get("action", "").upper()
    if action == "SQL":        return "state_update"
    if action == "RAG":        return "rag"         
    if action == "RAG_ANSWER": return "rag_answer"  
    if action == "CLARIFY":    return "clarify"
    return END

def sql_router(state):
    error = state.get("error")
    retry_count = state.get("retry_count",0)
    if error and retry_count<3:
        return "retry"
    return END

def rag_router(state):
    return "state_update"

# Nodes

builder.add_node("planner",planner_node)

builder.add_node("state_update",state_update_node)

builder.add_node("sql", sql_node)

builder.add_node( "retry", retry_node)

builder.add_node("rag",rag_node)

builder.add_node("clarify", clarify_node)

builder.add_node("rag_answer",rag_answer_node)

# Edges

builder.set_entry_point("planner")

builder.add_conditional_edges(
    "planner",
    planner_router,
    {
        "state_update":"state_update",
        "rag":"rag",
        "clarify":"clarify",
        "rag_answer":   "rag_answer",
        END: END
    }
)

builder.add_edge( "state_update", "sql")

builder.add_conditional_edges(
    "sql",
    sql_router,
    {
        "retry":"retry",
        END: END
    }
)



builder.add_edge( "retry", "sql")

builder.add_edge("rag","state_update")

builder.add_edge("rag_answer", END)
builder.add_edge("clarify",END)

graph = builder.compile()