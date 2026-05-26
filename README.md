# AI SQL Agent — Supervised Multi-Agent NL-to-SQL

<img width="885" height="963" alt="image" src="https://github.com/user-attachments/assets/fb3a55b1-866b-4ffc-aa96-4292b3c66bbc" />


## What it does
Converts natural language to validated SQL using a 
supervised multi-agent architecture. Serves non-technical 
teams on enterprise database without SQL knowledge.

## Architecture

supervisor → executor → [rag] → state_update → sql → answer

4 query types:
SCHEMA_QUERY  → schema questions answered from RAG
RAG_THEN_SQL  → first query: fetch schema then SQL
DATA_QUERY    → follow-up: SQL directly  
CLARIFY       → ambiguous: ask user

## Performance
First-attempt accuracy: X% across 16 test queries
Average latency: 3-5 seconds


| Metric | Result |
|--------|--------|
| First-attempt SQL accuracy | 87%+ across 16 test queries |
| Average latency | 3-8 seconds per query |
| Test database | Chinook (11 tables, ~15K rows) |
| Production target | 50GB enterprise DB (25 tables, 10M+ records) |

## Key Engineering Decisions

### Supervised over ReAct
Planner creates full execution plan once.
Executor follows fixed steps.
Predictable, debuggable, auditable.

### Multi-hop RAG retrieval
5 separate ChromaDB searches per query
(patterns, joins, tables, gotchas, metrics).
Retrieves 9 targeted chunks vs 5 generic chunks.
Eliminates hallucinated JOIN paths.

### Named parameters (:key)
Eliminates parameter order bugs.
Filter values validated before DB execution.

### Three-layer SQL validation
Guard 0: non-primitive param types removed
Guard 1: placeholder-param mismatch caught
Guard 2: active filters not applied caught

## Bugs Found and Fixed
1. sql_params accumulation — operator.add on list
2. Silent routing failure — missing .upper()
3. WHERE 1=1 hallucination — prompt engineering
4. RAG dead-end — RAG→END not RAG→SQL
5. CLARIFY unhandled — silent drop to END
6. Infinite retry loop — no exit condition
7. Non-primitive filter params — dict→SQLite crash
8. sql_query bleeding across turns — supervisor reset
9. retrieved_context not passed to LLM — biggest fix
10. Vector DB wrong doc_types — section tracking

## Tech Stack
LangGraph · FastAPI · ChromaDB · Streamlit
Groq LLaMA 3.3 70B · SQLite · Python 3.11

## How to Run
git clone https://github.com/yourusername/sql-agent
cd sqlagent/backend
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
python -m uvicorn app.main:app --reload
# Open new terminal
streamlit run frontend/app.py

## Author
Pasham Thirumal Reddy | Hyderabad, India
[https://www.linkedin.com/in/p-thirumal-reddy-9431b6182/] | [thirumalreddy0172@gmail.com]
