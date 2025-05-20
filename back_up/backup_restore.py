from cryptography.fernet import Fernet

ENCRYPTED_BACKUP_PATH = "database_backup.db.enc"
RESTORED_DB_PATH = "database_restored.db"
KEY_PATH = "../secret.key"

# Încarcă cheia Fernet
with open(KEY_PATH, "rb") as f:
    key = f.read()
fernet = Fernet(key)

# Decriptează backup-ul
with open(ENCRYPTED_BACKUP_PATH, "rb") as f:
    encrypted_data = f.read()
decrypted_data = fernet.decrypt(encrypted_data)
with open(RESTORED_DB_PATH, "wb") as f:
    f.write(decrypted_data)

print("Backup restaurat cu succes!")