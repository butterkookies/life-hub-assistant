"""Regression coverage for canonical destinations and real project/task records."""

from unittest.mock import MagicMock

import pytest

from notion_service import NotionService


@pytest.fixture
def service():
    service = NotionService(api_key="fake")
    service.client = MagicMock()
    service.client.data_sources.retrieve.return_value = {
        "id": service.TASKS_DATA_SOURCE_ID,
        "properties": {
            "Name": {"type": "title"},
            "Status": {"type": "status", "status": {"options": [{"name": "Not started"}]}},
            "Do Date": {"type": "date"},
            "Projects": {"type": "relation"},
        },
    }
    service.client.pages.create.return_value = {"id": "new-page", "url": "https://notion.so/new-page"}
    service.client.blocks.children.list.return_value = {"results": [], "has_more": False}
    return service


def test_task_is_row_in_manager_with_project_and_date(service):
    service.client.pages.retrieve.return_value = {
        "parent": {"data_source_id": service.PROJECTS_DATA_SOURCE_ID}
    }
    result = service.create_task("Submit report", "2026-09-06", "project-id")
    payload = service.client.pages.create.call_args.kwargs
    assert payload["parent"] == {"data_source_id": service.TASKS_DATA_SOURCE_ID}
    assert payload["properties"]["Projects"] == {"relation": [{"id": "projectid"}]}
    assert payload["properties"]["Do Date"] == {"date": {"start": "2026-09-06"}}
    assert result["data_source_id"] == service.TASKS_DATA_SOURCE_ID
    service.client.blocks.children.append.assert_not_called()


def test_unknown_field_fails_before_writing_instead_of_dropping_it(service):
    with pytest.raises(ValueError, match="Priority"):
        service.create_database_item(service.TASKS_DATA_SOURCE_ID, "Task", properties={"Priority": "High"})
    service.client.pages.create.assert_not_called()


def test_write_error_does_not_retry_with_missing_fields(service):
    service.client.pages.create.side_effect = TimeoutError("response lost")
    with pytest.raises(TimeoutError):
        service.create_database_item(service.TASKS_DATA_SOURCE_ID, "Task", properties={"Do Date": "2026-09-06"})
    assert service.client.pages.create.call_count == 1


def test_empty_master_tasks_does_not_fall_back_to_legacy_search(service):
    service.query_database = MagicMock(return_value=[])
    service.search_workspace = MagicMock()
    assert service.get_calendar_schedule("2026-09-06") == []
    assert service.get_tasks_for_day("2026-09-06") == []
    service.search_workspace.assert_not_called()


def test_legacy_database_rejected_before_write(service):
    with pytest.raises(ValueError, match="legacy"):
        service.create_database_item("a6494cb1b0994c41897a6ffb6b4a476a", "Task")
    service.client.pages.create.assert_not_called()


def test_project_creation_includes_filtered_shared_view(service):
    service.query_database = MagicMock(return_value=[])
    service.create_database_item = MagicMock(return_value={"id": "project-id", "url": "https://notion.so/project-id", "status": "created"})
    service.ensure_project_tasks_view = MagicMock(return_value={"status": "ready", "view_id": "view-id"})
    result = service.create_project("New app")
    assert service.create_database_item.call_args.args[0] == service.PROJECTS_DATA_SOURCE_ID
    service.ensure_project_tasks_view.assert_called_once_with("project-id", "table")
    assert result["status"] == "created"
    service.client.databases.create.assert_not_called()


def test_view_failure_reports_partial_project_and_preserves_repair_id(service):
    service.query_database = MagicMock(return_value=[])
    service.create_database_item = MagicMock(return_value={"id": "project-id", "status": "created"})
    service.ensure_project_tasks_view = MagicMock(side_effect=RuntimeError("view unavailable"))
    result = service.create_project("New app")
    assert result["status"] == "partial"
    assert result["id"] == "project-id"
    assert "ensure_project_tasks_view" in result["next_step"]


