import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001/api";

export default function App() {
  const [opportunities, setOpportunities] = useState([]);
  const [filters, setFilters] = useState({ sources: [], keywords: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Control state
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [keywordFilter, setKeywordFilter] = useState('');

  // Helper to extract clean domain name safely
  const getDomain = (urlStr) => {
    try {
      return new URL(urlStr).hostname.replace('www.', '');
    } catch (e) {
      return urlStr || 'Direct Link';
    }
  };

  // Fetch available dropdown options on mount
  useEffect(() => {
    fetch(`${API_BASE}/filters`)
      .then(res => res.json())
      .then(data => setFilters({ sources: data.sources || [], keywords: data.keywords || [] }))
      .catch(err => console.error("Filter init failed:", err));
  }, []);

  // Reactive data fetching when filters change
  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (sourceFilter) params.append('source', sourceFilter);
    if (keywordFilter) params.append('keyword', keywordFilter);

    fetch(`${API_BASE}/opportunities?${params.toString()}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then(data => {
        setOpportunities(data);
        setLoading(false);
        setError(null);
      })
      .catch(err => {
        console.error("Data fetch failed:", err);
        setError(`Unable to connect to Scout API server (${API_BASE})`);
        setLoading(false);
      });
  }, [search, sourceFilter, keywordFilter]);

  const resetFilters = () => {
    setSearch('');
    setSourceFilter('');
    setKeywordFilter('');
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-badge">Autonomous Scouting Engine</div>
        <h1>Target Opportunities</h1>
        <p>Displaying <strong>{opportunities.length}</strong> relevant results</p>

        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-value">{opportunities.length}</span>
            <span className="stat-label">Active Matches</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{filters.sources.length}</span>
            <span className="stat-label">Ingestion Feeds</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{filters.keywords.length}</span>
            <span className="stat-label">Target Keywords</span>
          </div>
        </div>
      </header>

      <section className="controls">
        <div className="search-wrapper">
          <input 
            type="text" 
            placeholder="Search by keyword or context..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && <button className="clear-search" onClick={() => setSearch('')}>×</button>}
        </div>
        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
          <option value="">Filter: All Sources</option>
          {filters.sources.map(src => (
            <option key={src} value={src}>{getDomain(src)}</option>
          ))}
        </select>
        <select value={keywordFilter} onChange={(e) => setKeywordFilter(e.target.value)}>
          <option value="">Filter: All Keywords</option>
          {filters.keywords.map(kw => (
            <option key={kw} value={kw}>{kw}</option>
          ))}
        </select>
        {(search || sourceFilter || keywordFilter) && (
          <button className="reset-btn" onClick={resetFilters}>Reset</button>
        )}
      </section>

      {error && (
        <div className="error-banner">
          ⚠️ {error}. Ensure FastAPI backend is running on port 8001.
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Scouting records...</p>
        </div>
      ) : opportunities.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h3>No matching opportunities found</h3>
          <p>Try adjusting your search terms or filters.</p>
          <button onClick={resetFilters} className="primary-btn">Clear All Filters</button>
        </div>
      ) : (
        <main className="results-grid">
          {opportunities.map(item => (
            <article key={item.id} className="opportunity-card">
              <header className="card-meta">
                <time className="date">{item.date_discovered}</time>
                <span className="source-badge">{getDomain(item.source)}</span>
              </header>
              <h2>
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
              </h2>
              <p className="snippet">{item.snippet}</p>
              <footer className="tags">
                {item.matched_keywords && item.matched_keywords.split(',').map(tag => (
                  <span key={tag.trim()} className="tag">{tag.trim()}</span>
                ))}
              </footer>
            </article>
          ))}
        </main>
      )}
    </div>
  );
}
