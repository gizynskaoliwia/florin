ATTACH DATABASE 'C:\Users\ogizy\AppData\Local\Florin\backups\florin_backup_20260602_102136.db' AS backup_db;

DELETE FROM savings_actual_grid;
INSERT INTO savings_actual_grid SELECT * FROM backup_db.savings_actual_grid;

DELETE FROM savings_actual_available;
INSERT INTO savings_actual_available SELECT * FROM backup_db.savings_actual_available;

DELETE FROM savings_spent;
INSERT INTO savings_spent SELECT * FROM backup_db.savings_spent;

DETACH DATABASE backup_db;
