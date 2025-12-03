# tests/test_db_conversions_new.py
"""
Tests unitaires pour le module db_conversions
Teste les conversions d'unités (masse, volume, etc.)
"""

import pytest
from app.models.db_conversions import convert_unit, get_convertible_units


# ============================================================================
# TESTS DE CONVERSION D'UNITÉS
# ============================================================================

class TestConvertUnit:
    """Tests pour la fonction convert_unit()"""

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_grammes_to_kilogrammes(self, temp_db):
        """Teste la conversion de grammes en kilogrammes"""
        result = convert_unit(1000, "g", "kg")
        assert result == 1.0, "1000g devrait donner 1kg"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_kilogrammes_to_grammes(self, temp_db):
        """Teste la conversion de kilogrammes en grammes"""
        result = convert_unit(1.5, "kg", "g")
        assert result == 1500.0, "1.5kg devrait donner 1500g"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_litres_to_millilitres(self, temp_db):
        """Teste la conversion de litres en millilitres"""
        result = convert_unit(1, "L", "mL")
        assert result == 1000.0, "1L devrait donner 1000mL"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_millilitres_to_litres(self, temp_db):
        """Teste la conversion de millilitres en litres"""
        result = convert_unit(500, "mL", "L")
        assert result == 0.5, "500mL devrait donner 0.5L"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_tasse_to_millilitres(self, temp_db):
        """Teste la conversion de tasse en millilitres"""
        result = convert_unit(2, "tasse", "mL")
        assert result == 500.0, "2 tasses devraient donner 500mL"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_cuillere_a_soupe_to_ml(self, temp_db):
        """Teste la conversion de cuillères à soupe en mL"""
        result = convert_unit(3, "c. à soupe", "mL")
        assert result == 45.0, "3 c. à soupe devraient donner 45mL"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_cuillere_a_cafe_to_ml(self, temp_db):
        """Teste la conversion de cuillères à café en mL"""
        result = convert_unit(2, "c. à café", "mL")
        assert result == 10.0, "2 c. à café devraient donner 10mL"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_same_unit_returns_same_value(self, temp_db):
        """Teste que convertir dans la même unité retourne la même valeur"""
        result = convert_unit(100, "g", "g")
        assert result == 100.0, "100g en g devrait rester 100g"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_zero_quantity(self, temp_db):
        """Teste la conversion avec une quantité nulle"""
        result = convert_unit(0, "g", "kg")
        assert result == 0.0, "0g devrait donner 0kg"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_decimal_quantity(self, temp_db):
        """Teste la conversion avec des décimales"""
        result = convert_unit(250.5, "g", "kg")
        assert result == pytest.approx(0.2505, rel=1e-6), "250.5g devrait donner 0.2505kg"

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_invalid_units_raises_error(self, temp_db):
        """Teste qu'une conversion impossible lève une erreur"""
        # Impossible de convertir grammes en litres (masse vs volume)
        with pytest.raises(Exception):
            convert_unit(100, "g", "L")

    @pytest.mark.unit
    @pytest.mark.database
    def test_convert_unknown_unit_raises_error(self, temp_db):
        """Teste qu'une unité inconnue lève une erreur"""
        with pytest.raises(Exception):
            convert_unit(100, "unitéinconnue", "g")


