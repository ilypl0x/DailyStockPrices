import ssl
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class Emailer():
    def sendmail(self,data,to,subject,attachment=None):
        gmail_user = 'python.autoemail29@gmail.com'
        gmail_password = '@utoPython7'

        sent_from = gmail_user

        if type(to) != list:
            to = re.split(',|;',to)

        msg = MIMEMultipart('mixed')
        msg['From'] = sent_from
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject

        msg.attach(MIMEText(data,'html'))

        if attachment is not None:
            payload = MIMEBase('application','octet-stream')
            payload.set_payload(open(attachment,'rb').read())
            encoders.encode_base64(payload)
            payload.add_header('Content-Disposition','attachment; filename="%s"' %os.path.basename(attachment))       
            msg.attach(payload)         

        context = ssl.create_default_context()
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com',465,context=context)
            server.ehlo()
            server.login(gmail_user,gmail_password)
            server.sendmail(sent_from,to, msg.as_string())
            server.close()
        except Exception as e:
            print('ERROR Sending the Email: {}'.format(e))
