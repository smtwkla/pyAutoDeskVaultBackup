import os.path
import sys
import subprocess
import datetime
import boto3
import botocore.exceptions

from secrets import *


def execute_vault_backup(cmd, workdir):
    c = subprocess.run([cmd], cwd=workdir)
    c = subprocess.run([r'tar', r'zcf', 'backups.tar.gz', 'Backups'], cwd=wd)


def upload_to_s3bucket(loc_file, s3_b, rem_file):
    print(f"Uploading {loc_file} to s3://{s3_b}/{rem_file}...")

    s3 = boto3.client('s3', aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key)

    s3.upload_file(loc_file, s3_b, rem_file)


bk_cmd = r'"C:\Program Files\Autodesk\Vault Server 2024\ADMS Console\Connectivity.ADMSConsole.exe" ' \
         fr'-Obackup -B{wd}\Backups -VUAdministrator  -VPCAD70_Inventor+ -S -L{wd}\VaultBackupLog.txt'
print(f"Executing {bk_cmd}...")
if len(sys.argv) > 1 and sys.argv[1] == "-d":
    bk_cmd = os.path.join(wd, "dummybackup.bat")

try:
    execute_vault_backup(bk_cmd, wd)
except Exception as e:
    print(e)
    exit(-1)

if r != 0:
    print(f"Error executing vault backup command. {r}")
    exit(-1)

n = datetime.datetime.now().strftime("%Y_%m_%d_%H_")
tar_rem_name = f'vault_backup_{n}.tar.gz'
tar_loc_fullname = os.path.join(wd, 'backups.tar.gz')
log_rem_name = f'VaultBackupLog.txt'
log_loc_fullname = os.path.join(wd, 'VaultBackupLog.txt')


try:
    upload_to_s3bucket(tar_loc_fullname, s3_bucket, tar_rem_name)
    upload_to_s3bucket(log_loc_fullname, s3_bucket, log_rem_name)
except (WindowsError, botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    print('Error occurred.\n', e)
    exit(-1)

print("Uploaded to S3.")
subprocess.run([r'cmd', r'/c', 'del', r'/Q', os.path.join(wd, r'backups.tar.gz')])
subprocess.run([r'cmd', r'/c', 'del', r'/Q', os.path.join(wd, r'VaultBackupLog.txt')])
