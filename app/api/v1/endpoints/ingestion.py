from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, status, Form
from typing import Optional
from app.ingestion.service import IngestionService
from app.ingestion.models import IngestionResponse, IngestionStatus

router = APIRouter()
ingestion_service = IngestionService()

@router.post("/file", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: Optional[str] = Form("Uncategorized")
):
    try:
        content = await file.read()
        task_id = await ingestion_service.process_file(content, file.filename, category=category)
        
        # Pass actual processing to background task
        background_tasks.add_task(
            ingestion_service.process_background, 
            task_id, 
            content, 
            file.filename,
            category
        )
        
        return IngestionResponse(
            task_id=task_id,
            status=IngestionStatus.PENDING,
            message="File accepted for background processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
