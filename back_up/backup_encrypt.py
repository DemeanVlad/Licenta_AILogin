import shutil
from cryptography.fernet import Fernet
import os

DB_PATH = "../database.db"  # sau calea corectă către baza ta de date
BACKUP_PATH = "database_backup.db"
ENCRYPTED_BACKUP_PATH = "database_backup.db.enc"
KEY_PATH = "../secret.key" 

# 1. Creează backup simplu (copie)
shutil.copyfile(DB_PATH, BACKUP_PATH)

# 2. Încarcă cheia Fernet
with open(KEY_PATH, "rb") as f:
    key = f.read()
fernet = Fernet(key)

# 3. Criptează backup-ul
with open(BACKUP_PATH, "rb") as f:
    data = f.read()
encrypted_data = fernet.encrypt(data)
with open(ENCRYPTED_BACKUP_PATH, "wb") as f:
    f.write(encrypted_data)

# 4. (Opțional) Șterge backup-ul necriptat
os.remove(BACKUP_PATH)

print("Backup și criptare realizate cu succes!")