wd = "c:\\backup\\vault"
ADMSConsolePath = 'C:\\Program Files\\Autodesk\\Vault Server 2025\\ADMS Console' # Vault Server 2024: Change path
BACKUP_FILE_PREFIX = 'vault_backup_'
BACKUP_FILE_SUFFIX = '.tar.gz'
BACKUP_FILE_TIME_FORMAT = "%Y_%m_%d_%H_"

MAX_DAYS_DAILY_BACKUPS = 7       # Daily backups above this age are deleted, except if needed for monthly
# MONTHLY_BACKUP_DAY = 1      # When deleting old daily backups, backups of this day of month is not deleted ...
# MAX_MONTHLY_BACKUPS = 6     # ... except if it is this many months old
