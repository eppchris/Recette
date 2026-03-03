-- Migration 010: Ajout de la colonne file_path pour stocker le chemin du PDF original
ALTER TABLE receipt_upload_history ADD COLUMN file_path TEXT;
