from flask import render_template, Blueprint, request, redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
from flask_login import current_user, login_required
from . import db
from .utils import sendConfirmMail

views = Blueprint("views", __name__)

def getAvailableHours(selected_date):
    from .models import Appointments

    now = datetime.now()
    all_slots = [f"{hour}:00" for hour in range(9, 18)]
    if selected_date.weekday() == 5:
        all_slots = [f"{hour}:00" for hour in range(10, 14)]

    # If the selected date is today, filter out past hours
    if selected_date == now.date():
        all_slots = [hour for hour in all_slots if int(hour.split(":")[0]) > now.hour]
    
    if selected_date.weekday() == 6:
        return {}

    appoints = Appointments.query.filter_by(date=selected_date).all()
    booked_slots = [
        appoint.hour.strftime("%H:%M") for appoint in appoints if appoint.not_cancelled
    ]

    slots = {hour: hour in booked_slots for hour in all_slots}

    return slots


def getAppointments(old=False):
    from .models import Appointments

    appointments = {}
    cancelled = {}

    now = datetime.now()

    if old:
        existed_appoint = Appointments.query.filter(
            Appointments.user_id == current_user.id,
            (Appointments.date < now.date())
        ).all()
    else:
        existed_appoint = Appointments.query.filter(
            Appointments.user_id == current_user.id,
            (Appointments.date > now.date()) | (Appointments.date == now.date()),
        ).all()

    for appoint in existed_appoint:
        index = appoint.id
        if appoint.not_cancelled:
            appointments[index] = {
                "date": appoint.date.strftime("%d %B"),
                "hour": appoint.hour.strftime("%H:%M"),
                "created_at": appoint.created_at.strftime("%d-%m-%Y %H:%M"),
                "not_cancelled": appoint.not_cancelled
            }
        else:
            cancelled[index] = {
                "date": appoint.date.strftime("%d %B"),
                "hour": appoint.hour.strftime("%H:%M"),
                "created_at": appoint.created_at.strftime("%d-%m-%Y %H:%M"),
                "not_cancelled": appoint.not_cancelled,
                "cancelled_at": appoint.cancelled_at.strftime("%d-%m-%Y %H:%M"),
                "cancelled_by": appoint.cancelled_by
            }

    # Convert dictionary to list of values and sort
    sorted_appointments = dict(
        sorted(
            appointments.items(),
            key=lambda x: (
                datetime.strptime(x[1]["date"], "%d %B"),
                datetime.strptime(x[1]["hour"], "%H:%M")
            ),
            reverse=True
        )
    )

    sorted_cancelled = dict(
        sorted(
            cancelled.items(),
            key=lambda x: (
                datetime.strptime(x[1]["date"], "%d %B"),
                datetime.strptime(x[1]["hour"], "%H:%M")
            ),
            reverse=True
        )
    )
    return sorted_appointments, sorted_cancelled


def getMailConfirmed(name):
    sbj = "🎉 Cont creat cu succes - Bine ai venit la Boti BArberSHOP!"

    msg = f"""
    Salut {name},

    Yeey! 🥳 Tocmai ți-ai creat contul la Boti BarberSHOP și oficial faci parte din gașca noastră de răsfățați. 💆‍♀️✨

    Acum poți:
    ✅ Programa rapid vizitele tale la salon
    ✅ Primi oferte și surprize exclusive 🎁
    ✅ Ține evidența tuturor programărilor tale

    Dacă ai vreo întrebare sau ai nevoie de ajutor, suntem aici pentru tine! 📩

    Ne vedem curând pentru o doză de frumusețe și relaxare! 💖

    Cu drag,
    Boti BarberSHOP 🌸
    """

    return sbj, msg