def test_linked_view_uses_shared_source_and_project_filter(service):
    service.client.pages.retrieve.return_value = {"parent": {"data_source_id": service.PROJECTS_DATA_SOURCE_ID}}
    service.client.views.list.return_value = {"results": [], "has_more": False}
    service.client.views.create.return_value = {"id": "view-id", "url": "https://notion.so/view-id"}
    result = service.ensure_project_tasks_view("project-id")
    args = service.client.views.create.call_args.kwargs
    assert args["data_source_id"] == service.TASKS_DATA_SOURCE_ID
    assert args["create_database"]["parent"]["page_id"] == "projectid"
    assert args["filter"] == {"property": "Projects", "relation": {"contains": "projectid"}}
    assert result["status"] == "ready"
    service.client.databases.create.assert_not_called()


def test_task_rejects_project_from_other_database(service):
    service.client.pages.retrieve.return_value = {"parent": {"data_source_id": "legacy-projects"}}
    with pytest.raises(ValueError, match="Projects"):
        service.create_task("Task", project_id="wrong-project")
    service.client.pages.create.assert_not_called()


def test_query_failure_is_not_reported_as_empty_database(service):
    service.client.data_sources.query.side_effect = RuntimeError("Notion unavailable")
    with pytest.raises(RuntimeError, match="Notion unavailable"):
        service.query_database(service.TASKS_DATA_SOURCE_ID)


def test_custom_title_and_date_columns_use_real_schema(service):
    service.client.data_sources.retrieve.return_value = {
        "id": service.TASKS_DATA_SOURCE_ID,
        "properties": {"Task": {"type": "title"}, "Due Date": {"type": "date"}},
    }
    service.create_database_item(service.TASKS_DATA_SOURCE_ID, "Task", properties={"Due Date": "2026-09-06"})
    props = service.client.pages.create.call_args.kwargs["properties"]
    assert "Task" in props and "Name" not in props
    assert props["Due Date"] == {"date": {"start": "2026-09-06"}}


def test_existing_view_is_reused_with_encoded_property_id(service):
    service.client.pages.retrieve.return_value = {"parent": {"data_source_id": service.PROJECTS_DATA_SOURCE_ID}}
    service.client.data_sources.retrieve.return_value["properties"]["Projects"]["id"] = "J%3Fl%7B"
    service.client.blocks.children.list.return_value = {"results": [{"type": "child_database", "id": "linked-db"}]}
    service.client.views.list.return_value = {"results": [{"id": "existing-view"}]}
    service.client.views.retrieve.return_value = {
        "id": "existing-view", "type": "table", "data_source_id": service.TASKS_DATA_SOURCE_ID,
        "filter": {"property": "J?l{", "relation": {"contains": "project-id"}},
    }
    result = service.ensure_project_tasks_view("project-id")
    assert result["reused"]
    service.client.views.create.assert_not_called()


def test_existing_project_is_repaired_without_duplicate(service):
    service.query_database = MagicMock(return_value=[{"id": "existing-project", "properties": {"Name": "App"}}])
    service.ensure_project_tasks_view = MagicMock(return_value={"status": "ready"})
    result = service.create_project("App")
    assert result["status"] == "existing"
    service.client.pages.create.assert_not_called()
    service.ensure_project_tasks_view.assert_called_once_with("existing-project", "table")


def test_search_paginates_and_retains_parent_locations(service):
    service.client.search.side_effect = [
        {"results": [{"id": "legacy", "object": "page", "parent": {"page_id": "old-root"}}], "has_more": True, "next_cursor": "next"},
        {"results": [{"id": service.ROOT_PAGE_ID, "object": "page", "parent": {"workspace": True}}], "has_more": False},
    ]
    results = service.search_workspace("Life Hub")
    assert results[0]["is_canonical"]
    assert results[1]["parent"] == {"page_id": "old-root"}
    assert service.client.search.call_args.kwargs["start_cursor"] == "next"


def test_checkboxes_cannot_substitute_for_task_rows(service):
    with pytest.raises(ValueError, match="create_task"):
        service.append_to_page(service.ROOT_PAGE_ID, "- [ ] Submit report")
    service.client.blocks.children.append.assert_not_called()
