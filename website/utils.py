from . import db, mail
from flask_mail import Message

def sendMail(dest, sbj, mssg):
    msg = Message(
        subject=sbj,
        recipients=[dest]
    )
    msg.body = mssg
    mail.send(msg)
