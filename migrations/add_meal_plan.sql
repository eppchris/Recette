-- Table de planification des repas quotidiens (indépendante des événements)
CREATE TABLE IF NOT EXISTS meal_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT NOT NULL,
    meal_type TEXT NOT NULL DEFAULT 'dinner',
    recipe_id INTEGER,
    free_text TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(id),
    CHECK (recipe_id IS NOT NULL OR free_text IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_meal_plan_date ON meal_plan(date);
CREATE INDEX IF NOT EXISTS idx_meal_plan_user_date ON meal_plan(user_id, date);
