from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from models import db, User, CycleData, SymptomData, ReportInfo
from flask_login import LoginManager, login_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from flask_migrate import Migrate
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from flask_mail import Message, Mail
from PyPDF2 import PdfReader, PdfWriter
import os
import secrets



app = Flask(__name__)

# configure database and mail
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your-database.db'
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '5cdf582071d1f9'
app.config['MAIL_PASSWORD'] = '26d73b04758c15'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'period-traker-20@example.com'  # dummy email

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)


# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# INDEX.HTML
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET'])
def signup_form():
    return render_template('signup.html')


# Sign Up endpoint
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    password = data['password']

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already in use'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password, first_name=first_name, last_name=last_name)
    db.session.add(new_user)
    db.session.commit()

    # Return a JSON response
    return jsonify({'success': True, 'message': 'Signup successful!'}), 200


# Login endpoint
@app.route('/login', methods=['POST'])
def login(authenticated=None):
    data = request.get_json()
    email = data['email']
    password = data['password']

    # Authenticate the user here

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/check-user-data', methods=['GET'])
@login_required
def check_user_data():
    needs_setup = current_user.last_period_date is None
    return jsonify({'needs_setup': needs_setup})


@app.route('/setup', methods=['GET'])
@login_required
def setup():
    return render_template('setup.html')


@app.route('/setup', methods=['POST'])
@login_required
def setup_user():
    data = request.get_json()

    try:
        last_period_date = datetime.strptime(data['lastPeriodDate'], '%Y-%m-%d').date()
        average_period_length = int(data['averagePeriodLength'])
        average_cycle_length = int(data['averageCycleLength'])

        # Update user info
        current_user.last_period_date = last_period_date
        current_user.average_period_length = average_period_length
        current_user.average_cycle_length = average_cycle_length
        db.session.commit()

        # Save initial Known period
        create_initial_known_period(current_user.id, last_period_date, average_period_length)

        # Generate initial period predictions
        generate_initial_predictions(current_user.id, last_period_date, average_cycle_length, average_period_length)

        return jsonify({'success': True, 'message': 'Setup completed successfully'}), 200
    except (ValueError, KeyError):
        # Handle invalid input
        return jsonify({'success': False, 'message': 'Invalid input data'}), 400


def generate_initial_predictions(user_id, start_date, cycle_length, period_length):
    predictions = []
    for i in range(1, 13):  # Generate predictions for the next 12 cycles
        predicted_start = start_date + timedelta(days=cycle_length * i)
        predicted_end = predicted_start + timedelta(days=period_length)
        predictions.append(
            CycleData(user_id=user_id, start_date=predicted_start, end_date=predicted_end, is_predicted=True))

    db.session.bulk_save_objects(predictions)
    db.session.commit()


def create_initial_known_period(user_id, start_date, period_length):
    end_date = start_date + timedelta(days=period_length)
    known_period = CycleData(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        is_predicted=False  # This is a known period, not a prediction
    )
    db.session.add(known_period)
    db.session.commit()


@app.route('/main', methods=['GET'])
@login_required
def main_page():
    return render_template('main.html', first_name=current_user.first_name)


@app.route('/user-cycle-info', methods=['GET'])
@login_required
def user_cycle_info():
    # Basic user cycle information
    user_info = {
        'last_period_date': current_user.last_period_date.strftime(
            '%Y-%m-%d') if current_user.last_period_date else None,
        'average_cycle_length': current_user.average_cycle_length,
        'average_period_length': current_user.average_period_length
    }

    # Fetch all known period records
    known_periods = CycleData.query.filter_by(user_id=current_user.id, is_predicted=False).all()
    known = [
        {
            'id': period.id,
            'start_date': period.start_date.strftime('%Y-%m-%d'),
            'end_date': period.end_date.strftime('%Y-%m-%d')
        } for period in known_periods
    ]

    # Fetch predicted periods
    predicted_periods = CycleData.query.filter_by(user_id=current_user.id, is_predicted=True).all()
    predictions = [
        {
            'start_date': period.start_date.strftime('%Y-%m-%d'),
            'end_date': period.end_date.strftime('%Y-%m-%d')
        } for period in predicted_periods
    ]

    # Include predictions in the response
    user_info['known_periods'] = known
    user_info['predictions'] = predictions

    return jsonify(user_info)


