from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from typing import Optional
import os

app = FastAPI(title="Scout Agent API", description="Exposes scouted opportunities to the dashboard.")

# CORS is required for local React development (React runs on 5173, FastAPI on 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict to your frontend domain
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
