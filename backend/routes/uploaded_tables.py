from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from typing import Optional
import json

from backend.models.uploaded_table import (
    UploadedTableMetadata,
    UploadedTableDetail,
    UploadTableResponse,
    TablesListResponse,
)
from backend.persistence.uploaded_table import (
    create_uploaded_table,
    list_uploaded_tables,
    get_uploaded_table_by_id,
    delete_uploaded_table,
    get_uploaded_table_body,
)
from backend.utils.csv_parser import parse_csv_to_list_of_dicts


router = APIRouter(prefix="/tables", tags=["tables"])


@router.post("/upload", response_model=UploadTableResponse)
async def upload_table(
    request: Request,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    content = (await file.read()).decode("utf-8")
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".csv"):
            table_data = parse_csv_to_list_of_dicts(content)
        elif filename.endswith(".json"):
            table_data = json.loads(content)
            if not isinstance(table_data, list):
                raise ValueError("JSON must be an array of objects")
        else:
            raise ValueError("File must be CSV or JSON")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid file: {e}")

    Session = request.app.state.app_db_sessionmaker
    db_session = Session()
    try:
        table = create_uploaded_table(db_session, table_data, name, description)
        return UploadTableResponse(
            id=table.id, name=table.name, message=f"Uploaded {len(table_data)} rows"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    finally:
        db_session.close()


@router.get("", response_model=TablesListResponse)
async def get_tables(request: Request):
    Session = request.app.state.app_db_sessionmaker
    db_session = Session()

    try:
        tables = list_uploaded_tables(db_session)
        metadata_list = []
        for t in tables:
            body = get_uploaded_table_body(t)
            metadata_list.append(
                UploadedTableMetadata(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    upload_timestamp=t.upload_timestamp.isoformat(),
                    columns=t.columns,
                    row_count=len(body),
                )
            )
        return TablesListResponse(tables=metadata_list, total=len(metadata_list))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()


@router.get("/{table_id}", response_model=UploadedTableDetail)
async def get_table(request: Request, table_id: int):
    Session = request.app.state.app_db_sessionmaker
    db_session = Session()

    try:
        table = get_uploaded_table_by_id(db_session, table_id)
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")

        body = get_uploaded_table_body(table)
        return UploadedTableDetail(
            id=table.id,
            name=table.name,
            description=table.description,
            upload_timestamp=table.upload_timestamp.isoformat(),
            columns=table.columns,
            row_count=len(body),
            body=body,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()


@router.delete("/{table_id}")
async def delete_table_endpoint(request: Request, table_id: int):
    Session = request.app.state.app_db_sessionmaker
    db_session = Session()

    try:
        if not delete_uploaded_table(db_session, table_id):
            raise HTTPException(status_code=404, detail="Table not found")
        return {"message": "Table deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_session.close()
