-- Migration : Liaison entre ingrédients et recettes (sous-recettes)
-- Permet d'associer un ingrédient d'une recette à une autre recette
-- (ex: "250g pâte feuilletée" -> recette "Pâte feuilletée")

ALTER TABLE recipe_ingredient
ADD COLUMN linked_recipe_id INTEGER REFERENCES recipe(id) ON DELETE SET NULL;