@app.route('/add-period', methods=['POST'])
@login_required
def add_period():
    data = request.get_json()
    start_date = data.get('start_date')

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = start_date_obj + timedelta(days=current_user.average_period_length - 1)

        # Create a new period record
        new_period = CycleData(user_id=current_user.id, start_date=start_date_obj, end_date=end_date_obj)
        db.session.add(new_period)
        db.session.commit()

        # Recalculate averages and update predictions
        recalculate_averages_and_update_predictions(current_user.id)

        return jsonify({'success': True, 'message': 'Period data added successfully'}), 200
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400


def recalculate_averages_and_update_predictions(user_id):
    user = User.query.get(user_id)
    periods = CycleData.query.filter_by(user_id=user_id, is_predicted=False).order_by(CycleData.start_date).all()

    # Ensure there are enough periods to calculate averages
    if len(periods) >= 2:
        # Calculate average period length
        total_period_length = sum((period.end_date - period.start_date).days for period in periods)
        average_period_length = total_period_length / len(periods)

        # Calculate average cycle length (time between start dates of consecutive periods)
        total_cycle_length = sum(
            (periods[i + 1].start_date - periods[i].start_date).days for i in range(len(periods) - 1))
        average_cycle_length = total_cycle_length / (len(periods) - 1)
    else:
        # If there aren't enough periods, use the user's existing average values
        user = User.query.get(user_id)
        average_period_length = user.average_period_length or 0
        average_cycle_length = user.average_cycle_length or 0

    # Update user's average period and cycle length
    user.average_period_length = int(average_period_length)
    user.average_cycle_length = int(average_cycle_length)

    # Update predictions
    update_period_predictions(user_id, periods[-1].start_date if periods else user.last_period_date,
                              average_cycle_length, average_period_length)

    db.session.commit()


def update_period_predictions(user_id, last_period_start, average_cycle_length, average_period_length):
    # Clear existing predictions
    CycleData.query.filter_by(user_id=user_id, is_predicted=True).delete()

    # Generate new predictions for the next 12 cycles
    for i in range(1, 13):  # Predict the next 12 cycles
        predicted_start_date = last_period_start + timedelta(days=int(average_cycle_length * i))
        predicted_end_date = predicted_start_date + timedelta(days=int(average_period_length))

        # Add prediction to database
        prediction = CycleData(
            user_id=user_id,
            start_date=predicted_start_date,
            end_date=predicted_end_date,
            is_predicted=True
        )
        db.session.add(prediction)
    db.session.commit()


@app.route('/update-period-end', methods=['POST'])
@login_required
def update_period_end():
    data = request.get_json()
    new_end_date_str = data.get('new_end_date')

    try:
        # Convert the new end date string to a datetime object
        new_end_date_obj = datetime.strptime(new_end_date_str, '%Y-%m-%d').date()

        # Find the closest period before the selected end date
        closest_period = None
        min_diff = timedelta.max
        for period in current_user.cycle_data:
            if new_end_date_obj >= period.start_date and new_end_date_obj - period.start_date < min_diff:
                closest_period = period
                min_diff = new_end_date_obj - period.start_date

        if closest_period:
            # Update the end date of the closest period
            closest_period.end_date = new_end_date_obj
            db.session.commit()

        # Recalculate averages and predictions
        recalculate_averages_and_update_predictions(current_user.id)

        return jsonify({'success': True, 'message': 'Period end date updated successfully'}), 200
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400


