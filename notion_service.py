import json
import logging
import math
from datetime import date
from typing import Dict, Any, List, Optional
from urllib.parse import unquote
from notion_client import Client
from notion_client.errors import APIResponseError
from config import settings
from image_models import AttachmentResult, TreadmillScan, WorkoutUpsertResult

logger = logging.getLogger("notion_service")

class NotionService:
    ROOT_PAGE_ID = "3be27102528781969765dedd1b639a0b"
    TASKS_DATABASE_ID = "d1527102528783299cac81b9d565b99b"
    TASKS_DATA_SOURCE_ID = "96927102528782d9bed487a7322ac310"
    PROJECTS_DATABASE_ID = "ba427102528782efbdce815b505396a2"
    PROJECTS_DATA_SOURCE_ID = "59827102528783dbb9e807b71c738058"
    LEGACY_DESTINATIONS = {
        "3b627102528781b988f2f1133532696f",  # Outer Life Hub page
        "a6494cb1b0994c41897a6ffb6b4a476a",  # Legacy Tasks database
        "e4c4941ceaff49f4b7738d19165955d1",  # Legacy Tasks data source
        "bbcdbba6e6064de09d75b11e1caae66a",  # Legacy Projects database
        "c63a416028274bc5a599e08d37bd3949",  # Legacy Projects data source
    }
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

    def _check_destination(self, entity_id: str) -> None:
        if entity_id.replace("-", "") in self.LEGACY_DESTINATIONS:
            raise ValueError("This is a legacy Life Hub destination. Use Life Hub Manager and its master databases.")

    def _paginate(self, endpoint, **params):
        """Read all pages; a failed request must not masquerade as an empty result."""
        while True:
            response = endpoint(**params)
            yield from response.get("results", [])
            if not response.get("has_more"):
                break
            params["start_cursor"] = response["next_cursor"]

    def _resolve_data_source(self, entity_id: str) -> str:
        clean_id = entity_id.replace("-", "")
        if clean_id in self.KNOWN_DATA_SOURCES:
            return self.KNOWN_DATA_SOURCES[clean_id]
        if clean_id in self.KNOWN_DATA_SOURCES.values():
            return clean_id
        try:
            source = self.client.data_sources.retrieve(data_source_id=clean_id)
            return source["id"].replace("-", "")
        except APIResponseError as exc:
            if exc.code != "object_not_found":
                raise
        database = self.client.databases.retrieve(database_id=clean_id)
        sources = database.get("data_sources", [])
        if len(sources) != 1:
            raise ValueError("Database has zero or multiple data sources; specify the exact data_source_id.")
        return sources[0]["id"].replace("-", "")

    def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        self._ensure_client()
        source_id = self._resolve_data_source(database_id)
        source = self.client.data_sources.retrieve(data_source_id=source_id)
        return {"data_source_id": source_id, "properties": source["properties"], "parent": source.get("parent")}

    def get_workspace_context(self) -> Dict[str, Any]:
        return {
            "root": {"id": self.ROOT_PAGE_ID, "title": "Life Hub Manager"},
            "tasks": {"database_id": self.TASKS_DATABASE_ID, **self.get_database_schema(self.TASKS_DATA_SOURCE_ID)},
            "projects": {"database_id": self.PROJECTS_DATABASE_ID, **self.get_database_schema(self.PROJECTS_DATA_SOURCE_ID)},
            "task_policy": "Create rows in master Tasks; relate Projects. Project pages contain filtered linked views of these same rows.",
            "legacy_destinations": sorted(self.LEGACY_DESTINATIONS),
        }

    def search_workspace(self, query: str = "", filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search pages and databases across the workspace."""
        self._ensure_client()
        params: Dict[str, Any] = {"page_size": 100}
        if query:
            params["query"] = query
        
        if filter_type == "page":
            params["filter"] = {"value": "page", "property": "object"}
        elif filter_type in ["database", "data_source"]:
            params["filter"] = {"value": "data_source", "property": "object"}

        results = []
        for item in self._paginate(self.client.search, **params):
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
                "parent": parent,
                "in_trash": item.get("in_trash", False),
                "is_legacy_destination": (item_id or "").replace("-", "") in self.LEGACY_DESTINATIONS,
                "is_canonical": (item_id or "").replace("-", "") in {
                    self.ROOT_PAGE_ID, self.TASKS_DATABASE_ID, self.TASKS_DATA_SOURCE_ID,
                    self.PROJECTS_DATABASE_ID, self.PROJECTS_DATA_SOURCE_ID,
                },
                "url": item.get("url"),
                "last_edited_time": item.get("last_edited_time")
            })
        return sorted(results, key=lambda item: (not item["is_canonical"], item["is_legacy_destination"]))

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
        blocks = list(self._paginate(self.client.blocks.children.list, block_id=clean_id, page_size=100))
        lines = [f"# {title}\n"]
        
        for block in blocks:
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
            elif b_type in ("child_page", "child_database"):
                lines.append(f"[{b_type}: {b_data.get('title', 'Untitled')}] ({block['id']})")

        return {
            "id": page.get("id"),
            "title": title,
            "url": page.get("url"),
            "parent": page.get("parent"),
            "children": [{"id": b["id"], "type": b["type"], "has_children": b.get("has_children", False)} for b in blocks],
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

        target_ds_id = self._resolve_data_source(clean_id)

        items = []
        for page in self._paginate(self.client.data_sources.query, data_source_id=target_ds_id, **body):
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
        tasks = self.query_database(self.TASKS_DATA_SOURCE_ID, page_size=100)

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
        projects_data = self.query_database(self.PROJECTS_DATA_SOURCE_ID, page_size=100)
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
        tasks = self.query_database(self.TASKS_DATA_SOURCE_ID, page_size=100)

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
        
        self._check_destination(clean_id)
        schema = self.get_database_schema(clean_id)
        source_id = schema["data_source_id"]
        self._check_destination(source_id)
        fields = schema["properties"]
        title_fields = [name for name, field in fields.items() if field["type"] == "title"]
        if len(title_fields) != 1:
            raise ValueError("Destination must have exactly one title property.")
        title_prop_name = title_fields[0]
        if not title.strip():
            raise ValueError("Title cannot be empty.")

        props: Dict[str, Any] = {
            title_prop_name: {
                "title": [{"text": {"content": title}}]
            }
        }
        
        if properties:
            for k, v in properties.items():
                norm_k = k if k in fields else self._normalize_key(k)
                if norm_k == title_prop_name:
                    continue
                if norm_k not in fields:
                    raise ValueError(f"Unknown property {k!r}. Available properties: {', '.join(fields)}. No item was created.")
                props[norm_k] = self._format_schema_value(norm_k, v, fields[norm_k])

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
            "parent": {"data_source_id": source_id},
            "properties": props
        }
        if children:
            body["children"] = children

        # Do not retry an uncertain write or silently drop requested properties.
        created = self.client.pages.create(**body)
        return {"id": created["id"], "url": created.get("url"), "status": "created",
                "data_source_id": source_id, "saved_properties": props}

    def _format_schema_value(self, name: str, value: Any, field: Dict[str, Any]) -> Dict[str, Any]:
        kind = field["type"]
        if kind in {"formula", "rollup", "created_time", "last_edited_time", "created_by", "last_edited_by", "unique_id"}:
            raise ValueError(f"Property {name!r} is computed/read-only.")
        if isinstance(value, dict):
            if kind not in value:
                raise ValueError(f"Property {name!r} requires {kind} data.")
            return value
        if kind in {"select", "status"}:
            options = field.get(kind, {}).get("options", [])
            matches = [option["name"] for option in options if option["name"].casefold() == str(value).casefold()]
            if not matches:
                raise ValueError(f"Invalid {name!r}: choose from {[option['name'] for option in options]}.")
            return {kind: {"name": matches[0]}}
        if kind == "relation":
            ids = value if isinstance(value, list) else [value]
            return {"relation": [{"id": str(item).replace("-", "")} for item in ids]}
        if kind == "date":
            return {"date": {"start": value} if value else None}
        if kind in {"title", "rich_text"}:
            return {kind: [{"text": {"content": str(value)}}]}
        if kind == "checkbox" and isinstance(value, bool):
            return {kind: value}
        if kind == "number" and (value is None or isinstance(value, (int, float)) and not isinstance(value, bool)):
            return {kind: value}
        if kind in {"url", "email", "phone_number"}:
            return {kind: value}
        raise ValueError(f"Provide a typed Notion {kind} value for {name!r}.")

    def _validate_project(self, project_id: str) -> None:
        project = self.client.pages.retrieve(page_id=project_id.replace("-", ""))
        parent = project.get("parent", {})
        parent_id = parent.get("data_source_id") or parent.get("database_id", "")
        if project.get("archived") or project.get("in_trash") or parent_id.replace("-", "") not in {
            self.PROJECTS_DATA_SOURCE_ID, self.PROJECTS_DATABASE_ID,
        }:
            raise ValueError("Project must be an active entry in Life Hub Manager's master Projects database.")

    def create_task(self, title: str, due_date: str = "", project_id: str = "", content: str = "") -> Dict[str, Any]:
        self._ensure_client()
        props: Dict[str, Any] = {"Status": "Not started"}
        if due_date:
            date.fromisoformat(due_date)
            props["Do Date"] = due_date
        if project_id:
            self._validate_project(project_id)
            props["Projects"] = [project_id]
        return self.create_database_item(self.TASKS_DATA_SOURCE_ID, title, properties=props, content=content)

    def ensure_project_tasks_view(self, project_id: str, view_type: str = "table") -> Dict[str, Any]:
        self._ensure_client()
        self._validate_project(project_id)
        if view_type not in {"table", "list", "board", "gallery", "calendar", "timeline"}:
            raise ValueError("Unsupported project task view type.")
        clean_project_id = project_id.replace("-", "")
        task_filter = {"property": "Projects", "relation": {"contains": clean_project_id}}
        fields = self.get_database_schema(self.TASKS_DATA_SOURCE_ID)["properties"]
        project_property = fields["Projects"].get("id", "Projects")
        # Find a prior successful view before retrying a partially completed project setup.
        references = []
        for block in self._paginate(self.client.blocks.children.list, block_id=clean_project_id, page_size=100):
            if block.get("type") == "child_database":
                references.extend(self._paginate(self.client.views.list, database_id=block["id"]))
        for reference in references:
            view = self.client.views.retrieve(view_id=reference["id"])
            if view.get("type") != view_type or (view.get("data_source_id") or "").replace("-", "") != self.TASKS_DATA_SOURCE_ID:
                continue
            relation = view.get("filter", {}).get("relation", {}) if view.get("filter") else {}
            contains = str(relation.get("contains", "")).replace("-", "")
            if unquote(view.get("filter", {}).get("property", "")) in {"Projects", unquote(project_property)} and contains == clean_project_id:
                return {"status": "ready", "view_id": view["id"], "url": view.get("url"), "reused": True}
        configuration: Dict[str, Any] = {"type": view_type}
        if view_type == "board":
            configuration["group_by"] = {"type": "status", "property_id": fields["Status"]["id"], "group_by": "group", "sort": {"type": "manual"}}
        elif view_type in {"calendar", "timeline"}:
            configuration["date_property_id"] = fields["Do Date"]["id"]
        view = self.client.views.create(
            create_database={"parent": {"type": "page_id", "page_id": clean_project_id}},
            data_source_id=self.TASKS_DATA_SOURCE_ID, name="Project Tasks", type=view_type,
            filter=task_filter, configuration=configuration,
        )
        return {"status": "ready", "view_id": view["id"], "url": view.get("url"), "reused": False}

    def create_project(self, title: str, content: str = "", view_type: str = "table") -> Dict[str, Any]:
        if not title.strip():
            raise ValueError("Project title cannot be empty.")
        if view_type not in {"table", "list", "board", "gallery", "calendar", "timeline"}:
            raise ValueError("Unsupported project task view type.")
        matches = [item for item in self.query_database(
            self.PROJECTS_DATA_SOURCE_ID, filter_json={"property": "Name", "title": {"equals": title}},
        ) if not item.get("properties", {}).get("Archive")]
        if len(matches) > 1:
            raise ValueError("Multiple projects have that name. Select the project ID before creating tasks or a view.")
        if matches:
            result = {**matches[0], "status": "existing"}
        else:
            result = self.create_database_item(self.PROJECTS_DATA_SOURCE_ID, title, content=content)
        try:
            result["tasks_view"] = self.ensure_project_tasks_view(result["id"], view_type)
        except Exception as exc:
            logger.warning("Project exists but tasks view setup failed: %s", type(exc).__name__)
            result.update(status="partial", error="Project saved, but the task view could not be confirmed.",
                          next_step="Call ensure_project_tasks_view with this project ID; do not create another project.")
        return result

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
        self._check_destination(clean_id)
        if block_type == "to_do" or any(line.lstrip().startswith(("- [ ]", "- [x]", "* [ ]", "* [x]")) for line in text.splitlines()):
            raise ValueError("Save actionable tasks with create_task in the master Tasks database, not page checkboxes.")
        
        valid_type = block_type if block_type in ["paragraph", "heading_2", "heading_3", "bulleted_list_item"] else "paragraph"
        
        block_body: Dict[str, Any] = {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
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
        self._check_destination(clean_id)
        
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
        self._check_destination(clean_id)

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

        created_db = self.client.databases.create(
            parent=parent,
            title=title_arr,
            is_inline=is_inline,
            initial_data_source={"properties": formatted_props}
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
            "view_type": norm_view if created_view_id or norm_view == "table" else "table",
            "requested_view_type": norm_view,
            "view_id": created_view_id,
            "status": "created" if created_view_id or norm_view == "table" else "partial"
        }

notion_service = NotionService()
