from . import db, mail
from flask import current_app
from flask_mail import Message
from datetime import datetime
from . import executor


def sendConfirmMail(email, sbj, msg):

    app = current_app._get_current_object()

    executor.submit(
        sendConfirmMailAsync, email, app, sbj, msg
    )



# Send a confirmation email to the user
def sendConfirmMailAsync(email, app, sbj, msg):

    try:
        # Ensure Flask app context inside the thread
        with app.app_context():
            sendMail(email, sbj, msg)
            
    except Exception as e:
        print(f"Error sending email: {e}")

def sendMail(dest, sbj, mssg):
    msg = Message(
        subject=sbj,
        recipients=[dest]
    )
    msg.body = mssg
    mail.send(msg)


def addDetails(props):
    from .models import Details
    detail = Details(
        motive_id=props['motive_id'],
        detail=props['detail'] if 'detail' in props else None,  
        user_id=props['user_id'],
        created_at=datetime.now()
    )
    db.session.add(detail)
    db.session.commit()
    return detail.id

motives = {
    1: 'Login',
    2: 'SignUp',
    3: 'Logout',
    4: 'addAppointment',
    5: 'cancelAppointment',
    6: 'modifyAppointment',
    7: 'deleteAccount',
    8: 'confirmEmail'
}