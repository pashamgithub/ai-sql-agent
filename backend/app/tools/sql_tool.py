import pandas as pd
from app.db.connection import get_connection
from app.core.logger import logger
import numpy as np
import time
#logger = get_logger(__name__)

class SQLTool:

    def __init__(self):
        self.conn = get_connection()
        logger.info("SQLTool initialized successfully")

    def clean_sql(self,query:str)-> str:
        if not query:
            return ""

        # Remove markdown code blocks safely
        query = query.replace("```sql", "")
        query = query.replace("```", "")

        return query.strip()


    def run(self, query:str,params=None):
        start_time = time.time()
        try:
            query = self.clean_sql(query) 
            if not query:
                logger.warning("Attempted to execute empty SQL query")
                return {
                    "status": "error",
                    "message": "Empty SQL query"
                }
            logger.info(f"Executing SQL:\n{query}")
            logger.info(f"SQL params: {params}")
            df = pd.read_sql_query(query,self.conn, params=params)
            df = df.replace([np.inf, -np.inf], None)
            df = df.fillna("")
            execution_time = round(time.time() - start_time,2)
            logger.info(
                f"SQL execution successful | "
                f"rows={len(df)} | "
                f"time={execution_time} sec"
            )
            return {
                "status":"success",
                "rows": df.to_dict(orient="records"),
                "row_count": len(df),
                "execution_time_sec": execution_time
            }
        except Exception as e:
            execution_time = round(time.time() - start_time,2)
            logger.exception("SQL execution failed")
            return {
                "status": "error",
                "message": str(e),
                "execution_time_sec": execution_time

            }
