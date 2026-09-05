import json
import unittest
from unittest.mock import MagicMock, patch

from notion_service import NotionService
import gemini_agent


class NotionCreateDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.service = NotionService(api_key='fake_key')
        self.service.client = MagicMock()

    def test_create_database_default_schema_and_view(self):
        self.service.client.databases.create.return_value = {
            'id': 'db-111',
            'url': 'https://notion.so/db-111',
            'data_sources': [{'id': 'ds-222', 'name': 'Project Tasks'}]
        }
        self.service.client.views.create.return_value = {'id': 'view-333', 'type': 'list'}

        res = self.service.create_database(
            parent_page_id='parent-page-000',
            title='Project Tasks',
            view_type='list'
        )

        self.assertEqual(res['id'], 'db-111')
        self.assertEqual(res['data_source_id'], 'ds-222')
        self.assertEqual(res['view_type'], 'list')
        self.assertEqual(res['view_id'], 'view-333')
        self.assertEqual(res['status'], 'created')

        call_kwargs = self.service.client.databases.create.call_args[1]
        self.assertIn('initial_data_source', call_kwargs)
        props = call_kwargs['initial_data_source']['properties']
        self.assertIn('Task', props)
        self.assertIn('Status', props)
        self.assertIn('Priority', props)

        self.service.client.views.create.assert_called_once_with(
            database_id='db-111',
            data_source_id='ds-222',
            name='Project Tasks (List View)',
            type='list',
            configuration={'type': 'list'}
        )

    def test_create_database_custom_shorthand_properties(self):
        self.service.client.databases.create.return_value = {
            'id': 'db-444',
            'url': 'https://notion.so/db-444',
            'data_sources': [{'id': 'ds-555'}]
        }

        res = self.service.create_database(
            parent_page_id='parent-page-000',
            title='Feature Backlog',
            properties={
                'Feature': 'title',
                'Status': 'status',
                'Priority': 'select',
                'Target Date': 'date',
                'Notes': 'rich_text'
            },
            view_type='board'
        )

        call_kwargs = self.service.client.databases.create.call_args[1]
        props = call_kwargs['initial_data_source']['properties']
        self.assertIn('Feature', props)
        self.assertIn('title', props['Feature'])
        self.assertIn('Status', props)
        self.assertIn('Target Date', props)
        self.assertIn('date', props['Target Date'])

    def test_gemini_tool_create_database_wrapper(self):
        with patch('gemini_agent.notion_service.create_database') as mock_create:
            mock_create.return_value = {'id': 'db-999', 'status': 'created', 'url': 'https://notion.so/db-999'}
            result_str = gemini_agent.create_database(
                parent_page_id='page-123',
                title='Tasks',
                properties_json='{"Task": "title", "Status": "status"}',
                view_type='gallery'
            )
            data = json.loads(result_str)
            self.assertEqual(data['id'], 'db-999')
            mock_create.assert_called_once_with(
                parent_page_id='page-123',
                title='Tasks',
                properties={'Task': 'title', 'Status': 'status'},
                view_type='gallery',
                is_inline=True
            )
