from fastapi import APIRouter
from app.models.request_models import QueryRequest
from app.services.query_service import process_query
from app.core.logger import logger
import time

router = APIRouter()

@router.get("/")
def health():
    logger.info("Health check endpoint called")
    return {"status": "running"}

@router.post("/query")
def query(request: QueryRequest):
    start_time = time.time()
    logger.info(
        f"Incoming query request: "
        f"{request.question}"
    )
    try:
        response = process_query(request.question)
        execution_time = round(time.time() - start_time,2)
        logger.info(f"Query completed successfully " f"in {execution_time} sec")
        response["execution_time_sec"] = execution_time

        return response
    
    except Exception as e:
        logger.exception(
            "Unhandled exception in /query endpoint")
        return {
            "status": "error",
            "message": str(e)
        }
    