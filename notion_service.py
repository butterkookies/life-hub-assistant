import json
import logging
from typing import Dict, Any, List, Optional
from notion_client import Client
from config import settings

logger = logging.getLogger("notion_service")

class NotionService:
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

    def query_database(self, database_id: str, filter_json: Optional[Dict] = None, page_size: int = 10) -> List[Dict[str, Any]]:
        """Query items in a Notion database."""
        self._ensure_client()
        clean_id = database_id.replace("-", "")
        body: Dict[str, Any] = {"page_size": min(page_size, 50)}
        if filter_json:
            body["filter"] = filter_json

        try:
            response = self.client.data_sources.query(data_source_id=clean_id, **body)
        except Exception:
            try:
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
            
            items.append({
                "id": page.get("id"),
                "url": page.get("url"),
                "properties": page_props
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

notion_service = NotionService()
