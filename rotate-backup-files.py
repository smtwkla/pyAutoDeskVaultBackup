import os.path
import sys
import subprocess
import datetime
import boto3
import botocore.exceptions
import logging

from secrets import *
from settings import *

VAULT_ROTATE_LOG_FILENAME = 'vault-rotate.log.txt'


class BackupFile:
    def __init__(self, fn='', ft=None):
        self.file_name = fn
        self.file_time = ft
        self.age = None
        self.calc_age()

    def delete(self, s3_client):
        logging.debug("deleting file: " + self.file_name)
        try:
            s3_client.delete_object(Bucket=s3_bucket, Key=self.file_name)
        except botocore.exceptions.ClientError as e:
            logging.error("Error deleting file from s3: " + e.response['Error']['Message'])

    def calc_age(self):
        if self.file_time is not None:
            self.age = datetime.datetime.now() - self.file_time
        else:
            return 0

    def __repr__(self):
        return f'{self.file_name} - {self.file_time} - {self.age.days} days ago'


def setup_logging():
    try:
        os.remove(VAULT_ROTATE_LOG_FILENAME)
    except OSError:
        pass
    logging.basicConfig(format='%(asctime)s %(message)s', filename=VAULT_ROTATE_LOG_FILENAME, encoding='utf-8',
                        level=logging.INFO)
    console = logging.StreamHandler()
    logging.getLogger().addHandler(console)


setup_logging()
logging.info('Starting Vault Log Rotation...')
s3 = boto3.client('s3', aws_access_key_id=s3_access_key_id, aws_secret_access_key=s3_secret_access_key)
s3_contents = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix)


backup_files = []

for obj in s3_contents['Contents']:
    file_name = obj['Key']
    if file_name.startswith(BACKUP_FILE_PREFIX) and file_name.endswith(BACKUP_FILE_SUFFIX):
        file_time_str = file_name.removeprefix(BACKUP_FILE_PREFIX).removesuffix(BACKUP_FILE_SUFFIX)
        file_time = datetime.datetime.strptime(file_time_str, BACKUP_FILE_TIME_FORMAT)
        backup_files.append(BackupFile(file_name, file_time))

for file in backup_files:
    if file.age.days > MAX_DAYS_DAILY_BACKUPS:
        logging.info(f'Deleting File {file} ...')
        file.delete(s3)
    else:
        logging.debug(f'File {file} retained.')

logging.info("Completed rotating backup files.")
logging.getLogger().handlers[0].flush()
s3.upload_file(VAULT_ROTATE_LOG_FILENAME, s3_bucket, VAULT_ROTATE_LOG_FILENAME)
