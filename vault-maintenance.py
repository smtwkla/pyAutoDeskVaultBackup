import os.path
import sys
import subprocess
import datetime
import logging

import email_secrets
import send_email_rep




# Maintenance plan for SQL Server Express based Vault
# Invoke as : VaultBackup.bat Name of Vault
# include [], only one vault at a time

VAULT_MAINT_LOG_FILENAME = 'vault-maintenance.log.txt'


def setup_logging():
    subprocess.run([r'cmd', r'/c', 'del', r'/Q', VAULT_MAINT_LOG_FILENAME, '2>nul'])
    logging.basicConfig(format='%(asctime)s %(message)s', filename=VAULT_MAINT_LOG_FILENAME, encoding='utf-8',
                        level=logging.INFO)
    console = logging.StreamHandler()
    logging.getLogger().addHandler(console)


def exec_sql_cmd(sql_cli, cmd):
    ex_cmd = [*sql_cli, cmd]
    logging.info(f"Executing SQL {' '.join(ex_cmd)}")
    try:
        rc = subprocess.run(ex_cmd, capture_output=True)
    except Exception as e:
        logging.error(f"Error running command.")
    else:
        logging.info(f'Command Complete with exit code {rc.returncode}. Command Output: )')
        logging.info(f'{rc.stdout.decode("ascii")}\n{rc.stderr.decode("ascii")}')


def send_report_and_exit(rc=0):
    logging.getLogger().handlers[0].flush()

    with open(VAULT_MAINT_LOG_FILENAME, 'r') as fl:
        log_content = fl.read()

    log_content = log_content.encode('ascii','ignore').decode('ascii')

    msg = f"""From: {email_secrets.SMTP_USER}
To: {', '.join(email_secrets.SMTP_SEND_TO)} 
Subject: Autodesk Vault Maintenance Report {datetime.datetime.now().strftime("%Y-%m-%d")}

{log_content}
    """
    send_email_rep.send_mail(msg)
    exit(rc)


setup_logging()

if len(sys.argv) > 1:
    vn = " ".join(sys.argv[1:])
    VaultName=f'[{vn}]'
    VaultLog=f'[{vn}_log]'
    logging.info(f"Vault Name: {VaultName}, Vault Log Name: {VaultLog}")
else:
    logging.error("No Vault name specified.")
    exit(-1)

sql_cmd =['sqlcmd', '-E', '-S', r".\AutodeskVault", '-Q']

# Setting {VaultName} database compatibility to 110
compat_q = f"ALTER DATABASE {VaultName} SET COMPATIBILITY_LEVEL = 110"

# Setting {VaultName} database recovery model to simple...
rec_q = f"ALTER DATABASE {VaultName} SET RECOVERY SIMPLE"

# Setting {VaultName} database Autogrowth value...
autogrow_q = f"ALTER DATABASE {VaultName}  MODIFY FILE (NAME={VaultName}, FILEGROWTH=100MB)"

# Setting {VaultName} database Log filesize...
dblog_q = f"ALTER DATABASE {VaultName} MODIFY FILE ( NAME = {VaultLog}, SIZE = 512000KB )"

# Setting {VaultName} database Autoclose to false...
auto_close_q = f"ALTER DATABASE {VaultName} SET AUTO_CLOSE OFF WITH NO_WAIT"

# Reindexing {VaultName} database...
reindex_q = f"USE {VaultName} " \
            "DECLARE tableCursor CURSOR FOR "\
            "SELECT NAME FROM sysobjects WHERE xtype in('U') "\
            "DECLARE @tableName nvarchar(128) OPEN tableCursor FETCH NEXT FROM tableCursor INTO @tableName "\
            "WHILE @@FETCH_STATUS = 0 "\
            "BEGIN DBCC DBREINDEX(@tableName, '') FETCH NEXT FROM tableCursor INTO @tableName END " \
            "CLOSE tableCursor DEALLOCATE tableCursor"

# Updating Statistics on {VaultName} database...
update_stat_q = f"USE {VaultName} Exec sp_MSForEachTable 'Update Statistics ? WITH FULLSCAN'"

q_list = [compat_q, rec_q, autogrow_q, dblog_q, auto_close_q, reindex_q, update_stat_q]

for q in q_list:
    exec_sql_cmd(sql_cmd, q)

send_report_and_exit()
