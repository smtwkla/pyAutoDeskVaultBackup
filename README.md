pyAutoDeskVaultBackup

Used to: 
1. Backup Autodesk Vault data to S3 bucket
2. Do weekly maintenance of SQL Express database.

Tested on Autodesk Vault Basic 2024

# 1. Backup
Uses ADMSConsole command line to generate backup, uses tar and uploads to S3. See [Vault Documentation](https://help.autodesk.com/view/VAULT/2024/ENU/?guid=GUID-56F358D7-C47B-4B6A-95CB-F402D6F2C7F9).
 

# 2. Maintenance
Executes scripts as per [Server Maintenance Part 6: Create SQL Maintenance Plan](https://help.autodesk.com/view/VAULT/2024/ENU/?guid=GUID-B294A257-8EC3-43E8-BC46-D701594C78FD). Rename example_email_secrets.py -> email_secrets.py, example_secrets.py -> secrets.py and fill in actual data.
Use Task Scheduler to execute weekly. Please execute the database modifications first, as described on the above page. 
