-- Migration : nombre de convives par jour d'événement
-- NULL = même nombre que l'événement (event.attendees)
ALTER TABLE event_date ADD COLUMN attendees INTEGER DEFAULT NULL;
