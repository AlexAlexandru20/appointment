from flask import render_template, Blueprint, request, redirect, url_for, jsonify, current_app, flash
from flask_login import login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer
from . import db, executor
from .utils import sendMail
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth = Blueprint('auth', __name__)

serializer = URLSafeTimedSerializer('123456789')


# Send a confirmation email to the user
def sendConfirmMailAsync(email, app):
    """Runs in a separate thread to send an email confirmation."""
    print(f"Thread started for {email}")

    try:
        # Ensure Flask app context inside the thread
        with app.app_context():
            print("Inside Flask context")

            token = serializer.dumps(email, salt='email-confirm')
            confirm_url = f"http://{app.config['SERVER_NAME']}/confirm-email/{token}"

            print(f'Generated confirmation URL: {confirm_url}')

            sbj = 'Confirm Your Email'
            msg = f'Click the link to confirm your email: {confirm_url}'
            sendMail(email, sbj, msg)
    except Exception as e:
        print(f"Error sending email: {e}")


def sendConfirmMail(email):
    """Submit the email sending task asynchronously."""
    print(f"Submitting email task for {email}")  # Debugging

    app = current_app._get_current_object()

    future = executor.submit(sendConfirmMailAsync, email, app)
    
    # Check if the function was submitted
    print(f"Task submitted: {future}")  



# Confirm the email token
def confirmEmailToken(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except:
        return 'The confirmation link is invalid or has expired.'
    return email


# Login route
@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        from .models import User
        email = request.form.get('email')

        existed_user = User.query.filter_by(email=email).first()

        if existed_user:
            password = check_password_hash(existed_user.password, request.form.get('password'))

            if password:
                if not existed_user.confirmed:
                    return redirect(url_for('auth.confirmEmailWindow', email=email))
                login_user(existed_user)

                if existed_user.name == None or existed_user.phone == None:
                    return redirect(url_for('views.addDetails'))
                return redirect(url_for('views.home'))
            else:
                return 'Password is incorrect'
        else:
            return redirect(url_for('auth.register'))

    return render_template('index.html')


# Register route
@auth.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        from .models import User
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password2')

        existed_user = User.query.filter_by(email=email).first()

        if not existed_user:
            if password == password_confirm:
                newUser = User(email=email, password=generate_password_hash(password, method='pbkdf2:sha256'), created_at=datetime.now(), confirmed=False)
                db.session.add(newUser)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print('Error: ', e)

                sendConfirmMail(email)
                return redirect(url_for('auth.confirmEmailWindow', email=email))
            else:
                return 'Passwords do not match'
    return render_template('register.html')


#Email confirmation window route
@auth.route('/confirmEmailWindow/<email>')
def confirmEmailWindow(email):
    return render_template('confirm_email.html', email=email)


#Email confirmation algorithm route
@auth.route('/confirm-email/<token>')
def confirmEmail(token):
    from .models import User
    email = confirmEmailToken(token)

    if not email:
        return 'The confirmation link is invalid or has expired.'
    
    user = User.query.filter_by(email=email).first()

    if user and not user.confirmed:

        user.confirmed = True
        db.session.commit()

        return redirect(url_for('auth.login'))
    
    elif user and user.confirmed:
        flash('Email already confirmed', 'info')
        return redirect(url_for('auth.login'))
    

#Send email again route
@auth.route('/send-email-again/<email>')
def sendEmailAgain(email):
    sendConfirmMail(email)
    return redirect(url_for('auth.confirmEmailWindow', email=email))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))