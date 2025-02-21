from flask import (
    render_template,
    Blueprint,
    request,
    redirect,
    url_for,
    jsonify,
    current_app,
    flash,
)
from flask_login import login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer
from . import db
from .utils import addDetails, motives, sendConfirmMail
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

auth = Blueprint("auth", __name__)

serializer = URLSafeTimedSerializer("123456789")

#creation of confirmation URL
def getMailInfo(email):
    token = serializer.dumps(email, salt="email-confirm")
    confirm_url = (
        f"https://{current_app.config['SERVER_NAME']}/confirm-email/{token}"
    )

    sbj = "📧 Confirmare adresă de email - Verifică și răsfață-te!"
    msg = f"""
    Salut,

    Suntem pe cale să îți oferim o experiență de neuitat la Boti BarberShop, dar mai întâi, trebuie să confirmăm că adresa ta de email este corectă.

    Dă click pe butonul de mai jos pentru a confirma:
    {confirm_url}

    După ce ai confirmat, vei putea să te bucuri de toate beneficiile unui cont la noi: 
    - Programări rapide
    - Oferte speciale
    - Tot ce îți trebuie pentru o sesiune de relaxare perfectă 💆‍♀️✨

    Dacă nu ai făcut tu această cerere, ignoră acest mesaj. În caz contrar, te așteptăm cu brațele deschise!

    Cu drag,  
    Boti BarberShop 🌸
    """

    return sbj, msg



# Confirm the email token
def confirmEmailToken(token):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
    except:
        return "The confirmation link is invalid or has expired."
    return email


# Get a secret code for the user
def getSecretCode(user_id):
    from .models import SecretCodes

    secret_code = SecretCodes.query.filter_by(user_id=user_id, used=False).first()

    code = random.randint(100000, 999999)

    if secret_code:
        secret_code.code = code
        secret_code.created_at = datetime.now()
        secret_code.used = False

    else:
        secret_code = SecretCodes(code=code, user_id=user_id)
        db.session.add(secret_code)

    try:
        db.session.commit()
        print(code)
        return secret_code.code, None
    except Exception as e:
        db.session.rollback()
        print("Error: ", e)
        return None, e


#Generate mail for secret code
def getMailCode(name, code):
    sbj = "🔐 Resetare parolă - Codul tău personal"
    msg = f"""
        Salut {name} 🌸,

        Am primit o cerere de resetare a parolei pentru contul tău la Boti BarberShop. Dacă ai solicitat acest lucru, folosește codul de mai jos pentru a-ți schimba parola:

        Codul tău de resetare este: {code}

        Acest cod va expira în 10 minute, așa că nu mai pierde timp și schimbă-ți parola cât mai curând!

        Dacă nu ai făcut tu această cerere, te rugăm să ignori acest mesaj și să ne contactezi pentru mai multe informații.

        Cu drag,
        Boti BarberShop 🌸
        """
    return sbj, msg


def getMailReset(name):
    sbj = "🔔 Parola contului tău a fost schimbată"

    msg = f"""
    Salut {name} 🌸,

    Tocmai îți confirmăm că parola contului tău la Boti BarberShop a fost schimbată cu succes. 🔐

    Dacă ai făcut tu această modificare, nu trebuie să faci nimic altceva - contul tău este în siguranță! ✅

    Dacă nu ai solicitat această schimbare, te rugăm să schimbi parola contului imediat și să ne contactezi pentru a securiza contul tău.

    Cu drag,
    Boti BarberShop 🌸
    """

    return sbj, msg

# Login route
@auth.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        from .models import User

        email = request.form.get("email")

        existed_user = User.query.filter_by(email=email).first()

        if existed_user:
            password = check_password_hash(
                existed_user.password, request.form.get("password")
            )

            if password:
                if not existed_user.confirmed:
                    return redirect(url_for("auth.confirmEmailWindow", email=email))
                login_user(existed_user)

                details = {
                    "motive_id": next(
                        (key for key, value in motives.items() if value == "Login"),
                        None,
                    ),
                    "user_id": existed_user.id,
                }

                try:
                    addDetails(details)
                    print("Details added")
                except Exception as e:
                    print("Error: ", e)

                if existed_user.name == None or existed_user.phone == None:
                    return redirect(url_for("views.addDetails"))
                return redirect(url_for("views.home"))
            else:
                return "Password is incorrect"
        else:
            return redirect(url_for("auth.register", email=email))

    return render_template("index.html")


# Register route
@auth.route("/register/<email>", methods=["GET", "POST"])
def register(email):
    if request.method == "POST":
        from .models import User

        email = request.form.get("email")
        password = request.form.get("password")
        password_confirm = request.form.get("password2")

        existed_user = User.query.filter_by(email=email).first()

        if not existed_user:
            if password == password_confirm:
                newUser = User(
                    email=email,
                    password=generate_password_hash(password, method="pbkdf2:sha256"),
                    created_at=datetime.now(),
                    confirmed=False,
                )
                db.session.add(newUser)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print("Error: ", e)

                details = {
                    "motive_id": next(
                        (key for key, value in motives.items() if value == "SignUp"),
                        None,
                    ),
                    "user_id": newUser.id,
                }

                try:
                    addDetails(details)
                    print("Details added")
                except Exception as e:
                    print("Error: ", e)
                    
                sbj, msg = getMailInfo(email)
                sendConfirmMail(email, sbj, msg)
                return redirect(url_for("auth.confirmEmailWindow", email=email))
            else:
                return "Passwords do not match"
        else:
            return redirect(url_for('auth.login'))
    
    return render_template("register.html", email = email if email != 'newUser' else None)


