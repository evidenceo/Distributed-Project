from flask import Flask, render_template, request, jsonify, url_for, redirect
from models import db, User, CycleData
from flask_login import LoginManager, login_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from flask_migrate import Migrate
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your-database.db'
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app, db)


# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
        end_date_obj = start_date_obj + timedelta(days=current_user.average_period_length)

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
        total_cycle_length = sum((periods[i + 1].start_date - periods[i].start_date).days for i in range(len(periods) - 1))
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
    update_period_predictions(user_id, periods[-1].start_date if periods else user.last_period_date, average_cycle_length, average_period_length)

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


@app.route('/update-period/${periodId}', methods=['POST'])
@login_required
def update_period_end():
    data = request.get_json()
    period_id = data.get('period_id')
    new_end_date = data.get('new_end_date')

    try:
        # Convert the new end date string to a datetime object
        new_end_date_obj = datetime.strptime(new_end_date, '%Y-%m-%d').date()

        # Fetch the period to be updated
        period = CycleData.query.get(period_id)
        if not period or period.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Period not found'}), 404

        # Update the end date
        period.end_date = new_end_date_obj
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


if __name__ == '__main__':
    app.run(debug=True)
