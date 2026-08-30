var G = Object.defineProperty;
var $ = (s, t, o) => t in s ? G(s, t, { enumerable: !0, configurable: !0, writable: !0, value: o }) : s[t] = o;
var P = (s, t, o) => $(s, typeof t != "symbol" ? t + "" : t, o);
import { app as y, BrowserWindow as K, globalShortcut as q, ipcMain as g, shell as Q, screen as X, Tray as Z, nativeImage as R, Menu as ee } from "electron";
import * as h from "path";
import * as S from "fs";
import { Client as te } from "@notionhq/client";
import * as se from "dotenv";
import { fileURLToPath as H } from "url";
const oe = () => {
  try {
    return h.dirname(H(import.meta.url));
  } catch {
    return process.cwd();
  }
}, U = oe(), ne = [
  h.resolve(U, "../../.env"),
  h.resolve(U, "../.env"),
  h.resolve(process.cwd(), "../.env"),
  h.resolve(process.cwd(), ".env")
];
for (const s of ne)
  if (S.existsSync(s)) {
    se.config({ path: s });
    break;
  }
const ae = process.env.NOTION_API_KEY || "", z = "d1527102528783299cac81b9d565b99b", re = "ba427102528782efbdce815b505396a2";
class ie {
  constructor() {
    P(this, "client", null);
    P(this, "projectsCache", /* @__PURE__ */ new Map());
  }
  getClient() {
    if (!this.client) {
      const t = process.env.NOTION_API_KEY || ae;
      if (!t)
        throw new Error("NOTION_API_KEY is not configured in .env");
      this.client = new te({ auth: t });
    }
    return this.client;
  }
  async getProjects() {
    const t = this.getClient(), o = re.replace(/-/g, "");
    try {
      const n = (await t.databases.query({
        database_id: o,
        page_size: 100
      })).results || [], i = [];
      for (const c of n) {
        const l = c.id;
        let a = "Untitled Project";
        const p = c.properties || {};
        for (const u of Object.values(p))
          if (u.type === "title") {
            const d = u.title || [];
            d.length > 0 && (a = d.map((x) => x.plain_text || "").join(""));
            break;
          }
        i.push({ id: l, name: a }), this.projectsCache.set(l, a), this.projectsCache.set(l.replace(/-/g, ""), a);
      }
      return i;
    } catch (r) {
      return console.error("Error fetching Notion projects:", r), [];
    }
  }
  async getTasks(t) {
    var n, i, c;
    const o = this.getClient(), r = z.replace(/-/g, "");
    this.projectsCache.size === 0 && await this.getProjects();
    try {
      const a = (await o.databases.query({
        database_id: r,
        page_size: 100
      })).results || [], p = [];
      for (const u of a) {
        const d = u.properties || {};
        if (((n = d.Archive) == null ? void 0 : n.checkbox) || !1) continue;
        let E = "Untitled Task";
        const I = d.Name || d.Task || d.Title;
        (I == null ? void 0 : I.type) === "title" && (E = (I.title || []).map((w) => w.plain_text || "").join(""));
        let O = null;
        const k = d["Do Date"] || d.Date || d["Due Date"];
        (k == null ? void 0 : k.type) === "date" && k.date && (O = k.date.start || null);
        let N = "Not started";
        const f = d.Status;
        (f == null ? void 0 : f.type) === "status" && f.status ? N = f.status.name || "Not started" : (f == null ? void 0 : f.type) === "select" && f.select && (N = f.select.name || "Not started");
        let W = "Normal";
        const b = d.Priority;
        (b == null ? void 0 : b.type) === "select" && b.select && (W = b.select.name || "Normal");
        let F = null, L = "Personal";
        const v = d.Projects || d.Project;
        if ((v == null ? void 0 : v.type) === "relation" && ((i = v.relation) == null ? void 0 : i.length) > 0) {
          const w = (c = v.relation[0]) == null ? void 0 : c.id;
          if (w) {
            F = w;
            const J = w.replace(/-/g, "");
            L = this.projectsCache.get(w) || this.projectsCache.get(J) || "Project";
          }
        }
        const M = {
          id: u.id,
          name: E || "Untitled Task",
          date: O,
          status: N,
          priority: W,
          projectId: F,
          projectName: L,
          url: u.url,
          properties: d
        };
        t ? O && O.startsWith(t) && p.push(M) : p.push(M);
      }
      return p;
    } catch (l) {
      return console.error("Error fetching Notion tasks:", l), [];
    }
  }
  async updateTaskStatus(t, o) {
    const r = this.getClient(), n = t.replace(/-/g, "");
    try {
      return await r.pages.update({
        page_id: n,
        properties: {
          Status: {
            status: {
              name: o
            }
          }
        }
      }), !0;
    } catch (i) {
      console.error(`Error updating task ${t} status:`, i);
      try {
        return await r.pages.update({
          page_id: n,
          properties: {
            Status: {
              select: {
                name: o
              }
            }
          }
        }), !0;
      } catch (c) {
        throw console.error("Fallback select update also failed:", c), c;
      }
    }
  }
  async createTask(t, o, r, n) {
    const i = this.getClient(), c = z.replace(/-/g, ""), l = {
      Name: {
        title: [
          {
            text: {
              content: t
            }
          }
        ]
      },
      Status: {
        status: {
          name: "Not started"
        }
      }
    };
    n && (l["Do Date"] = {
      date: {
        start: n
      }
    }), r && (l.Priority = {
      select: {
        name: r
      }
    }), o && (l.Projects = {
      relation: [
        {
          id: o.replace(/-/g, "")
        }
      ]
    });
    const a = await i.pages.create({
      parent: { database_id: c },
      properties: l
    }), p = o ? this.projectsCache.get(o) || this.projectsCache.get(o.replace(/-/g, "")) || "Project" : "Personal";
    return {
      id: a.id,
      name: t,
      status: "Not started",
      priority: r || "Normal",
      date: n || null,
      projectId: o || null,
      projectName: p,
      url: a.url,
      properties: l
    };
  }
  async getPagePreview(t) {
    const o = this.getClient(), r = t.replace(/-/g, ""), n = await o.pages.retrieve({ page_id: r });
    let i = "Untitled";
    for (const a of Object.values(n.properties || {}))
      if (a.type === "title") {
        i = (a.title || []).map((p) => p.plain_text || "").join("");
        break;
      }
    const c = await o.blocks.children.list({
      block_id: r,
      page_size: 50
    }), l = [];
    for (const a of c.results || []) {
      const p = a.type, u = a[p] || {}, d = (u.rich_text || []).map((x) => x.plain_text || "").join("");
      l.push({
        id: a.id,
        type: p,
        text: d,
        checked: u.checked
      });
    }
    return {
      id: n.id,
      title: i || "Untitled",
      url: n.url,
      blocks: l
    };
  }
}
const _ = new ie(), ce = () => {
  try {
    return h.dirname(H(import.meta.url));
  } catch {
    return process.cwd();
  }
}, C = ce();
process.env.DIST = h.join(C, "../dist");
process.env.VITE_PUBLIC = y.isPackaged ? process.env.DIST : h.join(process.env.DIST, "../public");
let e = null, m = null;
const V = process.env.VITE_DEV_SERVER_URL, D = h.join(y.getPath("userData"), "widget_config.json"), B = {
  x: 100,
  y: 100,
  width: 420,
  height: 640,
  alwaysOnTop: !1,
  theme: "light",
  opacity: 0.98,
  autoRefreshMinutes: 5,
  showCompleted: !0,
  startWithWindows: !1,
  filterMode: "today"
};
function T() {
  try {
    if (S.existsSync(D)) {
      const s = JSON.parse(S.readFileSync(D, "utf-8"));
      return { ...B, ...s };
    }
  } catch (s) {
    console.error("Error loading config:", s);
  }
  return B;
}
function j(s) {
  try {
    const o = { ...T(), ...s };
    S.writeFileSync(D, JSON.stringify(o, null, 2), "utf-8");
  } catch (t) {
    console.error("Error saving config:", t);
  }
}
function Y() {
  const s = [
    h.join(C, "../icon.png"),
    h.join(C, "../../icon.png"),
    h.join(process.cwd(), "icon.png")
  ];
  for (const t of s)
    if (S.existsSync(t)) {
      const o = R.createFromPath(t);
      if (!o.isEmpty()) return o;
    }
  return R.createEmpty();
}
function A() {
  const s = T(), t = X.getPrimaryDisplay(), { width: o, height: r } = t.workAreaSize;
  Math.min(Math.max(s.width || 420, 360), 600), Math.min(Math.max(s.height || 640, 480), 900), s.x, s.y;
  const n = !s.x || s.x <= 0, i = Y();
  e = new K({
    width: 430,
    height: 670,
    center: n,
    x: n ? void 0 : s.x,
    y: n ? void 0 : s.y,
    minWidth: 360,
    minHeight: 480,
    maxWidth: 700,
    maxHeight: 1e3,
    frame: !1,
    transparent: !0,
    hasShadow: !0,
    alwaysOnTop: s.alwaysOnTop ?? !0,
    resizable: !0,
    skipTaskbar: !1,
    show: !0,
    icon: i,
    title: "Notion Tasks Widget",
    webPreferences: {
      preload: h.join(C, "preload.cjs"),
      nodeIntegration: !1,
      contextIsolation: !0,
      sandbox: !1
    }
  }), e.show(), e.restore(), e.focus(), e.moveTop();
  const c = () => {
    if (e && !e.isDestroyed()) {
      const a = e.getBounds();
      j({
        x: a.x,
        y: a.y,
        width: a.width,
        height: a.height
      });
    }
  };
  e.on("moved", c), e.on("resized", c);
  const l = h.join(process.env.DIST, "index.html");
  V ? e.loadURL(V) : e.loadFile(l), e.webContents.on("did-finish-load", () => {
    console.log("Widget UI loaded successfully"), e == null || e.show(), e == null || e.focus();
  }), e.webContents.on("did-fail-load", (a, p, u) => {
    console.error("Failed to load widget UI:", p, u);
  });
}
function le() {
  const s = Y();
  m = new Z(s), m.setToolTip("Notion Tasks Desktop Widget (Click to Open)");
  const t = () => {
    !e || e.isDestroyed() ? A() : (e.isMinimized() && e.restore(), e.show(), e.focus(), e.moveTop(), e.setAlwaysOnTop(!0), setTimeout(() => {
      const r = T();
      e && !e.isDestroyed() && e.setAlwaysOnTop(r.alwaysOnTop);
    }, 500));
  }, o = () => {
    const r = T(), n = ee.buildFromTemplate([
      {
        label: "📋 Show Tasks Widget",
        click: t
      },
      {
        label: "🔄 Refresh Tasks Now",
        click: () => {
          t(), e == null || e.webContents.send("trigger-refresh");
        }
      },
      {
        label: "➕ Add Task for Today...",
        click: () => {
          t(), e == null || e.webContents.send("trigger-quick-add");
        }
      },
      { type: "separator" },
      {
        label: "📌 Always on Top",
        type: "checkbox",
        checked: r.alwaysOnTop,
        click: (i) => {
          const c = i.checked;
          e == null || e.setAlwaysOnTop(c), j({ alwaysOnTop: c }), e == null || e.webContents.send("config-updated", { alwaysOnTop: c });
        }
      },
      {
        label: "🚀 Launch on Windows Startup",
        type: "checkbox",
        checked: y.getLoginItemSettings().openAtLogin,
        click: (i) => {
          y.setLoginItemSettings({
            openAtLogin: i.checked,
            path: process.execPath
          }), j({ startWithWindows: i.checked });
        }
      },
      { type: "separator" },
      {
        label: "❌ Exit Widget",
        click: () => {
          y.quit();
        }
      }
    ]);
    m == null || m.setContextMenu(n);
  };
  m.on("click", t), m.on("double-click", t), o();
}
function de() {
  const s = () => {
    !e || e.isDestroyed() ? A() : !e.isVisible() || e.isMinimized() ? (e.restore(), e.show(), e.focus(), e.moveTop()) : e.isFocused() ? e.minimize() : (e.focus(), e.moveTop());
  };
  try {
    q.register("CommandOrControl+Shift+T", s), console.log("Registered global shortcut: Ctrl+Shift+T");
  } catch (t) {
    console.error("Failed to register global shortcut:", t);
  }
}
function pe() {
  g.handle("get-config", async () => T()), g.handle("save-config", async (s, t) => (j(t), t.alwaysOnTop !== void 0 && (e == null || e.setAlwaysOnTop(t.alwaysOnTop)), t.opacity !== void 0 && (e == null || e.setOpacity(t.opacity)), t.startWithWindows !== void 0 && y.setLoginItemSettings({
    openAtLogin: t.startWithWindows,
    path: process.execPath
  }), T())), g.on("window-minimize", () => {
    e == null || e.hide();
  }), g.on("window-close", () => {
    e == null || e.hide();
  }), g.on("window-set-topmost", (s, t) => {
    e == null || e.setAlwaysOnTop(t), j({ alwaysOnTop: t });
  }), g.handle("get-projects", async () => await _.getProjects()), g.handle("get-tasks", async (s, t) => await _.getTasks(t)), g.handle("update-task-status", async (s, t, o) => await _.updateTaskStatus(t, o)), g.handle(
    "create-task",
    async (s, t, o, r, n) => await _.createTask(t, o, r, n)
  ), g.handle("get-page-preview", async (s, t) => await _.getPagePreview(t)), g.on("open-external-url", (s, t) => {
    t && Q.openExternal(t);
  });
}
y.whenReady().then(() => {
  pe(), A(), le(), de(), y.on("activate", () => {
    K.getAllWindows().length === 0 && A();
  });
});
y.on("will-quit", () => {
  q.unregisterAll();
});
y.on("window-all-closed", () => {
  process.platform;
});