# Email change route
@auth.route("/change-email", methods=["GET", "POST"])
@login_required
def changeEmail():
    try:
        if request.method == "POST":
            from .models import User

            email = request.get_json().get("email")
            existed_user = User.query.filter_by(email=email).first()

            if not existed_user:
                sbj, msg = getMailInfo(email)
                sendConfirmMail(email, sbj, msg)
                return jsonify({'success': True}), 200
            else:
                return 'Email existed'
    except Exception as e:
        print("Error: ", e)
        return jsonify({'error': e}), 400

# Email confirmation window route
@auth.route("/confirmEmailWindow/<email>")
def confirmEmailWindow(email):
    return render_template("confirm_email.html", email=email)


# Email confirmation algorithm route
@auth.route("/confirm-email/<token>")
def confirmEmail(token):
    from .models import User

    email = confirmEmailToken(token)

    if not email:
        return "The confirmation link is invalid or has expired."

    user = User.query.filter_by(email=email).first()
    if not user and current_user.email and current_user.email != email:
        current_user.email = email
        try:
            db.session.commit()
            flash("Email updated successfully", "success")

            return redirect(url_for('auth.logout'))
        except Exception as e:
            db.session.rollback()
            print("Error: ", e)
            flash("An error occurred while updating your email. Please try again.", "error")
            return redirect(url_for('users.change'))

    if user and not user.confirmed:

        user.confirmed = True
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error: ", e)

        details = {
            "motive_id": next(
                (key for key, value in motives.items() if value == "confirmEmail"), None
            ),
            "user_id": user.id,
        }

        try:
            addDetails(details)
            print("Details added")
        except Exception as e:
            print("Error: ", e)
        flash("Email confirmed", "success")
        return redirect(url_for("auth.login"))

    elif user and user.confirmed:
        flash("Email already confirmed", "info")
        return redirect(url_for("auth.login"))


# Send email again route
@auth.route("/send-email-again/<email>")
def sendEmailAgain(email):
    sbj, msg = getMailInfo(email)
    sendConfirmMail(email, sbj, msg)
    return redirect(url_for("auth.confirmEmailWindow", email=email))

# Logout User
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# Change password route
@auth.route("/resetPass", methods=["GET", "POST"])
def resetPass():
    if request.method == "POST":
        from .models import User

        email = request.form.get("email")

        existed_user = User.query.filter_by(email=email).first()

        if existed_user:
            secret_code, error = getSecretCode(existed_user.id)
            name = existed_user.name if existed_user.name else None

            if secret_code:

                sbj, msg = getMailCode(name, secret_code)
                
                sendConfirmMail(email, sbj, msg)
                return redirect(url_for("auth.confirmSecretCode", user_id=existed_user.id))
            else:
                print(error)
                return "Error generating secret code"
        else:
            return "User not found"  

    return render_template("reset_password.html")


# Confirm secret code route
@auth.route("/confirm-secret-code/<user_id>", methods=["GET", "POST"])
def confirmSecretCode(user_id):
    if request.method == "POST":
        from .models import SecretCodes
        user_id = request.get_json().get('user_id')
        secret_code = request.get_json().get("code")

        print(secret_code)

        now = datetime.now()

        existed_code = SecretCodes.query.filter_by(
            user_id = user_id,
            code = secret_code
        ).first()

        print(existed_code)

        if existed_code:
            sent_at = existed_code.created_at

            if now - sent_at > timedelta(minutes=10):
                return redirect(url_for('auth.expiredCode', user_id=user_id))
            else:
                db.session.delete(existed_code)
                db.session.commit()
                return redirect(url_for("auth.resetPasswordForm", user_id=user_id))
        else:
            return jsonify({'error': 'wrong_code'}), 200

    return render_template("confirm_secret_code.html", user_id=user_id)


@auth.route('/resendCode', methods=['PUT', 'GET'])
def resendCode():
    if request.method == "PUT":
        from .models import User
        #receive user's id
        user_id = request.get_json().get('user_id')
        # Query the User DB to check for 
        user = User.query.filter_by(id=user_id).first()

        name = user.name if user.name else None
        email = user.email
        secret_code, error = getSecretCode(user_id)
        if secret_code:
            sbj, msg = getMailCode(name, secret_code)

            sendConfirmMail(email, sbj, msg)
            return jsonify(), 200
        else:
            print(error)
            return jsonify({'error': error}), 400
        

    return render_template("confirm_secret_code.html", user_id=user_id)

# Reset password form route
@auth.route("/reset-password-form/<user_id>", methods=["GET", "PUT"])
def resetPasswordForm(user_id):
    if request.method == "PUT":
        from .models import User

        existed_user = User.query.filter_by(id=user_id).first()

        if existed_user:
            password = request.get_json().get("pass1")
            password_confirm = request.get_json().get("pass2")

            if password == password_confirm:
                if not check_password_hash(existed_user.password, password):
                    existed_user.password = generate_password_hash(
                        password, method="pbkdf2:sha256"
                    )
                    try:
                        db.session.commit()
                        sbj, msg = getMailReset(existed_user.name)

                        sendConfirmMail(existed_user.email, sbj, msg)
                        return jsonify({}), 200
                    except Exception as e:
                        db.session.rollback()
                        print("Error: ", e)
                        return jsonify({'error': e}), 400

                else:
                    return "New password is the same as the old one"
            else:
                return "Passwords do not match"
        else: 
            return "User not found"
    return render_template("reset_password_form.html", user_id=user_id)
