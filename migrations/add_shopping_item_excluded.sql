-- Migration : ingrédient retiré de la liste de courses (décoché dans le parcours guidé)
-- 0 = à acheter, 1 = retiré (barré, absent de la liste envoyée/imprimée)
ALTER TABLE shopping_list_item ADD COLUMN excluded INTEGER NOT NULL DEFAULT 0;
