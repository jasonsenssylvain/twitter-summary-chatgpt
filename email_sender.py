from email.message import EmailMessage
import smtplib
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)
format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

class EmailSender:
  def __init__(self, account, password, receiver) -> None:
    self._account = account
    self._password = password
    self._receiver = receiver
    
  def send_email(self, subject, body):
    
    msg = MIMEText(body, 'html')
    msg["From"] = self._account
    msg["To"] = self._receiver
    msg["Subject"] = subject
    
    with smtplib.SMTP('smtp-mail.outlook.com', 587) as smtp:
      try:
        smtp.starttls()
        smtp.login(self._account, self._password)
        smtp.send_message(msg)
        logger.info("Email sent to {}".format(self._receiver))
      except Exception as ex:
        logger.exception("Error : {}".format(ex))
      
  