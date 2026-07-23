from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import Optional
import os
import asyncio
from contextlib import asynccontextmanager
from scout_agent import run_scout_cycle, generate_daily_whatsapp_summary, init_db

async def periodic_scout_task():
    """Background task that runs continuously on Railway every 6 hours."""
    # Run immediate cycle on startup
    await asyncio.sleep(5) # Brief delay to let server bind
    while True:
        try:
            print("[Railway Agent Service] Triggering automated scouting cycle...")
            run_scout_cycle()
            print("[Railway Agent Service] Dispatching daily WhatsApp summary...")
            generate_daily_whatsapp_summary()
        except Exception as e:
            print(f"[Railway Agent Service Error]: {e}")
        
        # Wait 6 hours (21,600 seconds) between scouting cycles
        await asyncio.sleep(21600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database and trigger background scouting loop
    init_db()
    task = asyncio.create_task(periodic_scout_task())
    yield
    # Shutdown: Cancel background task
    task.cancel()

app = FastAPI(
    title="Scout Agent API", 
    description="Exposes scouted opportunities to the dashboard.",
    lifespan=lifespan
)

# CORS is required for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to your Vercel/Netlify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = os.path.join(os.path.dirname(__file__), 'scout_data.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Returns dict-like objects
    return conn

@app.get("/api/filters")
def get_filters():
    """Analyzes the database to extract unique sources and keywords for frontend dropdown menus."""
    if not os.path.exists(DB_FILE):
        return {"sources": [], "keywords": []}
    with get_db_connection() as conn:
        sources = [row['source'] for row in conn.execute("SELECT DISTINCT source FROM opportunities").fetchall()]
        
        kws_raw = conn.execute("SELECT matched_keywords FROM opportunities").fetchall()
        keywords = set()
        for row in kws_raw:
            if row['matched_keywords']:
                for kw in row['matched_keywords'].split(','):
                    keywords.add(kw.strip())
                
    return {"sources": sorted(sources), "keywords": sorted(list(keywords))}

@app.get("/api/opportunities")
def get_opportunities(
    search: Optional[str] = None,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """Dynamic query endpoint supporting text search, exact source matching, and substring keyword matching."""
    if not os.path.exists(DB_FILE):
        return []
    with get_db_connection() as conn:
        query = "SELECT * FROM opportunities WHERE 1=1"
        params = []

        if search:
            query += " AND (title LIKE ? OR snippet LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if source:
            query += " AND source = ?"
            params.append(source)
        if keyword:
            query += " AND matched_keywords LIKE ?"
            params.append(f"%{keyword}%")

        query += " ORDER BY date_discovered DESC LIMIT ?"
        params.append(limit)

        items = conn.execute(query, params).fetchall()
        
    return [dict(item) for item in items]

@app.get("/api/health")
def health_check():
    """Diagnostic endpoint for Railway debugging."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    dist_path = os.path.join(app_dir, 'frontend', 'dist')
    return {
        "status": "ok",
        "app_dir": app_dir,
        "frontend_dist_path": dist_path,
        "frontend_dist_exists": os.path.exists(dist_path),
        "frontend_dist_contents": os.listdir(dist_path) if os.path.exists(dist_path) else [],
        "cwd": os.getcwd(),
        "cwd_contents": os.listdir(os.getcwd()),
    }

# ==========================================
# SERVE REACT FRONTEND STATIC FILES
# ==========================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Try multiple possible paths for the frontend dist
_app_dir = os.path.dirname(os.path.abspath(__file__))
_possible_paths = [
    os.path.join(_app_dir, 'frontend', 'dist'),
    os.path.join(os.getcwd(), 'frontend', 'dist'),
    '/app/frontend/dist',
]

FRONTEND_DIST = None
for _path in _possible_paths:
    if os.path.exists(_path) and os.path.isdir(_path):
        FRONTEND_DIST = _path
        break

if FRONTEND_DIST:
    print(f"[Frontend] Serving React build from: {FRONTEND_DIST}")
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api"):
            return None
        target_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(target_path) and os.path.isfile(target_path):
            return FileResponse(target_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    print(f"[Frontend] WARNING: frontend/dist not found. Checked paths: {_possible_paths}")

    @app.get("/")
    async def root_fallback():
        return HTMLResponse(
            "<h1>Scout Agent API is running</h1>"
            "<p>Frontend build not found. Visit <a href='/docs'>/docs</a> for API documentation.</p>"
            "<p>Visit <a href='/api/health'>/api/health</a> for diagnostics.</p>"
        )