# Email content for appointment confirmation
def getMailContent(name, date, hour, cancelled=False, moved=False):
    if cancelled:
        sbj = "😢 Programare anulată - Ne pare rău să te pierdem!"

        msg = f"""
            Salut {name} 👋,

            Of, veste tristă! Programarea ta de la Boti BarberSHOP a fost anulată.

            📅 Data: {date.strftime("%d-%m-%Y")}
            🕒 Ora: {hour.strftime("%H:%M")}

            Dacă a fost doar o mică schimbare de plan, nu-ți face griji! Te așteptăm oricând să reprogramezi și să îți oferim răsfățul pe care îl meriți. 💆‍♀️✨

            Dă-ne un semn când ești gata să ne vedem din nou! Până atunci, ai grijă de tine. 💖

            Cu drag,
            Boti BarberSHOP 🌸
        """
    elif moved:
        sbj = "🔄 Confirmare modificare programare - Ne vedem mai târziu!"

        msg = f"""
            Salut {name} 👋,

            Am primit cererea ta de a-ți reprograma vizita la Boti BarberSHOP. 🔄

            📅 Data: {date.strftime("%d-%m-%Y")}
            🕒 Ora: {hour.strftime("%H:%M")}
            📍 Locație: Sf. Gheorghe

            Ne bucurăm că ai găsit un alt moment potrivit pentru tine! Dacă ai nevoie să faci alte schimbări, nu ezita să ne contactezi.

            P.S. Nu uita să vii cu chef de relaxare și voie bună - restul e treaba noastră! 😎

            Ne vedem mai târziu,
            Boti BarberSHOP 💖
        """
    else:
        sbj = "🎉 Confirmare programare - Ne vedem curând!"

        msg = f"""
            Salut {name} 👋,

            Felicitări! Tocmai ți-ai rezervat un moment de răsfăț la Boti BarberSHOP. 🎊

            📅 Data: {date.strftime("%d-%m-%Y")}
            🕒 Ora: {hour.strftime("%H:%M")}
            📍 Locație: Sf. Gheorghe

            Ne bucurăm că ai ales să petreci puțin timp cu noi! 💆‍♀️💅 Dacă ai nevoie să schimbi ceva, dă-ne un semn cu cel puțin 3 ore înainte.

            P.S. Nu uita să vii cu chef de relaxare și voie bună - restul e treaba noastră! 😎

            Ne vedem curând,
            Boti BarberSHOP 💖    
        """
    
    return sbj, msg


@views.route("/home")
@login_required
def home():
    if current_user.name == None or current_user.phone == None:
        return redirect(url_for("views.addDetails"))
    my_appointments, cancelled = getAppointments()
    return render_template("home.html", user=current_user, appointments=my_appointments, cancelled=cancelled)


@views.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    if request.method == "POST" or request.method == "GET":
        date = request.get_json().get("date")
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            print(selected_date)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        available_slots = getAvailableHours(selected_date)
        return jsonify({"slots": available_slots})


