-- Migration : table des photos d'événements
CREATE TABLE IF NOT EXISTS event_photo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    photo_url TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_event_photo_event ON event_photo(event_id);