@app.route('/delete-period/<int:period_id>', methods=['DELETE'])
@login_required
def delete_period(period_id):
    period = CycleData.query.get(period_id)
    if not period or period.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Period not found'}), 404

    db.session.delete(period)
    db.session.commit()

    # Recalculate averages and predictions
    recalculate_averages_and_update_predictions(current_user.id)

    return jsonify({'success': True, 'message': 'Period data deleted successfully'}), 200


@app.route('/log', methods=['GET'])
@login_required
def log_page():
    date = request.args.get('date', default=None)
    return render_template('log.html', date=date)


@app.route('/save-symptoms', methods=['POST'])
@login_required
def save_symptoms():
    data = request.get_json()
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    symptom_record = SymptomData.query.filter_by(user_id=current_user.id, date=date).first()

    if symptom_record:
        # Update existing record
        symptom_record.flow = data.get('flow', symptom_record.flow)
        symptom_record.medicine = data.get('medicine', symptom_record.medicine)
        symptom_record.intercourse_protection = data.get('sex',
                                                         symptom_record.intercourse_protection)
        symptom_record.symptoms = data.get('symptoms', symptom_record.symptoms)
        symptom_record.mood = data.get('mood', symptom_record.mood)
        symptom_record.notes = data.get('notes', symptom_record.notes)
        db.session.commit()
    else:
        # Create a new record
        new_symptom_data = SymptomData(
            user_id=current_user.id,
            date=date,
            flow=data.get('flow', ''),
            medicine=data.get('medicine', ''),
            intercourse_protection=data.get('sex', ''),
            symptoms=data.get('symptom', ''),
            mood=data.get('mood', ''),
            notes=data.get('add-notes', '')
        )
        db.session.add(new_symptom_data)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Symptoms saved successfully'})


@app.route('/get-symptoms', methods=['GET'])
@login_required
def get_symptoms():
    date_str = request.args.get('date')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        symptom_data = SymptomData.query.filter_by(user_id=current_user.id, date=date).first()

        if symptom_data:
            return jsonify({
                'success': True,
                'data': {
                    'flow': symptom_data.flow,
                    'medicine': symptom_data.medicine,
                    'sex': symptom_data.intercourse_protection,
                    'symptoms': symptom_data.symptoms,
                    'mood': symptom_data.mood,
                    'notes': symptom_data.notes
                }
            }), 200
        else:
            return jsonify({'success': False, 'message': 'No data found'}), 404
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400


# REPORT.HTML
@app.route('/report', methods=['GET'])
@login_required
def report_page():
    return render_template('report.html')


@app.route('/report-data', methods=['GET'])
@login_required
def report_data():
    user_info = {
        'average_cycle_length': current_user.average_cycle_length,
        'average_period_length': current_user.average_period_length,
        'fertility_window': calculate_fertility_window(current_user.id)
    }
    return jsonify(user_info)


def calculate_fertility_window(user_id):
    # Fetch the next predicted cycle for the user
    next_predicted_cycle = CycleData.query.filter_by(user_id=user_id, is_predicted=True).order_by(
        CycleData.start_date).first()

    if not next_predicted_cycle:
        return None  # Return None if no predicted cycle is found

    # Estimate ovulation day (14 days before the start of the next cycle)
    ovulation_day = next_predicted_cycle.start_date - timedelta(days=14)

    # Fertility window: 5 days before and 1 day after the ovulation day
    fertile_window_start = ovulation_day - timedelta(days=5)
    fertile_window_end = ovulation_day + timedelta(days=1)

    return {
        'start': fertile_window_start.strftime('%Y-%m-%d'),
        'end': fertile_window_end.strftime('%Y-%m-%d')
    }


@app.route('/past-cycles', methods=['GET'])
@login_required
def past_cycles():
    user_id = current_user.id

    past_cycles = CycleData.query.filter_by(user_id=user_id, is_predicted=False).order_by(
        CycleData.start_date.desc()).all()

    cycles_data = [{'start_date': cycle.start_date.strftime('%Y-%m-%d'),
                    'end_date': cycle.end_date.strftime('%Y-%m-%d')}
                   for cycle in past_cycles]

    return jsonify(cycles_data)


