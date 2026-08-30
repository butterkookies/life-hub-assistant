import { Client } from '@notionhq/client';
import * as dotenv from 'dotenv';
import * as path from 'path';
import * as fs from 'fs';
import { NotionTask, NotionProject, PagePreviewData, PageBlock } from './types';

import { fileURLToPath } from 'url';

// Resolve directory safely in ESM and CJS
const getDirname = () => {
  try {
    return path.dirname(fileURLToPath(import.meta.url));
  } catch {
    return process.cwd();
  }
};

const baseDir = getDirname();
const possibleEnvPaths = [
  path.resolve(baseDir, '../../.env'),
  path.resolve(baseDir, '../.env'),
  path.resolve(process.cwd(), '../.env'),
  path.resolve(process.cwd(), '.env'),
];

for (const p of possibleEnvPaths) {
  if (fs.existsSync(p)) {
    dotenv.config({ path: p });
    break;
  }
}

const NOTION_API_KEY = process.env.NOTION_API_KEY || '';
const TASKS_DATABASE_ID = 'd1527102528783299cac81b9d565b99b';
const PROJECTS_DATABASE_ID = 'ba427102528782efbdce815b505396a2';

const KNOWN_DATA_SOURCES: Record<string, string> = {
  'd1527102528783299cac81b9d565b99b': '96927102528782d9bed487a7322ac310',
  'ba427102528782efbdce815b505396a2': '59827102528783dbb9e807b71c738058',
};

class NotionService {
  private client: Client | null = null;
  private projectsCache: Map<string, string> = new Map();

  private getClient(): Client {
    if (!this.client) {
      const apiKey = process.env.NOTION_API_KEY || NOTION_API_KEY;
      if (!apiKey) {
        throw new Error('NOTION_API_KEY is not configured in .env');
      }
      this.client = new Client({ auth: apiKey });
    }
    return this.client;
  }

  async getProjects(): Promise<NotionProject[]> {
    const client = this.getClient();
    const cleanId = PROJECTS_DATABASE_ID.replace(/-/g, '');

    try {
      const resp = await client.databases.query({
        database_id: cleanId,
        page_size: 100,
      });
      const results = resp.results || [];

      const projects: NotionProject[] = [];
      for (const item of results as any[]) {
        const id = item.id;
        let name = 'Untitled Project';
        const props = item.properties || {};
        for (const val of Object.values(props) as any[]) {
          if (val.type === 'title') {
            const arr = val.title || [];
            if (arr.length > 0) {
              name = arr.map((t: any) => t.plain_text || '').join('');
            }
            break;
          }
        }
        projects.push({ id, name });
        this.projectsCache.set(id, name);
        this.projectsCache.set(id.replace(/-/g, ''), name);
      }
      return projects;
    } catch (err) {
      console.error('Error fetching Notion projects:', err);
      return [];
    }
  }

  async getTasks(targetDate?: string): Promise<NotionTask[]> {
    const client = this.getClient();
    const cleanId = TASKS_DATABASE_ID.replace(/-/g, '');

    // Refresh projects map in background if empty
    if (this.projectsCache.size === 0) {
      await this.getProjects();
    }

    try {
      const resp = await client.databases.query({
        database_id: cleanId,
        page_size: 100,
      });
      const results = resp.results || [];

      const tasks: NotionTask[] = [];
      for (const item of results as any[]) {
        const props = item.properties || {};
        const isArchived = props.Archive?.checkbox || false;
        if (isArchived) continue;

        // Name
        let name = 'Untitled Task';
        const nameProp = props.Name || props.Task || props.Title;
        if (nameProp?.type === 'title') {
          name = (nameProp.title || []).map((t: any) => t.plain_text || '').join('');
        }

        // Do Date
        let doDate: string | null = null;
        const dateProp = props['Do Date'] || props.Date || props['Due Date'];
        if (dateProp?.type === 'date' && dateProp.date) {
          doDate = dateProp.date.start || null;
        }

        // Status
        let status = 'Not started';
        const statusProp = props.Status;
        if (statusProp?.type === 'status' && statusProp.status) {
          status = statusProp.status.name || 'Not started';
        } else if (statusProp?.type === 'select' && statusProp.select) {
          status = statusProp.select.name || 'Not started';
        }

        // Priority
        let priority = 'Normal';
        const prioProp = props.Priority;
        if (prioProp?.type === 'select' && prioProp.select) {
          priority = prioProp.select.name || 'Normal';
        }

        // Project Relation
        let projectId: string | null = null;
        let projectName = 'Personal';
        const relProp = props.Projects || props.Project;
        if (relProp?.type === 'relation' && relProp.relation?.length > 0) {
          const rawId = relProp.relation[0]?.id;
          if (rawId) {
            projectId = rawId;
            const cleanPId = rawId.replace(/-/g, '');
            projectName = this.projectsCache.get(rawId) || this.projectsCache.get(cleanPId) || 'Project';
          }
        }

        const taskItem: NotionTask = {
          id: item.id,
          name: name || 'Untitled Task',
          date: doDate,
          status,
          priority,
          projectId,
          projectName,
          url: item.url,
          properties: props,
        };

        if (targetDate) {
          if (doDate && doDate.startsWith(targetDate)) {
            tasks.push(taskItem);
          }
        } else {
          tasks.push(taskItem);
        }
      }
      return tasks;
    } catch (err) {
      console.error('Error fetching Notion tasks:', err);
      return [];
    }
  }

