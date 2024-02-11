import os.path
import sys
import subprocess
import datetime
import boto3
import botocore.exceptions
import traceback

from secrets import *


def upload_to_s3bucket(loc_file, s3_b, rem_file):
    print(f"Uploading {loc_file} to s3://{s3_b}/{rem_file}...")

    s3 = boto3.client('s3', aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key)

    s3.upload_file(loc_file, s3_b, rem_file)


adms = os.path.join(ADMSConsolePath, 'Connectivity.ADMSConsole.exe')
log_path = os.path.join(wd, "VaultBackupLog.txt")
bk_cmd = [adms, fr'-Obackup', fr'-B{wd}\Backups', '-VUAdministrator', f'-VP{VPassword}', '-S',
          f'-L{log_path}']


if len(sys.argv) > 1 and sys.argv[1] == "-d":
    bk_cmd = os.path.join(wd, "dummybackup.bat")

try:
    print("ADMSConsole Backup...")
    c = subprocess.run(bk_cmd, cwd=ADMSConsolePath)
    print("Tar...")
    c = subprocess.run([r'tar', r'zcf', 'backups.tar.gz', 'Backups'], cwd=wd)
except Exception as e:
    traceback.print_exc()
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
subprocess.run([r'cmd', r'/c', 'rmdir', r'/S', r'/Q', os.path.join(wd, r'Backups')])
subprocess.run([r'cmd', r'/c', 'del', r'/Q', tar_loc_fullname])
subprocess.run([r'cmd', r'/c', 'del', r'/Q', log_loc_fullname])
print("Temp Files cleared.")
