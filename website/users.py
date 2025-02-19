from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user, logout_user
from .models import User
from . import db
from .utils import sendConfirmMail

users = Blueprint('users', __name__)

def getMailInfo(name, deleted = False):
    sbj = "✍️ Actualizare profil - Modificările tale au fost salvate cu succes!"

    msg = f"""
    Salut {name}! 🌸,

    Îți confirmăm că au fost efectuate modificări în profilul tău la Boti BarberShop. 🛠️

    Dacă tu ai făcut aceste schimbări, totul este în regulă și nu trebuie să faci nimic altceva. ✅

    Dacă nu ai autorizat aceste modificări, te rugăm să ne contactezi imediat pentru a verifica securitatea contului tău.

    Cu drag,
    Boti BarberShop 🌸
    """

    if deleted:
        sbj = "❌ Cont șters – Ne pare rău să te vedem plecând!"

        msg = f"""
        Salut {name}! 🌸,

        Contul tău la Boti BarberShop a fost șters cu succes. 🏁

        Ne pare rău să te vedem plecând, dar dacă vreodată te răzgândești, te așteptăm cu brațele deschise! 🤗

        Dacă nu ai cerut această ștergere, te rugăm să ne contactezi imediat pentru a verifica situația.

        Mulțumim că ai fost parte din comunitatea noastră! 💙

        Cu drag,
        Boti BarberShop 🌸
        """


    return sbj, msg


@users.route('/change', methods = ['GET', 'POST'])
@login_required
def change():
    if request.method == 'POST':
        name = request.get_json().get('name')
        phone = request.get_json().get('phone')

        user = User.query.filter_by(id=current_user.id).first()
        if user:
            user.name = name
            user.phone = phone
            try:
                db.session.commit()

                sbj, msg = getMailInfo(name)

                sendConfirmMail(user.email, sbj, msg)

                return jsonify({'success': True}), 200
            except Exception as e:
                return jsonify({'error': e}), 400
        else:
            return jsonify({'success': False}), 400
    return render_template('change_details.html', user=current_user)


@users.route('/delete', methods = ['GET', 'POST'])
@login_required
def delete():
    if request.method == 'POST':
        from .models import Appointments, Details
        user = User.query.filter_by(id=current_user.id).first()

        if user:
            name = user.name
            email = user.email
            appoints = Appointments.query.filter_by(user_id=user.id).all()

            if appoints:
                for appoint in appoints:
                    db.session.delete(appoint)
            logout_user()
            db.session.delete(user)
            try:
                db.session.commit()
                sbj, msg = getMailInfo(name, deleted=True)

                sendConfirmMail(email, sbj, msg)
                return jsonify({'success': True}), 200
            except Exception as e:
                return jsonify({'error': e}), 400
        else:
            return jsonify({'success': False}), 400