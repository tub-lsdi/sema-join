from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from typing import Optional

from backend.models.uploaded_table import (
    UploadedTableDetail,
    UploadTableResponse,
    TablesListResponse,
)
from backend.services import AppDatabaseService


router = APIRouter(prefix="/tables", tags=["tables"])


@router.post("/upload", response_model=UploadTableResponse)
async def upload_table(
    request: Request,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    db_service: AppDatabaseService = request.app.state.app_database_service

    # Try UTF-8 first, fallback to latin-1
    file_bytes = await file.read()
    try:
        content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = file_bytes.decode("latin-1")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File encoding not supported. Please use UTF-8 or Latin-1 encoded files.",
            )

    try:
        return db_service.upload_table(content, file.filename or "", name, description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("", response_model=TablesListResponse)
async def get_tables(request: Request):
    db_service: AppDatabaseService = request.app.state.app_database_service
    try:
        return db_service.list_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{table_id}", response_model=UploadedTableDetail)
async def get_table(request: Request, table_id: int):
    db_service: AppDatabaseService = request.app.state.app_database_service

    try:
        result = db_service.get_table_detail(table_id)
        if not result:
            raise HTTPException(status_code=404, detail="Table not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{table_id}")
async def delete_table_endpoint(request: Request, table_id: int):
    db_service: AppDatabaseService = request.app.state.app_database_service

    try:
        if not db_service.delete_table(table_id):
            raise HTTPException(status_code=404, detail="Table not found")
        return {"message": "Table deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