@views.route("/submitAppointment", methods=["POST"])
@login_required
def submitAppointment():
    from .models import Appointments

    data = request.get_json()
    date = data.get("date")
    hour = data.get("hour")
    move_from = data.get("move_from")  # Renamed to match JS request

    if not date or not hour:
        return jsonify({"error": "Missing date or hour"}), 400

    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
        selected_hour = datetime.strptime(hour, "%H:%M").time()
    except ValueError:
        return jsonify({"error": "Invalid date or hour format"}), 400

    # Check if the selected slot is already booked
    existing_appointment = Appointments.query.filter_by(
        date=selected_date, hour=selected_hour
    ).first()

    if existing_appointment and existing_appointment.not_cancelled:
        return jsonify({"existed": True, "redirect": url_for('views.home')}), 200 

    # Handle moving an appointment
    if move_from:
        old_appointment = Appointments.query.filter_by(id=move_from, user_id=current_user.id).first()

        if not old_appointment:
            return jsonify({"error": "Original appointment not found"}), 404  # Not found
        db.session.delete(old_appointment)
        # Book new slot
        if existing_appointment and not existing_appointment.not_cancelled:
            # Reactivate previously canceled appointment
            existing_appointment.user_id = current_user.id
            existing_appointment.not_cancelled = True
            existing_appointment.cancelled_by = None
            existing_appointment.cancelled_at = None
            existing_appointment.created_at = datetime.now()
            new_appointment = existing_appointment
        else:
            # Create a new appointment
            new_appointment = Appointments(
                user_id=current_user.id,
                date=selected_date,
                hour=selected_hour,
                created_at=datetime.now(),
            )
            db.session.add(new_appointment)

        try:
            db.session.commit()
            flash("Appointment moved successfully!", "success")
            sbj, msg = getMailContent(current_user.name, selected_date, selected_hour, moved=True)
            sendConfirmMail(current_user.email, sbj, msg)
            return jsonify({"existed": False, "redirect": url_for("views.home")}), 200
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return jsonify({"error": "An error occurred while moving the appointment"}), 500

    # Create a new appointment
    new_appointment = Appointments(
        user_id=current_user.id,
        date=selected_date,
        hour=selected_hour,
        created_at=datetime.now(),
    )
    db.session.add(new_appointment)

    try:
        db.session.commit()
        current_user.user_appointments += 1
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        sbj, msg = getMailContent(current_user.name, selected_date, selected_hour)
        sendConfirmMail(current_user.email, sbj, msg)
        return jsonify({"existed": False, "redirect": url_for("views.home")}), 200
    except Exception as e:
        db.session.rollback()
        print("Error:", e)
        return jsonify({"error": "An error occurred while booking the appointment"}), 500


@views.route("/get-old-appoints", methods=["GET"])
@login_required
def getOldAppoints():
    appointments, cancelled = getAppointments(True)
    return jsonify({"appointments": appointments, "cancelled": cancelled}), 200


@views.route("/addDetails", methods=["GET", "POST"])
@login_required
def addDetails():
    if request.method == "POST":
        from .models import User

        name = request.form.get("name")
        phone = request.form.get("phone")
        user = User.query.filter_by(id=current_user.id).first()
        user.name = name
        user.phone = phone
        try:
            db.session.commit()
            sbj, msg = getMailConfirmed(name)

            sendConfirmMail(user.email, sbj, msg)
        except Exception as e:
            db.session.rollback()
            print("Error: ", e)
        return redirect(url_for("views.home"))
    return render_template("addDetails.html", user=current_user)


@views.route("/cancelAppointment", methods=["POST"])
@login_required
def cancelAppointment():
    id = request.get_json().get("id")
    if not id:
        return jsonify({"error": "Missing appointment ID"}), 400

    from .models import Appointments

    appointment = Appointments.query.filter_by(id=id, user_id=current_user.id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    if not appointment.not_cancelled:
        return jsonify({"error": "Appointment already cancelled"}), 400

    # Check if the appointment time is more than 3 hours from now
    appointment_time = datetime.combine(appointment.date, appointment.hour)
    if appointment_time - datetime.now() < timedelta(hours=3):
        print("Appointment time: ", appointment_time)
        return jsonify({"elapsed": True}), 200
    
    appointment.not_cancelled = False
    appointment.cancelled_at = datetime.now()
    appointment.cancelled_by = current_user.name

    try:
        db.session.commit()
        current_user.cancelled += 1
        db.session.commit()
        flash("Appointment cancelled successfully!", "success")
        sbj, msg = getMailContent(
            current_user.name,
            appointment.date,
            appointment.hour,
            cancelled=True,
        )
        sendConfirmMail(appointment.user.email, sbj, msg)
        return jsonify({"redirect": url_for("views.home")}), 200  # OK status
    except Exception as e:
        db.session.rollback()
        print("Error: ", e)
        return (
            jsonify({"error": "An error occurred while cancelling the appointment"}),
            500,
        )  # Internal Server Error status
