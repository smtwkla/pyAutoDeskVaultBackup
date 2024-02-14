import os.path
import sys
import subprocess
import datetime
import boto3
import botocore.exceptions
import logging

import email_secrets
import send_email_rep

from secrets import *
from settings import *


ADMS_LOG_FILENAME = 'ADMSConsoleBackupLog.txt'
VAULTBACKUP_LOG_FILENAME = 'vault-backup.log.txt'


def setup_logging():
    subprocess.run([r'cmd', r'/c', 'del', r'/Q', VAULTBACKUP_LOG_FILENAME])
    logging.basicConfig(format='%(asctime)s %(message)s', filename=VAULTBACKUP_LOG_FILENAME, encoding='utf-8',
                        level=logging.INFO)
    console = logging.StreamHandler()
    logging.getLogger().addHandler(console)


def upload_to_s3bucket(loc_file, s3_b, rem_file):
    logging.info(f"Uploading {loc_file} to s3://{s3_b}/{rem_file}...")
    s3 = boto3.client('s3', aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key)
    s3.upload_file(loc_file, s3_b, rem_file)


def send_report_and_exit(rc=0):
    logging.getLogger().handlers[0].flush()

    with open(VAULTBACKUP_LOG_FILENAME, 'r') as fl:
        log_content = fl.read()

    log_content = log_content.encode('ascii','ignore').decode('ascii')

    msg = f"""From: {email_secrets.SMTP_USER}
To: {', '.join(email_secrets.SMTP_SEND_TO)} 
Subject: Autodesk Vault Backup Report {datetime.datetime.now().strftime("%Y-%m-%d")}

{log_content}
    """
    send_email_rep.send_mail(msg)
    exit(rc)


def human_size(bytes, units=[' bytes','KB','MB','GB','TB', 'PB', 'EB']):
    """ Returns a human-readable string representation of bytes """
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes>>10, units[1:])


adms = os.path.join(ADMSConsolePath, 'Connectivity.ADMSConsole.exe')
log_path = os.path.join(wd, ADMS_LOG_FILENAME)
bk_cmd = [adms, fr'-Obackup', fr'-B{wd}\Backups', '-VUAdministrator', f'-VP{VPassword}', '-S', '-VAL'
          f'-L{log_path}']

if len(sys.argv) > 1 and sys.argv[1] == "-d":
    #used for debuging and dev purpose, without invoking the actual ADMSConsole
    bk_cmd = [os.path.join(wd, "dummybackup.bat")]
    ADMSConsolePath = os.path.join(wd)

setup_logging()

try:
    logging.info("Running ADMSConsole Backup...")
    c = subprocess.run(bk_cmd, cwd=ADMSConsolePath, capture_output=True)
    logging.info(f"ADMSConsole Backup Complete with exit code {c.returncode}.")
    logging.info(f"{c.stderr.decode('ascii')}")
    logging.info(f"Logfile Contents:")
    try:
        with open(log_path, "r") as f:
            logging.info(f.read())
    except FileNotFoundError:
        logging.critical('<Could not find log file.>')
    logging.info("Running tar...")
    c = subprocess.run([r'tar', r'zcf', 'backups.tar.gz', 'Backups'], cwd=wd)
except Exception as e:
    logging.exception(f"Error running {bk_cmd}.")
    send_report_and_exit(-1)

n = datetime.datetime.now().strftime("%Y_%m_%d_%H_")
tar_rem_name = f'vault_backup_{n}.tar.gz'
tar_loc_fullname = os.path.join(wd, 'backups.tar.gz')
log_rem_name = f'VaultBackupADMSLog.txt'

try:
    fs = human_size(os.path.getsize(tar_loc_fullname))
    logging.info(f'Backup tar file {tar_rem_name} is {fs}')
except Exception as e:
    pass

try:
    upload_to_s3bucket(tar_loc_fullname, s3_bucket, tar_rem_name)
    upload_to_s3bucket(log_path, s3_bucket, log_rem_name)
except (WindowsError, botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    logging.exception('Error occurred during S3 Upload.')
    send_report_and_exit(-1)

logging.info(f"Uploaded {log_rem_name} to S3.")
subprocess.run([r'cmd', r'/c', 'rmdir', r'/S', r'/Q', os.path.join(wd, r'Backups')])
subprocess.run([r'cmd', r'/c', 'del', r'/Q', tar_loc_fullname])
subprocess.run([r'cmd', r'/c', 'del', r'/Q', log_path])
logging.debug("Temp Files cleared.")
logging.info("Success.")
send_report_and_exit()