  async updateTaskStatus(taskId: string, newStatus: string): Promise<boolean> {
    const client = this.getClient();
    const cleanId = taskId.replace(/-/g, '');
    try {
      await client.pages.update({
        page_id: cleanId,
        properties: {
          Status: {
            status: {
              name: newStatus,
            },
          },
        },
      });
      return true;
    } catch (err) {
      console.error(`Error updating task ${taskId} status:`, err);
      // Fallback try select
      try {
        await client.pages.update({
          page_id: cleanId,
          properties: {
            Status: {
              select: {
                name: newStatus,
              },
            },
          },
        });
        return true;
      } catch (err2) {
        console.error(`Fallback select update also failed:`, err2);
        throw err2;
      }
    }
  }

  async createTask(
    title: string,
    projectId?: string,
    priority?: string,
    doDate?: string
  ): Promise<NotionTask> {
    const client = this.getClient();
    const cleanDbId = TASKS_DATABASE_ID.replace(/-/g, '');

    const properties: any = {
      Name: {
        title: [
          {
            text: {
              content: title,
            },
          },
        ],
      },
      Status: {
        status: {
          name: 'Not started',
        },
      },
    };

    if (doDate) {
      properties['Do Date'] = {
        date: {
          start: doDate,
        },
      };
    }

    if (priority) {
      properties['Priority'] = {
        select: {
          name: priority,
        },
      };
    }

    if (projectId) {
      properties['Projects'] = {
        relation: [
          {
            id: projectId.replace(/-/g, ''),
          },
        ],
      };
    }

    const created: any = await client.pages.create({
      parent: { database_id: cleanDbId },
      properties,
    });

    const projectName = projectId
      ? this.projectsCache.get(projectId) || this.projectsCache.get(projectId.replace(/-/g, '')) || 'Project'
      : 'Personal';

    return {
      id: created.id,
      name: title,
      status: 'Not started',
      priority: priority || 'Normal',
      date: doDate || null,
      projectId: projectId || null,
      projectName,
      url: created.url,
      properties,
    };
  }

  async getPagePreview(pageId: string): Promise<PagePreviewData> {
    const client = this.getClient();
    const cleanId = pageId.replace(/-/g, '');

    const page: any = await client.pages.retrieve({ page_id: cleanId });
    let title = 'Untitled';
    for (const val of Object.values(page.properties || {}) as any[]) {
      if (val.type === 'title') {
        title = (val.title || []).map((t: any) => t.plain_text || '').join('');
        break;
      }
    }

    const blocksResp: any = await client.blocks.children.list({
      block_id: cleanId,
      page_size: 50,
    });

    const blocks: PageBlock[] = [];
    for (const block of blocksResp.results || []) {
      const type = block.type;
      const data = block[type] || {};
      const text = (data.rich_text || []).map((t: any) => t.plain_text || '').join('');
      blocks.push({
        id: block.id,
        type,
        text,
        checked: data.checked,
      });
    }

    return {
      id: page.id,
      title: title || 'Untitled',
      url: page.url,
      blocks,
    };
  }
}

export const notionService = new NotionService();
