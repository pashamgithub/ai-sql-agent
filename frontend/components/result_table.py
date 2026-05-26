import pandas as pd
import streamlit as st


def render_result_table(rows):

    if not rows:
        st.warning("No rows returned")
        return

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True
    )