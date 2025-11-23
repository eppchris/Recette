-- Migration : Système de catégorisation et tags pour les recettes
-- Version 1.4 - Catégories et tags bilingues FR/JP
-- Date : 2025-11-23

-- ============================================================================
-- TABLE : categories (catégories principales : entrée, plat, dessert...)
-- ============================================================================
CREATE TABLE IF NOT EXISTS category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fr TEXT NOT NULL UNIQUE,
    name_jp TEXT NOT NULL,
    description_fr TEXT,
    description_jp TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE : tags (tags flexibles : viande, végétarien, rapide...)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_fr TEXT NOT NULL UNIQUE,
    name_jp TEXT NOT NULL,
    description_fr TEXT,
    description_jp TEXT,
    color TEXT DEFAULT '#3B82F6', -- Couleur hex pour l'affichage
    is_system BOOLEAN DEFAULT 0,   -- Tags système (non supprimables)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE : recipe_category (relation many-to-many)
-- Une recette peut avoir plusieurs catégories
-- ============================================================================
CREATE TABLE IF NOT EXISTS recipe_category (
    recipe_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (recipe_id, category_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLE : recipe_tag (relation many-to-many)
-- Une recette peut avoir plusieurs tags
-- ============================================================================
CREATE TABLE IF NOT EXISTS recipe_tag (
    recipe_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (recipe_id, tag_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- ============================================================================
-- DONNÉES : Catégories par défaut
-- ============================================================================
INSERT INTO category (name_fr, name_jp, description_fr, description_jp, display_order) VALUES
('Entrée', '前菜', 'Plats servis en début de repas', '食事の最初に提供される料理', 1),
('Plat principal', 'メイン料理', 'Plat principal du repas', '食事のメイン料理', 2),
('Accompagnement', '付け合わせ', 'Plats d''accompagnement', '副菜', 3),
('Dessert', 'デザート', 'Plats sucrés de fin de repas', '食後の甘い料理', 4),
('Sauce', 'ソース', 'Sauces et assaisonnements', 'ソースと調味料', 5),
('Boisson', '飲み物', 'Boissons chaudes et froides', '温かい飲み物と冷たい飲み物', 6),
('Apéritif', 'アペリティフ', 'Amuse-bouches et snacks', '軽食とスナック', 7),
('Petit-déjeuner', '朝食', 'Plats du petit-déjeuner', '朝食の料理', 8);

-- ============================================================================
-- DONNÉES : Tags par défaut (système)
-- ============================================================================
INSERT INTO tag (name_fr, name_jp, description_fr, description_jp, color, is_system) VALUES
-- Type de protéine
('Viande', '肉', 'Contient de la viande', '肉を含む', '#EF4444', 1),
('Poisson', '魚', 'Contient du poisson', '魚を含む', '#3B82F6', 1),
('Fruits de mer', '海鮮', 'Contient des fruits de mer', '海産物を含む', '#06B6D4', 1),
('Volaille', '鶏肉', 'Contient de la volaille', '鶏肉を含む', '#F59E0B', 1),

-- Régimes alimentaires
('Végétarien', 'ベジタリアン', 'Sans viande ni poisson', '肉や魚を含まない', '#10B981', 1),
('Végétalien', 'ビーガン', 'Sans produits animaux', '動物性食品を含まない', '#059669', 1),
('Sans gluten', 'グルテンフリー', 'Sans gluten', 'グルテンを含まない', '#8B5CF6', 1),
('Sans lactose', '乳糖不使用', 'Sans produits laitiers', '乳製品を含まない', '#A78BFA', 1),

-- Temps de préparation
('Rapide', '速い', 'Moins de 30 minutes', '30分未満', '#22C55E', 1),
('Moyen', '普通', '30 à 60 minutes', '30分から60分', '#FBBF24', 1),
('Long', '長い', 'Plus d''1 heure', '1時間以上', '#F97316', 1),

-- Difficulté
('Facile', '簡単', 'Facile à réaliser', '簡単に作れる', '#34D399', 1),
('Intermédiaire', '中級', 'Niveau intermédiaire', '中級レベル', '#FBBF24', 1),
('Difficile', '難しい', 'Pour cuisiniers expérimentés', '経験豊富な料理人向け', '#F87171', 1),

-- Cuisine du monde
('Française', 'フランス料理', 'Cuisine française', 'フランス料理', '#0EA5E9', 1),
('Japonaise', '日本料理', 'Cuisine japonaise', '日本料理', '#EC4899', 1),
('Italienne', 'イタリア料理', 'Cuisine italienne', 'イタリア料理', '#84CC16', 1),
('Asiatique', 'アジア料理', 'Cuisine asiatique', 'アジア料理', '#F59E0B', 1),

-- Occasions
('Fête', 'パーティー', 'Pour les occasions festives', 'お祝いの機会に', '#A855F7', 1),
('Quotidien', '日常', 'Pour tous les jours', '日常的に', '#6B7280', 1),
('Saison', '季節', 'Recette de saison', '季節の料理', '#14B8A6', 1);

-- ============================================================================
-- INDEX : Pour améliorer les performances de recherche
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_recipe_category_recipe ON recipe_category(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_category_category ON recipe_category(category_id);
CREATE INDEX IF NOT EXISTS idx_recipe_tag_recipe ON recipe_tag(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_tag_tag ON recipe_tag(tag_id);
CREATE INDEX IF NOT EXISTS idx_tag_name_fr ON tag(name_fr);
CREATE INDEX IF NOT EXISTS idx_category_name_fr ON category(name_fr);