@app.route('/predicted-cycles', methods=['GET'])
@login_required
def predicted_cycles():
    user_id = current_user.id

    predicted_cycles = CycleData.query.filter_by(user_id=user_id, is_predicted=True).order_by(
        CycleData.start_date.desc()).all()

    cycles_data = [{'start_date': cycle.start_date.strftime('%Y-%m-%d'),
                    'end_date': cycle.end_date.strftime('%Y-%m-%d')}
                   for cycle in predicted_cycles]

    return jsonify(cycles_data)


# SHAREDATA.HTML
@app.route('/sharedata', methods=['GET'])
@login_required
def share_data():
    return render_template('sharedata.html')


@app.route('/send-report', methods=['POST'])
@login_required
def send_report():
    data = request.get_json()
    recipient_email = data['recipientEmail']
    recipient_name = data['recipientName']
    password = data['password']

    # Fetch the user's first name and last name
    user = User.query.get(current_user.id)

    # Generate PDF report
    file_path = generate_pdf_report(current_user.id)

    # Encrypt the PDF report
    encrypted_file_path = encrypt_pdf(file_path, password)

    # Save the password (hashed) and the report's identifier in the database for verification
    store_report_info(current_user.id, encrypted_file_path, password)

    # Send the email with the report attached
    send_report_email(recipient_email, recipient_name, encrypted_file_path, user.first_name, user.last_name)

    # Optional: Clean up the PDF file from the server after sending the email
    os.remove(file_path)
    os.remove(encrypted_file_path)

    return jsonify({'success': True, 'message': 'Report sent successfully'})


@app.route('/verify-user', methods=['POST'])
@login_required
def verify_user():
    data = request.get_json()
    login_password = data['loginPassword']

    # verify user's login password
    user = User.query.get(current_user.id)
    if not check_password_hash(user.password_hash, login_password):
        return jsonify({'success': False, 'message': 'Invalid login password'}), 401

    return jsonify({'success': True, 'message': 'Login Verification successful'})


@app.route('/encrypt-report', methods=['POST'])
@login_required
def encrypt_report():
    data = request.get_json()
    report_password = data['reportPassword']

    # Generate PDF report
    file_path = generate_pdf_report(current_user.id)

    # Encrypt the PDF report
    encrypted_file_path = encrypt_pdf(file_path, report_password)

    # Store the path or identifier of the encrypted file
    # (in the user session, database, etc., depending on your application logic)
    store_encrypted_file_path(encrypted_file_path)
    return jsonify({'success': True})


@app.route('/download-report', methods=['GET'])
@login_required
def download_report():
    # Retrieve the stored path or identifier of the encrypted file
    encrypted_file_path = retrieve_encrypted_file_path()
    return send_file(encrypted_file_path, as_attachment=True)

def generate_pdf_report(user_id):
    user, past_cycles, symptoms = get_user_data(user_id)

    file_name = f'user_report_{user_id}.pdf'
    file_path = os.path.join('pdf-reports', file_name)

    # Create a canvas to draw on the PDF
    c = canvas.Canvas(file_path)

    # Add content to the PDF
    # Adding a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "Period Tracker")

    # Adding User Name
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, f"Report for {user.first_name} {user.last_name}")

    # Adding average cycle and period lengths
    c.setFont("Helvetica", 12)
    c.drawString(72, 780, f"Average Cycle Length: {user.average_cycle_length} days")
    c.drawString(72, 760, f"Average Period Length: {user.average_period_length} days")

    # Adding Past Cycles
    y_position = 740
    for cycle in past_cycles:
        cycle_info = f"Cycle from {cycle.start_date.strftime('%Y-%m-%d')} to {cycle.end_date.strftime('%Y-%m-%d')}"
        c.drawString(72, y_position, cycle_info)
        y_position -= 20  # Adjust y_position for next line

    # Adding Symptoms
    y_position = 700
    for symptom in symptoms:
        symptom_info = f"Symptoms on {symptom.date.strftime('%Y-%m-%d')}:{[symptom.flow, symptom.medicine,
                                                                           symptom.intercourse_protection, 
                                                                           symptom.symptoms, symptom.mood, 
                                                                           symptom.notes]}"
        c.drawString(72, y_position, symptom_info)
        y_position -= 20  # Adjust y_position for next line

        # Check if we need to start a new page
        if y_position < 50:  # Example threshold for the bottom of the page
            c.showPage()  # Start a new page
            c.setFont("Helvetica", 12)  # Reset the font
            y_position = 800  # Reset y_position to the top of the new page

    c.save()

    return file_path


