from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

data = {
    'Admin': [],
    'Accounts': [],
    'Parking': [],
    'Tickets': []
}

PARKING_CAPACITY = 20
PARKING_FEE_PER_HOUR = 50

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def save_data():
    pd.DataFrame(data['Admin']).to_csv('admin_data.csv', index=False)
    pd.DataFrame(data['Accounts']).to_csv('accounts_data.csv', index=False)
    pd.DataFrame(data['Parking']).to_csv('parking_data.csv', index=False)
    pd.DataFrame(data['Tickets']).to_csv('tickets_data.csv', index=False)

def load_data():
    try:
        data['Admin'] = pd.read_csv('admin_data.csv').to_dict('records') if not pd.read_csv('admin_data.csv').empty else []
        data['Accounts'] = pd.read_csv('accounts_data.csv').to_dict('records') if not pd.read_csv('accounts_data.csv').empty else []
        data['Parking'] = pd.read_csv('parking_data.csv').to_dict('records') if not pd.read_csv('parking_data.csv').empty else []
        data['Tickets'] = pd.read_csv('tickets_data.csv').to_dict('records') if not pd.read_csv('tickets_data.csv').empty else []
    except (FileNotFoundError, pd.errors.EmptyDataError):
        pass

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        
        admin = next((a for a in data['Admin'] if a['Username'] == username and a['PIN'] == pin), None)
        if admin:
            session['admin_logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/')
@login_required
def home():
    available_spaces = PARKING_CAPACITY - len([v for v in data['Parking'] if not v['Check-Out']])
    return render_template('index.html', 
                         available_spaces=available_spaces, 
                         total_capacity=PARKING_CAPACITY,
                         admin_name=session.get('username'))

@app.route('/create_admin', methods=['GET', 'POST'])
@login_required
def create_admin():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        
        # Check if admin already exists
        if any(a['Username'] == username for a in data['Admin']):
            flash('Username already exists!', 'error')
            return render_template('create_admin.html')
            
        if username and pin:
            data['Admin'].append({'Username': username, 'PIN': pin})
            save_data()
            flash('Admin created successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('All fields are required.', 'error')
    return render_template('create_admin.html')

@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        vehicle_type = request.form.get('vehicle_type', '').strip()
        license_plate = request.form.get('license_plate', '').strip().upper()
        
        # Print debug information
        print(f"Received form data - Type: {vehicle_type}, Plate: {license_plate}")
        
        if not vehicle_type or not license_plate:
            flash("All fields are required.", "error")
            return render_template('add_vehicle.html',admin_name=session.get('username'))
            
        if not license_plate.isalnum():  # Basic plate validation
            flash("Invalid license plate format.", "error")
            return render_template('add_vehicle.html',admin_name=session.get('username'))
        
        # Check if parking capacity is reached
        if len(data['Parking']) >= PARKING_CAPACITY:
            flash("Parking is full. Cannot add more vehicles.", "error")
            return render_template('add_vehicle.html',admin_name=session.get('username'))

        # Add vehicle to parking data
        data['Parking'].append({
            'License Plate': license_plate,
            'Vehicle Type': vehicle_type,
            'Check-In': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Check-Out': None
        })
        
        # Create a ticket for the vehicle
        data['Tickets'].append({
            'License Plate': license_plate,
            'Vehicle Type': vehicle_type,
            'Check-In': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Check-Out': None,
            'Fee': 0
        })
        
        save_data()
        flash("Vehicle added successfully!", "success")
        return redirect(url_for('home'))
    
    return render_template('add_vehicle.html')
    if request.method == 'POST':
        vehicle_type = request.form.get('vehicle_type', '').strip()
        license_plate = request.form.get('license_plate', '').strip().upper()
        
        # Print debug information
        print(f"Received form data - Type: {vehicle_type}, Plate: {license_plate}")
        
        if not vehicle_type or not license_plate:
            flash("All fields are required.", "error")
            return render_template('add_vehicle.html',admin_name=session.get('username'))
            
        if not license_plate.isalnum():  # Basic plate validation
            flash("Invalid license plate format.", "error")
            return render_template('add_vehicle.html',admin_name=session.get('username'))
        
        # Check if parking capacity is reached
        if len(data['Parking']) >= PARKING_CAPACITY:
            flash("Parking is full. Cannot add more vehicles.", "error")
            return render_template('add_vehicle.html',admin_name=session.get('username'))

        # Add vehicle to parking data
        data['Parking'].append({
            'License Plate': license_plate,
            'Vehicle Type': vehicle_type,
            'Check-In': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Check-Out': None
        })
        save_data()
        flash("Vehicle added successfully!", "success")
        return redirect(url_for('home'))
    
    return render_template('add_vehicle.html')


@app.route('/check_out_vehicle', methods=['GET', 'POST'])
@login_required
def check_out_vehicle():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        check_out_time = datetime.now()
        parked_vehicle = next((v for v in data['Parking'] if v['License Plate'] == license_plate and not v['Check-Out']), None)
        if not parked_vehicle:
            flash("Vehicle not found or already checked out.", "error")
        else:
            parked_vehicle['Check-Out'] = check_out_time.strftime("%Y-%m-%d %H:%M:%S")
            fee = calculate_fee(parked_vehicle['Check-In'], check_out_time)
            save_data()
            flash(f"Check-out successful. Parking fee: INR {fee}", "success")
            return redirect(url_for('home'))
    return render_template('check_out_vehicle.html',admin_name=session.get('username'))

@app.route('/generate_report')
@login_required
def generate_report():
    total_vehicles = len(data['Parking'])
    total_tickets = len(data['Tickets'])
    total_revenue = sum(
        calculate_fee(v['Check-In'], datetime.strptime(v['Check-Out'], "%Y-%m-%d %H:%M:%S"))
        for v in data['Parking'] if v['Check-Out']
    )
    return render_template('generate_report.html', 
                         total_vehicles=total_vehicles,
                         total_tickets=total_tickets,
                         total_revenue=total_revenue)

def calculate_fee(check_in_time, check_out_time):
    if isinstance(check_in_time, str):
        check_in_time = datetime.strptime(check_in_time, "%Y-%m-%d %H:%M:%S")
    duration = check_out_time - check_in_time
    hours = duration.total_seconds() // 3600
    return max(1, int(hours)) * PARKING_FEE_PER_HOUR

if __name__ == '__main__':
    load_data()
    # Create default admin if none exists
    if not data['Admin']:
        data['Admin'].append({'Username': 'admin', 'PIN': '1234'})
        save_data()
    app.run(debug=True)