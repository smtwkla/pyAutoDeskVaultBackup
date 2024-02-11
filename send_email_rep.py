import smtplib
import email_secrets as es
import email.message


def send_mail(text):
    mailserver = smtplib.SMTP(es.SMTP_SRV, es.SMTP_PORT)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.login(es.SMTP_USER, es.SMTP_PASSWORD)
    # Adding a newline before the body text fixes the missing message body
    mailserver.sendmail(es.SMTP_USER, es.SMTP_SEND_TO, text)
    mailserver.quit()
