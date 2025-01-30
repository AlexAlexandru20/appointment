from flask import render_template, Blueprint, request, redirect, url_for, jsonify, flash
from datetime import datetime, time
from flask_login import current_user, login_required
from . import db

views = Blueprint('views', __name__)

def getAvailableHours(selected_date):
    from .models import Appointments
    all_slots = [f"{hour}:00" for hour in range(9, 18)]
    appoints = Appointments.query.filter_by(date=selected_date).all()
    booked_slots = [appoint.hour.strftime("%H:%M") for appoint in appoints if not appoint.cancelled]
    print(booked_slots)

    slots = {hour: hour in booked_slots for hour in all_slots}
    print(slots)

    return slots


def getAppointments():
    from .models import Appointments
    appointments = {}
    existed_appoint = Appointments.query.filter_by(user_id=current_user.id).all()
    for appoint in existed_appoint:
        index = appoint.id
        appointments[index] = {
            "date": appoint.date.strftime("%d-%m-%Y"),
            "hour": appoint.hour.strftime("%H:%M"),
            "created_at": appoint.created_at.strftime("%d-%m-%Y %H:%M"),
            "cancelled": appoint.cancelled
        }
        if appoint.cancelled:
            appointments[index]["cancelled_at"] = appoint.cancelled_at.strftime("%d-%m-%Y %H:%M")
            appointments[index]["cancelled_by"] = appoint.cancelled_by
    return appointments

@views.route('/home')
@login_required
def home():
    if current_user.name == None or current_user.phone == None:
        return redirect(url_for('views.addDetails'))
    my_appointments = getAppointments()
    print(my_appointments)
    return render_template('home.html', user=current_user, appointments=my_appointments)


@views.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if request.method == 'POST' or request.method == 'GET':
        date = request.get_json().get('date')
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            print(selected_date)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        available_slots = getAvailableHours(selected_date)
        return jsonify({"slots": available_slots})


@views.route('/submitAppointment', methods=['POST', 'GET'])
@login_required
def submitAppointment():
     if request.method == 'POST':
        from .models import User, Appointments
        data = request.get_json()
        date = data.get('date')
        hour = data.get('hour')
        if not date or not hour:
            return jsonify({"error": "Missing date or hour"}), 400

        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            selected_hour = datetime.strptime(hour, "%H:%M").time()
        except ValueError:
            return jsonify({"error": "Invalid date or hour format"}), 400

        # Check if the selected slot is already booked
        existing_appointment = Appointments.query.filter_by(date=selected_date, hour=selected_hour).first()
        if existing_appointment and not existing_appointment.cancelled:
            flash("This slot is already booked. Please select another one.", "alert")
            return jsonify({"existed": True, "redirect": url_for('views.home')}), 200  # Conflict status

        elif existing_appointment and existing_appointment.cancelled:
            existing_appointment.user_id = current_user.id
            existing_appointment.cancelled = False
            existing_appointment.cancelled_by = None
            existing_appointment.cancelled_at = None
            existing_appointment.created_at = datetime.now()
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print('Error: ', e)
                return jsonify({"error": "An error occurred while booking the appointment"}), 500
            
        # If available, create a new appointment
        new_appointment = Appointments(
            user_id=current_user.id,
            date=selected_date,
            hour=selected_hour,
            created_at=datetime.now()
        )
        db.session.add(new_appointment)
        try:
            db.session.commit()
            current_user.user_appointments += 1
            db.session.commit()
            flash("Appointment booked successfully!", "success")
            return jsonify({"existed": False, "redirect": url_for('views.home')}), 200  # OK status
        except Exception as e:
            db.session.rollback()
            print('Error: ', e)
            return jsonify({"error": "An error occurred while booking the appointment"}), 500  # Internal Server Error status

            
          


@views.route('/addDetails', methods=['GET', 'POST'])
@login_required
def addDetails():
    if request.method == 'POST':
        from .models import User
        name = request.form.get('name')
        phone = request.form.get('phone')
        user = User.query.filter_by(id=current_user.id).first()
        user.name = name
        user.phone = phone
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Error: ', e)
        return redirect(url_for('views.home'))
    return render_template('addDetails.html', user=current_user)


@views.route('/cancelAppointment', methods=['POST'])
@login_required
def cancelAppointment():
    id = request.get_json().get('id')
    if not id:
        return jsonify({"error": "Missing appointment ID"}), 400
    
    from .models import Appointments
    appointment = Appointments.query.filter_by(id=id).first()
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    
    if appointment.cancelled:
        return jsonify({"error": "Appointment already cancelled"}), 400
    
    appointment.cancelled = True
    appointment.cancelled_at = datetime.now()
    appointment.cancelled_by = current_user.name

    try:
        db.session.commit()
        current_user.cancelled += 1
        db.session.commit()
        flash("Appointment cancelled successfully!", "success")
        return jsonify({"redirect": url_for('views.home')}), 200  # OK status
    except Exception as e:
        db.session.rollback()
        print('Error: ', e)
        return jsonify({"error": "An error occurred while cancelling the appointment"}), 500  # Internal Server Error status
    
