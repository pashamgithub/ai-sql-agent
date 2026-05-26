import streamlit as st
from api_client import ask_agent
from components.result_table import render_result_table

st.set_page_config(
    page_title="AI SQL Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI SQL Agent")

st.markdown(
    "Ask questions in natural language."
)

question = st.text_input(
    "Enter your question",
    placeholder="Top 5 artists by revenue"
)

submit = st.button("Submit")


if submit and question:

    with st.spinner("Agent is thinking..."):

        response = ask_agent(question)

    if response.get("error"):
        st.error(response["error"])

    else:

        # =========================
        # Final Answer
        # =========================
        st.subheader("Final Answer")

        st.write(response.get("final_answer"))

        # =========================
        # SQL Query
        # =========================
        st.subheader("Generated SQL")

        st.code(
            response.get("sql_query", ""),
            language="sql"
        )

        # =========================
        # Steps
        # =========================
        st.subheader("Execution Steps")

        steps = response.get("completed_steps", [])

        st.write(" → ".join(steps))

        # =========================
        # Results Table
        # =========================
        st.subheader("Query Results")

        result = response.get("result", {})

        rows = result.get("rows", [])

        render_result_table(rows)

        # =========================
        # Metadata
        # =========================
        st.subheader("Metadata")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Rows Returned",
                result.get("row_count", 0)
            )

        with col2:
            st.metric(
                "Status",
                result.get("status", "unknown")
            )