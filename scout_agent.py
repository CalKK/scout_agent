import json
import sqlite3
import datetime
import urllib.request
import urllib.parse
import time
import requests
import feedparser
import sys
from bs4 import BeautifulSoup

# Ensure UTF-8 output formatting for Windows command prompt print compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = 'scout_data.db'
CONFIG_FILE = 'config.json'


# ==========================================
# DATABASE LOGIC
# ==========================================
def init_db():
    """Initializes the SQLite database with robust deduplication via UNIQUE constraint."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                snippet TEXT,
                source TEXT,
                matched_keywords TEXT,
                date_discovered DATE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                sources_checked INTEGER,
                items_found INTEGER,
                errors TEXT
            )
        ''')
        conn.commit()

def save_opportunity(conn, title, url, snippet, source, keywords):
    """Saves to DB. Returns True if inserted, False if duplicate (IntegrityError)."""
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO opportunities (title, url, snippet, source, matched_keywords, date_discovered)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, url, snippet[:500], source, ", ".join(keywords), datetime.date.today()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# ==========================================
# INGESTION & FILTERING LOGIC
# ==========================================
def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def match_keywords(text, keywords):
    """Algorithm: Case-insensitive substring matching."""
    if not text: return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]

def ingest_rss(url, keywords, conn):
    """Parses an RSS/Atom feed and extracts standardized fields."""
    try:
        feed = feedparser.parse(url)
        found_count = 0
        for entry in feed.entries:
            title = entry.get('title', '')
            snippet = entry.get('summary', '') or entry.get('description', '')
            # Clean HTML tags from snippet if present
            if snippet:
                snippet = BeautifulSoup(snippet, 'html.parser').get_text(strip=True)
            link = entry.get('link', '')
            matched = match_keywords(title + " " + snippet, keywords)
            
            if matched and save_opportunity(conn, title, link, snippet, url, matched):
                found_count += 1
        return found_count
    except Exception as e:
        print(f"Error fetching RSS {url}: {e}")
        return 0

def ingest_html(url, keywords, conn):
    """Generic HTML scraper with basic anti-blocking headers."""
    found_count = 0
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req, timeout=15).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Target semantic text containers
        texts = soup.find_all(['h1', 'h2', 'h3', 'p'])
        
        for element in texts:
            text = element.get_text(strip=True)
            matched = match_keywords(text, keywords)
            if matched:
                a_tag = element.find_parent('a') or element.find('a')
                link = a_tag['href'] if a_tag and 'href' in a_tag.attrs else url
                if link.startswith('/'):
                    link = urllib.parse.urljoin(url, link)
                if save_opportunity(conn, text[:100] + "...", link, text, url, matched):
                    found_count += 1
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return -1
    return found_count

def run_scout_cycle():
    """Main ingestion orchestration."""
    config = load_config()
    init_db()
    keywords = config['keywords']
    total_found, sources_checked = 0, 0
    errors = []
    
    print(f"[{datetime.datetime.now()}] Starting scout cycle...")
    
    with sqlite3.connect(DB_FILE) as conn:
        for feed_url in config['sources']['rss_feeds']:
            sources_checked += 1
            total_found += ingest_rss(feed_url, keywords, conn)
            
        for site_url in config['sources']['scrape_sites']:
            sources_checked += 1
            count = ingest_html(site_url, keywords, conn)
            if count == -1:
                errors.append(f"Failed to scrape {site_url}")
            else:
                total_found += count

        # Log the run statistics
        c = conn.cursor()
        c.execute('''
            INSERT INTO run_logs (timestamp, sources_checked, items_found, errors)
            VALUES (?, ?, ?, ?)
        ''', (datetime.datetime.now(), sources_checked, total_found, str(errors)))
        conn.commit()
        
    print(f"Cycle complete. Scraped/updated opportunities into {DB_FILE}.")

# ==========================================
# NOTIFICATION LOGIC (WhatsApp)
# ==========================================
def generate_daily_whatsapp_summary():
    """Compiles the daily digest and dispatches it via CallMeBot with strict chunking limits."""
    config = load_config()
    one_day_ago = datetime.date.today() - datetime.timedelta(days=1)
    
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT title, url, source, matched_keywords 
            FROM opportunities WHERE date_discovered >= ?
        ''', (one_day_ago,))
        items = c.fetchall()
    
    if not items:
        print("No new opportunities today. Skipping WhatsApp message.")
        return
        
    # --- Chunking Algorithm ---
    MAX_CHARS = 3000 
    chunks = []
    current_chunk = f"🎯 *Daily Opportunity Scout* ({datetime.date.today()})\nFound {len(items)} items:\n\n"
    
    for title, url, source, kws in items:
        item_text = f"*{title}*\n🏷️ {kws}\n🔗 {url}\n\n"
        
        if len(current_chunk) + len(item_text) > MAX_CHARS:
            chunks.append(current_chunk)
            current_chunk = f"🎯 *Daily Scout (Cont.)*\n\n" + item_text
        else:
            current_chunk += item_text
            
    if current_chunk:
        chunks.append(current_chunk)

    # --- Dispatch Algorithm ---
    tw_config = config.get('whatsapp', {})
    api_url = "https://api.callmebot.com/whatsapp.php"
    
    print(f"Sending {len(chunks)} message chunk(s) to WhatsApp...")
    
    for index, chunk in enumerate(chunks):
        try:
            params = {
                "phone": tw_config.get('phone_number', ''),
                "text": chunk,
                "apikey": tw_config.get('api_key', '')
            }
            if tw_config.get('api_key') == "1203067" or not tw_config.get('api_key'):
                print(f"[CallMeBot Simulated Log - Chunk {index + 1}/{len(chunks)}]:\n{chunk}")
                continue

            response = requests.get(api_url, params=params, timeout=15)
            
            if response.status_code == 200:
                print(f"Chunk {index + 1}/{len(chunks)} sent successfully!")
            else:
                print(f"Failed to send chunk {index + 1}. Server: {response.text}")
                
            if index < len(chunks) - 1:
                time.sleep(3)
                
        except Exception as e:
            print(f"Failed to connect to WhatsApp API on chunk {index + 1}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--summary':
        generate_daily_whatsapp_summary()
    else:
        run_scout_cycle()
