#!/usr/bin/env python

import smtplib
from email.Header import Header
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import farmer_log
import sys

mail_from = "zongruix.zhang@intel.com"
mail_to = "zongruix.zhang@intel.com"


def sendMail(sender, receiver, subject):
    smtpserver = "smtp.intel.com"
    msg = MIMEMultipart("related")

    msg["Subject"] = Header(subject, "utf-8")

    html = """
    <html>
        <head>This is a test</head>
        <body>
            <br><img width=75 height=134 alt="" src="cid:meinv_image"/></br>
        </body>
    </html>
    """
    htm = MIMEText(html, 'html', 'utf-8')
    msg.attach(htm)

    fp = open('12.PNG', 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    msgImage.add_header("Content-ID", "<meinv_image>")
    msg.attach(msgImage)

    att = MIMEText(open("log.tar.gz").read(), "base64", "utf-8")
    att["Content-Type"] = "application/octet-stream"
    att["Content-Disposition"] = 'attachment;filename="log.tar.gz"'
    msg.attach(att)
    smtp = smtplib.SMTP()
    try:
        smtp.connect(smtpserver)
        smtp.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        print e        
    finally:
        smtp.quit()

def send_security_code(sender, receiver, securityCode):
    result = True
    smtpserver = "smtp.intel.com"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header("Security Code[%s]" % securityCode, "utf-8")
    html = """
    <html>
        <head>Security Code:</head>
        <body>
            <p><label><h4>%s</h4></label></p>
        </body>
    </html>
    """ % securityCode
    htm = MIMEText(html, 'html', 'utf-8')
    msg.attach(htm)
    smtp = smtplib.SMTP()
    try:
        smtp.connect(smtpserver)
        smtp.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        result = False
        farmer_log.error("%s" % e)
    finally:
        smtp.quit()
    return result


if __name__ == "__main__":
    mail_from = sys.argv[1]
    mail_to = sys.argv[2]
    secCode = sys.argv[3]
    send_security_code(mail_from, mail_to, secCode)
