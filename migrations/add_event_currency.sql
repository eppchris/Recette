-- Migration: Ajout de la devise pour les événements
-- Date: 2025-11-17
-- Description: Mémorise la devise dans laquelle le budget a été créé

-- Ajouter la colonne currency à la table event
-- Par défaut EUR pour les événements existants
ALTER TABLE event ADD COLUMN currency TEXT DEFAULT 'EUR';

-- Mettre à jour les événements existants avec une devise par défaut
UPDATE event SET currency = 'EUR' WHERE currency IS NULL;
