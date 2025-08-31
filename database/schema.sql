CREATE TABLE IF NOT EXISTS mc_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    z INTEGER NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);