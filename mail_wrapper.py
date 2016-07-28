#!/usr/bin/env python

import smtplib
from email import Header
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

mail_from = "localhost"
mail_to = "zongruix.zhang@intel.com"

msg = MIMEMultipart("")

def sendMail(sender, receiver, subject):
    smtpserver = "smtp.intel.com"
    username = "zongruix.zhang@intel.com"
    password = "Intel,123456"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")

    html = """
    <html>
        <head>This is a test</head>
        <body>
            <br><img src="cid:meinv_image"/></br>
        </body>
    </html>
    """
    htm = MIMEText(html, 'html', 'utf-8')
    msg.attach(htm)

    fp = open('meinv.jpg', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    msgImage.add_header("Content-ID", "<meinv_image>")
    msg.attach(msgImage)

    att = MIMEText(open("log.tar.gz").read(), "base64", "utf-8")
    att["Content-Type"] = "application/octet-stream"
    att["Content-Disposition"] = 'attachment;filename="log.tar.gz"'
    msg.attach(att)
    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()