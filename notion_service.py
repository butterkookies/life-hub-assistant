import json
import logging
import math
from datetime import date
from typing import Dict, Any, List, Optional
from notion_client import Client
from config import settings
from image_models import AttachmentResult, TreadmillScan, WorkoutUpsertResult

logger = logging.getLogger("notion_service")

class NotionService:
    HEALTH_LOG_DATABASE_ID = "3c327102528781669c3cc7d7acfaa2a4"
    HEALTH_LOG_DATA_SOURCE_ID = "3c327102528781ab8777000b115b3f54"
    WORKOUT_PROPERTY_MAP = {
        "duration_minutes": "Duration (min)",
        "distance_km": "Distance (km)",
        "steps": "Treadmill Steps",
        "calories_kcal": "Workout Calories",
        "speed_kmh": "Speed (km/h)",
        "heart_rate_bpm": "Pulse / HR (bpm)",
        "trax_program": "TRAX Program",
        "workout_type": "Workout Type",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.NOTION_API_KEY
        self.client = Client(auth=self.api_key) if self.api_key else None

    def _ensure_client(self):
        if not self.client:
            if not settings.NOTION_API_KEY:
                raise ValueError("NOTION_API_KEY is not set in environment or .env file.")
            self.client = Client(auth=settings.NOTION_API_KEY)

    def search_workspace(self, query: str = "", filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search pages and databases across the workspace."""
        self._ensure_client()
        params: Dict[str, Any] = {"page_size": 20}
        if query:
            params["query"] = query
        
        if filter_type == "page":
            params["filter"] = {"value": "page", "property": "object"}
        elif filter_type in ["database", "data_source"]:
            params["filter"] = {"value": "data_source", "property": "object"}

        try:
            response = self.client.search(**params)
        except Exception:
            # Fallback without filter if filter rejected by Notion API version
            params.pop("filter", None)
            response = self.client.search(**params)

        results = []
        for item in response.get("results", []):
            obj_type = item.get("object")
            item_id = item.get("id")
            title = "Untitled"
            parent = item.get("parent", {})
            db_id = parent.get("database_id") if parent.get("type") == "database_id" else item_id
            
            if obj_type == "page":
                props = item.get("properties", {})
                for prop_val in props.values():
                    if prop_val.get("type") == "title":
                        title_arr = prop_val.get("title", [])
                        if title_arr:
                            title = "".join(t.get("plain_text", "") for t in title_arr)
                        break
            elif obj_type in ["database", "data_source"]:
                title_arr = item.get("title", [])
                if title_arr:
                    title = "".join(t.get("plain_text", "") for t in title_arr)

            results.append({
                "id": db_id if obj_type == "data_source" else item_id,
                "data_source_id": item_id if obj_type == "data_source" else None,
                "type": obj_type,
                "title": title or "Untitled",
                "url": item.get("url"),
                "last_edited_time": item.get("last_edited_time")
            })
        return results

    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Retrieve page metadata and all child text blocks formatted as markdown."""
        self._ensure_client()
        clean_id = page_id.replace("-", "")
        page = self.client.pages.retrieve(page_id=clean_id)
        
        # Extract title
        title = "Untitled"
        props = page.get("properties", {})
        for prop_val in props.values():
            if prop_val.get("type") == "title":
                title_arr = prop_val.get("title", [])
                if title_arr:
                    title = "".join(t.get("plain_text", "") for t in title_arr)
                break

        # Fetch child blocks
        blocks_resp = self.client.blocks.children.list(block_id=clean_id, page_size=100)
        lines = [f"# {title}\n"]
        
        for block in blocks_resp.get("results", []):
            b_type = block.get("type")
            b_data = block.get(b_type, {})
            rich_texts = b_data.get("rich_text", [])
            text_content = "".join(t.get("plain_text", "") for t in rich_texts)
            
            if b_type == "paragraph":
                lines.append(f"{text_content}\n")
            elif b_type == "heading_1":
                lines.append(f"# {text_content}\n")
            elif b_type == "heading_2":
                lines.append(f"## {text_content}\n")
            elif b_type == "heading_3":
                lines.append(f"### {text_content}\n")
            elif b_type == "bulleted_list_item":
                lines.append(f"- {text_content}")
            elif b_type == "numbered_list_item":
                lines.append(f"1. {text_content}")
            elif b_type == "to_do":
                checked = "x" if b_data.get("checked") else " "
                lines.append(f"- [{checked}] {text_content}")
            elif b_type == "callout":
                lines.append(f"> 💡 {text_content}")
            elif b_type == "quote":
                lines.append(f"> {text_content}")
            elif b_type == "code":
                lines.append(f"```\n{text_content}\n```")

        return {
            "id": page.get("id"),
            "title": title,
            "url": page.get("url"),
            "content": "\n".join(lines)
        }

    KNOWN_DATA_SOURCES = {
        "d1527102528783299cac81b9d565b99b": "96927102528782d9bed487a7322ac310", # Tasks
        "ba427102528782efbdce815b505396a2": "59827102528783dbb9e807b71c738058", # Projects
        "51127102528782ed8a80816bc58e66a1": "97227102528782ad81b707fb6d42c4d5", # Workstreams
        "2f37a332d3d2412eb52130f52c279318": "d4e6043c84e045d2a63b45ad038819f7", # Notes
        "ea7c1cc69135485fbe4d0f7fd4947a00": "6e61a09d80e94e5ba56d0f94772cc1f1", # Thought Inbox
        HEALTH_LOG_DATABASE_ID: HEALTH_LOG_DATA_SOURCE_ID, # Daily Health & Workout Log
    }

    @staticmethod
    def _notion_property_value(prop: Dict[str, Any]) -> Any:
        prop_type = prop.get("type")
        value = prop.get(prop_type) if prop_type else None
        if prop_type == "select":
            return value.get("name") if value else None
        if prop_type == "date":
            return value.get("start") if value else None
        if prop_type in ("title", "rich_text"):
            return "".join(item.get("plain_text", "") for item in (value or []))
        return value

    @staticmethod
    def _workout_property_payload(attribute: str, value: Any) -> Dict[str, Any]:
        if attribute in ("trax_program", "workout_type"):
            return {"select": {"name": value}}
        return {"number": value}

    @staticmethod
    def _values_match(existing: Any, incoming: Any) -> bool:
        if isinstance(existing, (int, float)) and isinstance(incoming, (int, float)):
            return math.isclose(float(existing), float(incoming), rel_tol=1e-6, abs_tol=1e-6)
        return existing == incoming

    def upsert_daily_workout(
        self,
        scan: TreadmillScan,
        allow_overwrite: bool = False,
        expected_conflicts: Optional[Dict[str, tuple[Any, Any]]] = None,
    ) -> WorkoutUpsertResult:
        """Create or safely update the single health-log row for a date."""
        validation_errors = scan.validation_errors()
        if validation_errors:
            raise ValueError(
                "Invalid treadmill scan: " + "; ".join(validation_errors)
            )
        self._ensure_client()
        response = self.client.data_sources.query(
            data_source_id=self.HEALTH_LOG_DATA_SOURCE_ID,
            filter={"property": "Date", "date": {"equals": scan.date}},
            page_size=2,
        )
        results = response.get("results", [])
        incoming = {
            attribute: getattr(scan, attribute)
            for attribute in self.WORKOUT_PROPERTY_MAP
            if getattr(scan, attribute) is not None
        }

        if not results:
            properties: Dict[str, Any] = {
                "Day": {
                    "title": [
                        {
                            "text": {
                                "content": date.fromisoformat(scan.date).strftime(
                                    "%b %d, %Y"
                                )
                            }
                        }
                    ]
                },
                "Date": {"date": {"start": scan.date}},
            }
            for attribute, value in incoming.items():
                properties[self.WORKOUT_PROPERTY_MAP[attribute]] = (
                    self._workout_property_payload(attribute, value)
                )
            page = self.client.pages.create(
                parent={"data_source_id": self.HEALTH_LOG_DATA_SOURCE_ID},
                properties=properties,
            )
            return WorkoutUpsertResult(
                action="created",
                page_id=page.get("id", ""),
                page_url=page.get("url"),
                written_fields=list(incoming),
            )

        page = results[0]
        page_id = page.get("id", "")
        page_url = page.get("url")
        existing_properties = page.get("properties", {})
        updates: Dict[str, Any] = {}
        written_fields: list[str] = []
        conflicts: Dict[str, tuple[Any, Any]] = {}

        for attribute, value in incoming.items():
            property_name = self.WORKOUT_PROPERTY_MAP[attribute]
            existing = self._notion_property_value(
                existing_properties.get(property_name, {})
            )
            if existing is None or existing == "":
                updates[property_name] = self._workout_property_payload(attribute, value)
                written_fields.append(attribute)
            elif not self._values_match(existing, value):
                conflicts[attribute] = (existing, value)
                if allow_overwrite:
                    updates[property_name] = self._workout_property_payload(attribute, value)
                    written_fields.append(attribute)

        if allow_overwrite and conflicts and (
            expected_conflicts is None or conflicts != expected_conflicts
        ):
            return WorkoutUpsertResult(
                action="conflict",
                page_id=page_id,
                page_url=page_url,
                conflicts=conflicts,
            )
        if conflicts and not allow_overwrite:
            return WorkoutUpsertResult(
                action="conflict",
                page_id=page_id,
                page_url=page_url,
                conflicts=conflicts,
            )
        if not updates:
            return WorkoutUpsertResult(
                action="duplicate", page_id=page_id, page_url=page_url
            )

        updated = self.client.pages.update(page_id=page_id, properties=updates)
        return WorkoutUpsertResult(
            action="updated",
            page_id=updated.get("id", page_id),
            page_url=updated.get("url", page_url),
            written_fields=written_fields,
            conflicts=conflicts,
        )

    def attach_image(
        self,
        page_id: str,
        image_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> AttachmentResult:
        """Upload an image to Notion and append it to a daily log page."""
        self._ensure_client()
        last_error: Optional[Exception] = None
        upload_id: Optional[str] = None
        for _attempt in range(3):
            try:
                upload = self.client.file_uploads.create(
                    mode="single_part", filename=filename, content_type=mime_type
                )
                candidate_upload_id = upload["id"]
                self.client.file_uploads.send(
                    file_upload_id=candidate_upload_id,
                    file=(filename, image_bytes, mime_type),
                )
                upload_id = candidate_upload_id
                break
            except Exception as exc:
                last_error = exc
                logger.warning("Notion image attachment attempt failed: %s", type(exc).__name__)
        if not upload_id:
            return AttachmentResult(
                attached=False,
                error=str(last_error) if last_error else "Unknown attachment error",
            )
        try:
            # Append once. Retrying an ambiguous append timeout can duplicate blocks.
            self.client.blocks.children.append(
                block_id=page_id.replace("-", ""),
                children=[
                    {
                        "object": "block",
                        "type": "image",
                        "image": {
                            "type": "file_upload",
                            "file_upload": {"id": upload_id},
                        },
                    }
                ],
            )
            return AttachmentResult(attached=True, file_upload_id=upload_id)
        except Exception as exc:
            logger.warning("Notion image block append failed: %s", type(exc).__name__)
            last_error = exc
        return AttachmentResult(
            attached=False,
            file_upload_id=upload_id,
            error=str(last_error) if last_error else "Unknown attachment error",
            # The append may have committed before a response timeout. Retrying could
            # create a duplicate block, so only known pre-append failures are retryable.
            retryable=False,
        )

    def query_database(self, database_id: str, filter_json: Optional[Dict] = None, page_size: int = 20) -> List[Dict[str, Any]]:
        """Query items in a Notion database or data source."""
        self._ensure_client()
        clean_id = database_id.replace("-", "")
        body: Dict[str, Any] = {"page_size": min(page_size, 100)}
        if filter_json:
            body["filter"] = filter_json

        target_ds_id = self.KNOWN_DATA_SOURCES.get(clean_id, clean_id)

        try:
            response = self.client.data_sources.query(data_source_id=target_ds_id, **body)
        except Exception:
            try:
                db = self.client.databases.retrieve(database_id=clean_id)
                ds_list = db.get("data_sources", [])
                if ds_list:
                    ds_id = ds_list[0]["id"].replace("-", "")
                    response = self.client.data_sources.query(data_source_id=ds_id, **body)
                else:
                    response = self.client.request(path=f"databases/{clean_id}/query", method="POST", body=body)
            except Exception as e:
                logger.error(f"Error querying database {clean_id}: {e}")
                return []

        items = []
        for page in response.get("results", []):
            page_props = {}
            for name, val in page.get("properties", {}).items():
                p_type = val.get("type")
                if p_type == "title":
                    title_arr = val.get("title", [])
                    page_props[name] = "".join(t.get("plain_text", "") for t in title_arr)
                elif p_type == "rich_text":
                    rt_arr = val.get("rich_text", [])
                    page_props[name] = "".join(t.get("plain_text", "") for t in rt_arr)
                elif p_type == "select":
                    sel = val.get("select")
                    page_props[name] = sel.get("name") if sel else None
                elif p_type == "status":
                    st = val.get("status")
                    page_props[name] = st.get("name") if st else None
                elif p_type == "date":
                    dt = val.get("date")
                    page_props[name] = dt.get("start") if dt else None
                elif p_type == "checkbox":
                    page_props[name] = val.get("checkbox")
                elif p_type == "number":
                    page_props[name] = val.get("number")
                elif p_type == "relation":
                    page_props[name] = [r.get("id") for r in val.get("relation", [])]
            
            items.append({
                "id": page.get("id"),
                "url": page.get("url"),
                "properties": page_props
            })
        return items

    def get_calendar_schedule(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve scheduled tasks and calendar events for a specific date (YYYY-MM-DD) or upcoming items."""
        self._ensure_client()
        # Find Tasks database / data source
        tasks = self.query_database("d1527102-5287-8329-9cac-81b9d565b99b", page_size=50)
        if not tasks:
            # Fallback search
            results = self.search_workspace(query="Tasks", filter_type="data_source")
            if results:
                tasks = self.query_database(results[0]["id"], page_size=50)

        scheduled_items = []
        for task in tasks:
            props = task.get("properties", {})
            task_name = props.get("Name") or "Untitled Task"
            do_date = props.get("Do Date") or props.get("Date") or props.get("Due Date")
            status = props.get("Status") or "Not started"
            
            if target_date:
                if do_date and str(do_date).startswith(target_date):
                    scheduled_items.append({
                        "task": task_name,
                        "date": do_date,
                        "status": status,
                        "url": task.get("url"),
                        "properties": props
                    })
            else:
                if do_date:
                    scheduled_items.append({
                        "task": task_name,
                        "date": do_date,
                        "status": status,
                        "url": task.get("url"),
                        "properties": props
                    })
        return scheduled_items

    def get_projects_map(self) -> Dict[str, str]:
        """Fetch all projects and map their IDs (both hyphenated and clean) to project names."""
        self._ensure_client()
        projects_data = self.query_database("ba427102-5287-82ef-bdce-815b505396a2", page_size=100)
        proj_map = {}
        for p in projects_data:
            p_id = p.get("id", "")
            clean_id = p_id.replace("-", "")
            name = p.get("properties", {}).get("Name") or "Untitled Project"
            if p_id:
                proj_map[p_id] = name
            if clean_id:
                proj_map[clean_id] = name
        return proj_map

    def get_tasks_for_day(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve rich tasks for a specific date (YYYY-MM-DD), with mapped project names and priority."""
        self._ensure_client()
        tasks = self.query_database("d1527102-5287-8329-9cac-81b9d565b99b", page_size=100)
        if not tasks:
            results = self.search_workspace(query="Tasks", filter_type="data_source")
            if results:
                tasks = self.query_database(results[0]["id"], page_size=100)

        proj_map = {}
        try:
            proj_map = self.get_projects_map()
        except Exception as e:
            logger.warning(f"Could not load project map: {e}")

        items = []
        for task in tasks:
            props = task.get("properties", {})
            task_id = task.get("id")
            task_name = props.get("Name") or "Untitled Task"
            do_date = props.get("Do Date") or props.get("Date") or props.get("Due Date")
            status = props.get("Status") or "Not started"
            priority = props.get("Priority") or "Normal"
            archive = props.get("Archive", False)
            if archive:
                continue

            # Project relation
            rel_projects = props.get("Projects", [])
            project_names = []
            project_id = None
            if isinstance(rel_projects, list) and rel_projects:
                project_id = rel_projects[0]
                for pid in rel_projects:
                    c_pid = str(pid).replace("-", "")
                    p_name = proj_map.get(pid) or proj_map.get(c_pid)
                    if p_name:
                        project_names.append(p_name)

            main_project_name = project_names[0] if project_names else "Personal"

            if target_date:
                if do_date and str(do_date).startswith(target_date):
                    items.append({
                        "id": task_id,
                        "name": task_name,
                        "date": str(do_date),
                        "status": status,
                        "priority": priority,
                        "project_id": project_id,
                        "project_name": main_project_name,
                        "url": task.get("url"),
                        "properties": props
                    })
            else:
                items.append({
                    "id": task_id,
                    "name": task_name,
                    "date": str(do_date) if do_date else None,
                    "status": status,
                    "priority": priority,
                    "project_id": project_id,
                    "project_name": main_project_name,
                    "url": task.get("url"),
                    "properties": props
                })
        return items


    def _normalize_key(self, k: str) -> str:
        key_map = {
            "project": "Projects",
            "projects": "Projects",
            "due": "Do Date",
            "due date": "Do Date",
            "due_date": "Do Date",
            "date": "Do Date",
            "status": "Status",
            "priority": "Priority",
            "archive": "Archive",
            "workstream": "Workstream"
        }
        return key_map.get(k.strip().lower(), k)

    def _format_property_val(self, k: str, v: Any) -> Dict[str, Any]:
        """Format arbitrary Python types into Notion property structures."""
        if isinstance(v, dict) and any(x in v for x in ["select", "date", "status", "checkbox", "relation", "title", "rich_text", "number", "people"]):
            return v
        elif isinstance(v, bool):
            return {"checkbox": v}
        elif isinstance(v, (int, float)):
            return {"number": v}
        elif isinstance(v, list):
            # Treat array of strings / UUIDs as relations
            return {"relation": [{"id": str(item_id).replace("-", "")} for item_id in v]}
        elif isinstance(v, str):
            lower_v = v.lower()
            if lower_v in ["done", "in progress", "not started", "to-do", "complete", "completed"]:
                name_map = {"done": "Done", "in progress": "In progress", "not started": "Not started", "to-do": "Not started", "complete": "Done", "completed": "Done"}
                return {"status": {"name": name_map.get(lower_v, v)}}
            elif "priority" in lower_v:
                return {"select": {"name": v}}
            elif len(v) == 10 and v.count("-") == 2: # YYYY-MM-DD
                return {"date": {"start": v}}
            elif len(v) in [32, 36] and ("-" in v or v.isalnum()) and k.lower() in ["projects", "project", "workstream"]:
                # Single UUID as relation
                return {"relation": [{"id": v.replace("-", "")}]}
            else:
                return {"rich_text": [{"text": {"content": v}}]}
        return {"rich_text": [{"text": {"content": str(v)}}]}

    def create_database_item(self, database_id: str, title: str, title_prop_name: str = "Name",
                             properties: Optional[Dict[str, Any]] = None,
                             content: Optional[str] = None) -> Dict[str, Any]:
        """Create a new page/entry in a Notion database."""
        self._ensure_client()
        clean_id = database_id.replace("-", "")
        
        # Check if clean_id is a data source and resolve to parent database_id
        try:
            ds = self.client.data_sources.retrieve(data_source_id=clean_id)
            if ds.get("parent", {}).get("type") == "database_id":
                clean_id = ds["parent"]["database_id"].replace("-", "")
        except Exception:
            pass

        props: Dict[str, Any] = {
            title_prop_name: {
                "title": [{"text": {"content": title}}]
            }
        }
        
        if properties:
            for k, v in properties.items():
                norm_k = self._normalize_key(k)
                if norm_k == title_prop_name:
                    continue
                props[norm_k] = self._format_property_val(norm_k, v)

        children = []
        if content:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            })

        body = {
            "parent": {"database_id": clean_id},
            "properties": props
        }
        if children:
            body["children"] = children

        try:
            created = self.client.pages.create(**body)
            return {"id": created.get("id"), "url": created.get("url"), "status": "created"}
        except Exception as e:
            # If property validation failed, retry with just title and basic status
            logger.warning(f"Initial page create failed ({e}). Retrying with safe core properties...")
            safe_props = {title_prop_name: {"title": [{"text": {"content": title}}]}}
            if "Status" in props:
                safe_props["Status"] = props["Status"]
            safe_body = {"parent": {"database_id": clean_id}, "properties": safe_props}
            if children:
                safe_body["children"] = children
            created = self.client.pages.create(**safe_body)
            return {"id": created.get("id"), "url": created.get("url"), "status": "created"}

    def update_page_properties(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update properties of an existing Notion page or database item (e.g. status, priority, archive)."""
        self._ensure_client()
        clean_id = page_id.replace("-", "")
        
        props: Dict[str, Any] = {}
        for k, v in properties.items():
            props[k] = self._format_property_val(k, v)

        updated = self.client.pages.update(page_id=clean_id, properties=props)
        return {"id": updated.get("id"), "url": updated.get("url"), "status": "updated"}

    def append_to_page(self, page_id: str, text: str, block_type: str = "paragraph") -> Dict[str, Any]:
        """Append text blocks to an existing page."""
        self._ensure_client()
        clean_id = page_id.replace("-", "")
        
        valid_type = block_type if block_type in ["paragraph", "heading_2", "heading_3", "bulleted_list_item", "to_do"] else "paragraph"
        
        block_body: Dict[str, Any] = {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
        if valid_type == "to_do":
            block_body["checked"] = False

        children = [{
            "object": "block",
            "type": valid_type,
            valid_type: block_body
        }]

        self.client.blocks.children.append(block_id=clean_id, children=children)
        return {"status": "appended", "page_id": page_id}

    def create_page(self, parent_page_id: str, title: str, content: str = "") -> Dict[str, Any]:
        """Create a new child page under a parent page."""
        self._ensure_client()
        clean_id = parent_page_id.replace("-", "")
        
        body = {
            "parent": {"page_id": clean_id},
            "properties": {
                "title": {"title": [{"text": {"content": title}}]}
            }
        }
        if content:
            body["children"] = [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]}
            }]

        created = self.client.pages.create(**body)
        return {"id": created.get("id"), "url": created.get("url"), "status": "created"}

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Optional[Dict[str, Any]] = None,
        view_type: str = "table",
        is_inline: bool = True
    ) -> Dict[str, Any]:
        """Create an actual Notion database with schema properties and layout view under a parent page."""
        self._ensure_client()
        clean_id = parent_page_id.replace("-", "")

        # Default properties if none provided or empty
        if not properties:
            formatted_props = {
                "Task": {"title": {}},
                "Status": {
                    "status": {
                        "options": [
                            {"name": "Not started", "color": "default"},
                            {"name": "In progress", "color": "blue"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "gray"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "High", "color": "red"}
                        ]
                    }
                },
                "Due Date": {"date": {}},
                "Notes": {"rich_text": {}}
            }
        else:
            formatted_props = {}
            has_title = False
            for k, v in properties.items():
                if isinstance(v, dict):
                    formatted_props[k] = v
                    if "title" in v:
                        has_title = True
                elif isinstance(v, str):
                    vt = v.lower().strip()
                    if vt in ["title", "name", "task"]:
                        formatted_props[k] = {"title": {}}
                        has_title = True
                    elif vt in ["status"]:
                        formatted_props[k] = {
                            "status": {
                                "options": [
                                    {"name": "Not started", "color": "default"},
                                    {"name": "In progress", "color": "blue"},
                                    {"name": "Done", "color": "green"}
                                ]
                            }
                        }
                    elif vt in ["select", "priority"]:
                        formatted_props[k] = {
                            "select": {
                                "options": [
                                    {"name": "Low", "color": "gray"},
                                    {"name": "Medium", "color": "yellow"},
                                    {"name": "High", "color": "red"}
                                ]
                            }
                        }
                    elif vt in ["multi_select", "tags"]:
                        formatted_props[k] = {"multi_select": {}}
                    elif vt in ["date", "due_date", "due"]:
                        formatted_props[k] = {"date": {}}
                    elif vt in ["checkbox", "done", "completed"]:
                        formatted_props[k] = {"checkbox": {}}
                    elif vt in ["number"]:
                        formatted_props[k] = {"number": {"format": "number"}}
                    elif vt in ["people", "assignee", "user"]:
                        formatted_props[k] = {"people": {}}
                    elif vt in ["url"]:
                        formatted_props[k] = {"url": {}}
                    else:
                        formatted_props[k] = {"rich_text": {}}
                else:
                    formatted_props[k] = {"rich_text": {}}

            if not has_title:
                formatted_props = {"Task": {"title": {}}, **formatted_props}

        parent = {"type": "page_id", "page_id": clean_id}
        title_arr = [{"type": "text", "text": {"content": title}}]

        try:
            created_db = self.client.databases.create(
                parent=parent,
                title=title_arr,
                is_inline=is_inline,
                initial_data_source={"properties": formatted_props}
            )
        except Exception as err:
            logger.warning(f"databases.create with initial_data_source failed: {err}. Retrying with properties...")
            created_db = self.client.databases.create(
                parent=parent,
                title=title_arr,
                is_inline=is_inline,
                properties=formatted_props
            )

        db_id = created_db.get("id")
        data_sources = created_db.get("data_sources", [])
        ds_id = data_sources[0].get("id") if data_sources else None

        if db_id and ds_id:
            clean_db = db_id.replace("-", "")
            clean_ds = ds_id.replace("-", "")
            self.KNOWN_DATA_SOURCES[clean_db] = clean_ds

        # Create custom view if requested (e.g. list, board, gallery, calendar, timeline)
        created_view_id = None
        valid_views = ["table", "board", "list", "gallery", "calendar", "timeline"]
        norm_view = view_type.lower().strip()
        if norm_view in valid_views and norm_view != "table" and ds_id:
            try:
                view_res = self.client.views.create(
                    database_id=db_id,
                    data_source_id=ds_id,
                    name=f"{title} ({norm_view.capitalize()} View)",
                    type=norm_view,
                    configuration={"type": norm_view}
                )
                created_view_id = view_res.get("id")
            except Exception as e_view:
                logger.warning(f"Could not create custom view '{norm_view}': {e_view}")

        return {
            "id": db_id,
            "data_source_id": ds_id,
            "title": title,
            "url": created_db.get("url"),
            "view_type": norm_view,
            "view_id": created_view_id,
            "status": "created"
        }

notion_service = NotionService()