def encrypt_pdf(file_path, password):
    # Read the original PDF
    reader = PdfReader(file_path)
    writer = PdfWriter()

    # Copy all pages from the reader to the writer
    for page in reader.pages:
        writer.add_page(page)

    # Encrypt the new PDF
    writer.encrypt(password)

    # Save the encrypted PDF to a new file
    encrypted_file_path = file_path.replace(".pdf", "_encrypted.pdf")
    with open(encrypted_file_path, "wb") as encrypted_file:
        writer.write(encrypted_file)

    return encrypted_file_path


def get_user_data(user_id):
    # Assuming you have models set up for User, CycleData, SymptomData, etc.
    user = User.query.get(user_id)
    past_cycles = CycleData.query.filter_by(user_id=user_id, is_predicted=False).all()
    symptoms = SymptomData.query.filter_by(user_id=user_id).all()

    return user, past_cycles, symptoms


def store_report_info(user_id, file_path, password):
    report_info = ReportInfo(user_id=user_id, file_path=file_path, password=password)
    db.session.add(report_info)
    db.session.commit()


def send_report_email(recipient_email, recipient_name, file_path, user_first_name, user_last_name):
    # Construct the email subject with the user's name
    email_subject = f"{user_first_name} {user_last_name}'s Period Tracker Report"

    # Construct the message
    msg = Message(email_subject,
                  sender="period-tracker-20@example.com",  # default sender from your Mailtrap config
                  recipients=[recipient_email])

    msg.body = f"Hello {recipient_name},\n\nPlease find attached the period tracker report."

    with open(file_path, 'rb') as fp:
        msg.attach(filename=os.path.basename(file_path),
                   content_type="application/pdf",
                   data=fp.read())

    mail.send(msg)


def store_encrypted_file_path(encrypted_file_path):
    # Store the encrypted file path in the user's session
    session['encrypted_file_path'] = encrypted_file_path


def retrieve_encrypted_file_path():
    # Retrieve the encrypted file path from the user's session
    return session.get('encrypted_file_path')


# ACCOUNT.HTML, EDIT_PROFILE.HTML, RECOMMENDATIONS.HTML
@app.route('/account', methods=['GET'])
@login_required
def account():
    user = User.query.get(current_user.id)
    return render_template('account.html', user=user)


@app.route('/show_edit_profile', methods=['GET'])
@login_required
def show_edit_profile():
    user = User.query.get(current_user.id)
    return render_template('edit_profile.html', user=user)


@app.route('/edit_profile', methods=['POST'])
@login_required
def process_edit_profile():
    user = User.query.get(current_user.id)
    if user:
        user.first_name = request.form.get('firstName')
        user.last_name = request.form.get('lastName')
        user.email = request.form.get('email')
        db.session.commit()

        # Redirect to a route, not directly to an HTML file
        return redirect(url_for('account'))


@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Account deleted'})


@app.route('/recommendations', methods=['GET'])
@login_required
def recommendations():
    return render_template('recommendations.html')




if __name__ == '__main__':
    app.run(debug=True)
