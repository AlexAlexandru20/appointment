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
        data = request.get_json()

        # Correct way to access dictionary keys
        name = data.get("name")
        phone = data.get("phone")

        user = User.query.filter_by(id=current_user.id).first()
        if user:
            updated = False  # Track if changes were made

            if name and name != user.name:
                user.name = name
                updated = True
            if phone and phone != user.phone:
                user.phone = phone
                updated = True

            if updated:  # Commit only if changes were made
                try:
                    db.session.commit()

                    sbj, msg = getMailInfo(user.name)
                    sendConfirmMail(user.email, sbj, msg)

                    return jsonify({'success': True}), 200
                except Exception as e:
                    db.session.rollback()  # Rollback in case of error
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'success': False, 'message': 'No changes made'}), 400
        else:
            return jsonify({'error': 'User not found'}), 404
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