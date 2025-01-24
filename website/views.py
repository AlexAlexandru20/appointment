from flask import render_template, Blueprint, request, redirect, url_for, jsonify, flash
from datetime import datetime
from flask_login import current_user, login_required
from . import db

views = Blueprint('views', __name__)

def get_available_hours(selected_date):
    from .models import Appointments
    all_slots = [f"{hour}:00" for hour in range(9, 18)]
    booked_slots = [a.date.strftime("%H:%M") for a in Appointments.query.filter_by(date=selected_date).all()]
    
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    return available_slots


@views.route('/home')
@login_required
def home():
    if current_user.name == None or current_user.phone == None:
        return redirect(url_for('views.addDetails'))
    return render_template('home.html', user=current_user)


@views.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if request.method == 'POST' or request.method == 'GET':
        date = request.get_json().get('date')
        try:
                selected_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
                return jsonify({"error": "Invalid date format"}), 400

        available_slots = get_available_hours(selected_date)
        return jsonify({"available_hours": available_slots})


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
        if existing_appointment:
            flash("This slot is already booked. Please select another one.", "alert")
            return jsonify({"existed": True, "redirect": url_for('views.home')}), 200  # Conflict status

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