# ============================================================================
# TESTS PARAMÉTRÉS POUR LES CONVERSIONS
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
@pytest.mark.parametrize("quantity,from_unit,to_unit,expected", [
    # Conversions de masse
    (1000, "g", "kg", 1.0),
    (1, "kg", "g", 1000.0),
    (500, "g", "kg", 0.5),

    # Conversions de volume
    (1, "L", "mL", 1000.0),
    (500, "mL", "L", 0.5),
    (2, "tasse", "mL", 500.0),
    (3, "c. à soupe", "mL", 45.0),
    (4, "c. à café", "mL", 20.0),

    # Même unité
    (100, "g", "g", 100.0),
    (250, "mL", "mL", 250.0),

    # Quantité nulle
    (0, "g", "kg", 0.0),
    (0, "L", "mL", 0.0),
])
def test_convert_unit_parametrized(temp_db, quantity, from_unit, to_unit, expected):
    """
    Test paramétré pour plusieurs conversions
    Chaque tuple (quantity, from_unit, to_unit, expected) génère un test
    """
    result = convert_unit(quantity, from_unit, to_unit)
    assert result == pytest.approx(expected, rel=1e-6), \
        f"{quantity} {from_unit} devrait donner {expected} {to_unit}, obtenu {result}"


# ============================================================================
# TESTS POUR get_convertible_units()
# ============================================================================

class TestGetConvertibleUnits:
    """Tests pour la fonction get_convertible_units()"""

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_convertible_units_from_grammes(self, temp_db):
        """Teste les unités convertibles depuis 'g'"""
        result = get_convertible_units("g")
        assert isinstance(result, list), "Devrait retourner une liste"
        assert "kg" in result, "'kg' devrait être convertible depuis 'g'"

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_convertible_units_from_litres(self, temp_db):
        """Teste les unités convertibles depuis 'L'"""
        result = get_convertible_units("L")
        assert isinstance(result, list), "Devrait retourner une liste"
        assert "mL" in result, "'mL' devrait être convertible depuis 'L'"

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_convertible_units_from_tasse(self, temp_db):
        """Teste les unités convertibles depuis 'tasse'"""
        result = get_convertible_units("tasse")
        assert isinstance(result, list), "Devrait retourner une liste"
        assert "mL" in result, "'mL' devrait être convertible depuis 'tasse'"

    @pytest.mark.unit
    @pytest.mark.database
    def test_get_convertible_units_unknown_unit(self, temp_db):
        """Teste avec une unité inconnue"""
        result = get_convertible_units("unitéinconnue")
        # Devrait retourner une liste vide ou lever une erreur selon l'implémentation
        assert isinstance(result, list), "Devrait retourner une liste (possiblement vide)"


# ============================================================================
# TESTS D'INTÉGRATION (conversions en chaîne)
# ============================================================================

@pytest.mark.integration
@pytest.mark.database
class TestConversionChaining:
    """Tests pour les conversions en chaîne (si implémenté)"""

    def test_chain_conversion_tasse_to_litre(self, temp_db):
        """
        Teste une conversion en chaîne : tasse → mL → L
        (Si la fonction supporte le chaînage automatique)
        """
        # D'abord tasse → mL
        ml = convert_unit(4, "tasse", "mL")  # 4 tasses = 1000mL

        # Puis mL → L
        litres = convert_unit(ml, "mL", "L")  # 1000mL = 1L

        assert litres == 1.0, "4 tasses devraient donner 1L via mL"

    def test_chain_conversion_cuillere_to_litre(self, temp_db):
        """Teste tasse → mL → L en une fois (si supporté)"""
        # 200 c. à café = 200 * 5mL = 1000mL = 1L
        ml = convert_unit(200, "c. à café", "mL")
        litres = convert_unit(ml, "mL", "L")

        assert litres == 1.0, "200 c. à café = 1L"


# ============================================================================
# TESTS DE PERFORMANCE (optionnels)
# ============================================================================

@pytest.mark.slow
@pytest.mark.database
def test_conversion_performance(temp_db):
    """
    Teste que les conversions sont rapides
    (utile si tu as beaucoup de conversions dans une liste de courses)
    """
    import time

    start = time.time()

    # Faire 1000 conversions
    for _ in range(1000):
        convert_unit(100, "g", "kg")

    elapsed = time.time() - start

    # Devrait prendre moins de 1 seconde pour 1000 conversions
    assert elapsed < 1.0, f"1000 conversions ont pris {elapsed:.2f}s, trop lent !"
