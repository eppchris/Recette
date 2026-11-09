-- Migration : nom japonais du type WORKSHOP (espace en tête et faute de frappe)
UPDATE event_type SET name_jp = 'ワークショップ' WHERE name_fr = 'WORKSHOP';
