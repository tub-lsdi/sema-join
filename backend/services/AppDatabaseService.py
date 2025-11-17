import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.persistence.uploaded_table import (
    create_uploaded_table,
    list_uploaded_tables,
    get_uploaded_table_by_id,
    delete_uploaded_table,
    get_uploaded_table_body,
    UploadedTable,
)
from backend.persistence.table_entry import create_table_entry
from backend.persistence.join_history import create_join_history
from backend.utils.csv_parser import parse_csv_to_list_of_dicts
from backend.models.uploaded_table import (
    UploadedTableMetadata,
    UploadedTableDetail,
    UploadTableResponse,
    TablesListResponse,
)


class AppDatabaseService:
    """Manages uploaded tables and join history in MySQL."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def parse_file_content(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Parse CSV or JSON file content into list of dicts."""
        filename_lower = filename.lower()

        if filename_lower.endswith(".csv"):
            return parse_csv_to_list_of_dicts(content)
        elif filename_lower.endswith(".json"):
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError("JSON must be an array of objects")
            return data
        else:
            raise ValueError("File must be CSV or JSON")

    def upload_table(
        self,
        content: str,
        filename: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> UploadTableResponse:
        table_data = self.parse_file_content(content, filename)

        session = self.session_factory()
        try:
            table = create_uploaded_table(session, table_data, name, description)
            return UploadTableResponse(
                id=table.id, name=table.name, message=f"Uploaded {len(table_data)} rows"
            )
        finally:
            session.close()

    def _build_metadata(self, table: UploadedTable) -> UploadedTableMetadata:
        body = get_uploaded_table_body(table)
        return UploadedTableMetadata(
            id=table.id,
            name=table.name,
            description=table.description,
            upload_timestamp=table.upload_timestamp.isoformat(),
            columns=table.columns,
            row_count=len(body),
        )

    def list_tables(self) -> TablesListResponse:
        session = self.session_factory()
        try:
            tables = list_uploaded_tables(session)
            metadata_list = [self._build_metadata(t) for t in tables]
            return TablesListResponse(tables=metadata_list, total=len(metadata_list))
        finally:
            session.close()

    def get_table_detail(self, table_id: int) -> Optional[UploadedTableDetail]:
        session = self.session_factory()
        try:
            table = get_uploaded_table_by_id(session, table_id)
            if not table:
                return None

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
        finally:
            session.close()

    def delete_table(self, table_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        session = self.session_factory()
        try:
            return delete_uploaded_table(session, table_id)
        finally:
            session.close()

    def get_table_data(self, table_id: int) -> Optional[List[Dict[str, Any]]]:
        """Returns raw table data or None if not found."""
        session = self.session_factory()
        try:
            table = get_uploaded_table_by_id(session, table_id)
            if not table:
                return None
            return get_uploaded_table_body(table)
        finally:
            session.close()

    def save_join_history(
        self,
        table_r_id: int,
        table_s_id: int,
        bridge_table: List[Dict[str, Any]],
        result: List[Dict[str, Any]],
        r_join_col: str,
        s_join_col: str,
    ) -> None:
        """Persist join operation and results to history."""
        session = self.session_factory()
        try:
            list_r = self.get_table_data(table_r_id)
            list_s = self.get_table_data(table_s_id)

            if not list_r or not list_s:
                raise ValueError("Cannot save history: tables not found")

            list_r_entry = create_table_entry(session, list_r)
            list_s_entry = create_table_entry(session, list_s)
            bridge_entry = create_table_entry(session, bridge_table)
            result_entry = create_table_entry(session, result)

            create_join_history(
                session=session,
                list_r_entry=list_r_entry,
                list_s_entry=list_s_entry,
                bridge_table_entry=bridge_entry,
                result_entry=result_entry,
                r_join_col=r_join_col,
                s_join_col=s_join_col,
            )
        finally:
            session.close()
