import os
import io
import random
import string
import base64
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session
)
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
from models import db, Bus, Route, Schedule, Seat, Booking, BoardingPoint, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ritesh-tours-travels-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bus_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADMIN_PASSWORD = 'Ritesh'
UPI_ID = 'riteshtravels@upi'
MERCHANT_NAME = 'Ritesh Tours & Travels'

db.init_app(app)


# ─── Auth Helpers ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged' not in session or not session['admin_logged']:
            flash('Admin access required. Please login as admin.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@app.context_processor
def inject_user():
    return dict(current_user=get_current_user(), admin_logged=session.get('admin_logged', False))


# ─── Helper ──────────────────────────────────────────────────────────────────
def generate_booking_id():
    return 'RT' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def create_seats_for_schedule(schedule):
    """Create seat objects for a new schedule based on bus type."""
    seat_map = {
        'AC Seater': [('seater', 'S') for _ in range(40)],
        'Non-AC Seater': [('seater', 'S') for _ in range(45)],
        'AC Sleeper': [('sleeper', 'U') for _ in range(16)],
        'Semi-Sleeper': [('sleeper', 'U') for _ in range(24)],
    }
    seats_spec = seat_map.get(schedule.bus.bus_type, [('seater', 'S') for _ in range(40)])
    for i, (stype, _) in enumerate(seats_spec, 1):
        db.session.add(Seat(
            schedule_id=schedule.id,
            seat_number=str(i),
            seat_type=stype,
        ))
    db.session.commit()


def generate_upi_qr(amount, booking_id):
    """Generate a styled UPI QR code and return it as base64 string."""
    upi_string = f"upi://pay?pa={UPI_ID}&pn={MERCHANT_NAME}&am={amount}&cu=INR&tn=Booking%20{booking_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(upi_string)
    qr.make(fit=True)

    # Create styled QR with colors
    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        color_mask=SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=(26, 26, 46),
        ),
    ).convert('RGB')

    # Add merchant name below QR
    w, h = qr_img.size
    final_img = Image.new('RGB', (w, h + 80), (255, 255, 255))
    final_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(final_img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()
        small_font = font

    draw.text((w // 2, h + 10), "Scan to Pay", fill=(226, 55, 68), font=font, anchor="mt")
    draw.text((w // 2, h + 35), f"₹{amount}", fill=(26, 26, 46), font=font, anchor="mt")
    draw.text((w // 2, h + 58), UPI_ID, fill=(108, 117, 125), font=small_font, anchor="mt")

    buf = io.BytesIO()
    final_img.save(buf, format='PNG')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


# ─── Seed Data ───────────────────────────────────────────────────────────────
def seed_database():
    if Bus.query.first():
        return  # already seeded

    # Create default admin user
    admin = User(
        name='Admin',
        email='admin@riteshtravels.com',
        phone='9876543210',
        is_admin=True,
    )
    admin.set_password(ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()

    # Route
    route = Route(
        origin='Gadinglaj',
        destination='Pune',
        distance_km=340,
        duration_hours=7.5,
    )
    db.session.add(route)
    db.session.commit()

    # Buses
    buses_data = [
        {
            'bus_name': 'Ritesh Travels AC',
            'bus_type': 'AC Seater',
            'total_seats': 40,
            'operator': 'Ritesh Tours and Travels',
            'bus_number': 'MH-09-RS-1001',
            'amenities': 'AC, Charging Point, Water Bottle, Blanket',
        },
        {
            'bus_name': 'Ritesh Express',
            'bus_type': 'Non-AC Seater',
            'total_seats': 45,
            'operator': 'Ritesh Tours and Travels',
            'bus_number': 'MH-09-RS-1002',
            'amenities': 'Water Bottle, Charging Point',
        },
        {
            'bus_name': 'Ritesh Sleeper Elite',
            'bus_type': 'AC Sleeper',
            'total_seats': 16,
            'operator': 'Ritesh Tours and Travels',
            'bus_number': 'MH-09-RS-1003',
            'amenities': 'AC, Blanket, Pillow, Charging Point, Water Bottle',
        },
        {
            'bus_name': 'Ritesh Semi-Sleeper',
            'bus_type': 'Semi-Sleeper',
            'total_seats': 24,
            'operator': 'Ritesh Tours and Travels',
            'bus_number': 'MH-09-RS-1004',
            'amenities': 'Recliner Seats, Charging Point, Water Bottle',
        },
        {
            'bus_name': 'Ritesh Luxury',
            'bus_type': 'AC Seater',
            'total_seats': 40,
            'operator': 'Ritesh Tours and Travels',
            'bus_number': 'MH-09-RS-1005',
            'amenities': 'AC, Wi-Fi, Charging Point, Water Bottle, Snacks, LED Screen',
        },
        {
            'bus_name': 'Ritesh Classic',
            'bus_type': 'Non-AC Seater',
            'total_seats': 45,
            'operator': 'Ritesh Tours and Travels',
            'bus_number': 'MH-09-RS-1006',
            'amenities': 'Charging Point, Water Bottle',
        },
    ]
    buses = []
    for bd in buses_data:
        b = Bus(**bd)
        db.session.add(b)
        buses.append(b)
    db.session.commit()

    # Boarding & dropping points
    boarding_names = [
        'Gadinglaj Bus Stand',
        'Gadinglaj - Highway Junction',
        'Radhanagari Naka',
    ]
    dropping_names = [
        'Pune Swargate Bus Stand',
        'Pune - Pune Satara Road',
        'Kothrud Bus Stop',
        'Pune - Hinjewadi Phase 3',
    ]
    for name in boarding_names:
        db.session.add(BoardingPoint(route_id=route.id, name=name, time_offset_min=0))
    for name in dropping_names:
        db.session.add(BoardingPoint(route_id=route.id, name=name, time_offset_min=0))
    db.session.commit()

    # Schedules for next 7 days
    departure_times = [
        (21, 30),
        (22, 0),
        (23, 0),
        (23, 30),
        (6, 0),
        (7, 30),
    ]
    prices = {
        'AC Seater': 750,
        'Non-AC Seater': 500,
        'AC Sleeper': 1000,
        'Semi-Sleeper': 650,
    }

    today = date.today()
    for day_offset in range(7):
        d = today + timedelta(days=day_offset)
        for i, bus in enumerate(buses):
            h, m = departure_times[i % len(departure_times)]
            dep = datetime(d.year, d.month, d.day, h, m)
            arr = dep + timedelta(hours=route.duration_hours)
            price = prices.get(bus.bus_type, 500) + random.choice([0, 0, 50, 100, -50])

            sched = Schedule(
                bus_id=bus.id,
                route_id=route.id,
                departure_time=dep,
                arrival_time=arr,
                price=round(price, -1),
                available_seats=bus.total_seats,
                travel_date=d,
                status='active',
            )
            db.session.add(sched)
            db.session.commit()
            create_seats_for_schedule(sched)

    db.session.commit()


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([name, email, phone, password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash(f'Welcome {name}! Account created successfully.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.name}!', 'success')
            next_url = request.args.get('next', url_for('index'))
            return redirect(next_url)

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged'] = True
            flash('Welcome to Admin Panel!', 'success')
            return redirect(url_for('admin'))
        flash('Invalid admin password.', 'danger')
        return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('index'))


# ─── Main Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    routes = Route.query.all()
    return render_template('index.html', routes=routes)


@app.route('/search', methods=['GET', 'POST'])
def search():
    origin = request.args.get('origin', 'Gadinglaj')
    destination = request.args.get('destination', 'Pune')
    travel_date_str = request.args.get('travel_date', date.today().isoformat())
    bus_type = request.args.get('bus_type', '')

    try:
        travel_date = date.fromisoformat(travel_date_str)
    except ValueError:
        travel_date = date.today()

    route = Route.query.filter_by(origin=origin, destination=destination).first()
    if not route:
        flash('No route found for the selected cities.', 'warning')
        return render_template('search_results.html', schedules=[], origin=origin,
                               destination=destination, travel_date=travel_date, bus_type=bus_type)

    query = Schedule.query.filter(
        Schedule.route_id == route.id,
        Schedule.travel_date == travel_date,
        Schedule.status == 'active',
        Schedule.available_seats > 0,
    )
    if bus_type:
        query = query.join(Bus).filter(Bus.bus_type == bus_type)

    schedules = query.order_by(Schedule.departure_time).all()

    if travel_date == date.today():
        now = datetime.now()
        schedules = [s for s in schedules if s.departure_time > now]

    return render_template('search_results.html',
                           schedules=schedules,
                           origin=origin,
                           destination=destination,
                           travel_date=travel_date,
                           bus_type=bus_type,
                           route=route)


@app.route('/select-seats/<int:schedule_id>')
def select_seats(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    seats = Seat.query.filter_by(schedule_id=schedule_id).order_by(Seat.seat_number.cast(db.Integer)).all()
    boarding_points = BoardingPoint.query.filter_by(route_id=schedule.route_id).all()
    return render_template('seat_selection.html',
                           schedule=schedule,
                           seats=seats,
                           boarding_points=boarding_points)


@app.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    schedule_id = request.form.get('schedule_id', type=int)
    selected_seats = request.form.getlist('selected_seats')
    passenger_name = request.form.get('passenger_name', '').strip()
    passenger_email = request.form.get('passenger_email', '').strip()
    passenger_phone = request.form.get('passenger_phone', '').strip()
    boarding_point = request.form.get('boarding_point', '')
    dropping_point = request.form.get('dropping_point', '')
    passenger_gender = request.form.get('passenger_gender', 'M')
    payment_method = request.form.get('payment_method', 'upi')

    if not all([schedule_id, selected_seats, passenger_name, passenger_email, passenger_phone]):
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('select_seats', schedule_id=schedule_id))

    schedule = Schedule.query.get_or_404(schedule_id)

    available = Seat.query.filter(
        Seat.schedule_id == schedule_id,
        Seat.seat_number.in_(selected_seats),
        Seat.is_booked == False,
    ).all()

    if len(available) != len(selected_seats):
        flash('Some seats are no longer available. Please try again.', 'danger')
        return redirect(url_for('select_seats', schedule_id=schedule_id))

    # Book seats
    for seat in available:
        seat.is_booked = True
        seat.gender = passenger_gender

    schedule.available_seats -= len(selected_seats)

    total = schedule.price * len(selected_seats)
    payment_status = 'paid' if payment_method == 'cash' else 'pending'

    booking = Booking(
        booking_id=generate_booking_id(),
        schedule_id=schedule_id,
        passenger_name=passenger_name,
        passenger_email=passenger_email,
        passenger_phone=passenger_phone,
        seat_numbers=','.join(selected_seats),
        total_amount=total,
        boarding_point=boarding_point,
        dropping_point=dropping_point,
        status='confirmed',
        payment_method=payment_method,
        payment_status=payment_status,
        user_id=session.get('user_id'),
    )
    db.session.add(booking)
    db.session.commit()

    # If UPI payment, redirect to payment page with QR
    if payment_method == 'upi':
        return redirect(url_for('payment_page', booking_id=booking.booking_id))

    return redirect(url_for('booking_confirmation', booking_id=booking.booking_id))


@app.route('/payment/<booking_id>')
def payment_page(booking_id):
    booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
    qr_base64 = generate_upi_qr(booking.total_amount, booking.booking_id)
    return render_template('payment.html', booking=booking, qr_code=qr_base64, upi_id=UPI_ID)


@app.route('/api/payment-confirm/<booking_id>', methods=['POST'])
def api_payment_confirm(booking_id):
    """Called after user scans QR and completes payment."""
    booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
    booking.payment_status = 'paid'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Payment confirmed'})


@app.route('/booking/<booking_id>')
def booking_confirmation(booking_id):
    booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
    qr_base64 = None
    if booking.payment_method == 'upi' and booking.payment_status == 'pending':
        qr_base64 = generate_upi_qr(booking.total_amount, booking.booking_id)
    return render_template('booking_confirmation.html', booking=booking, qr_code=qr_base64)


@app.route('/my-bookings', methods=['GET', 'POST'])
def my_bookings():
    bookings = []
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        if phone:
            bookings = Booking.query.filter_by(passenger_phone=phone).order_by(Booking.created_at.desc()).all()
        elif email:
            bookings = Booking.query.filter_by(passenger_email=email).order_by(Booking.created_at.desc()).all()
    elif 'user_id' in session:
        bookings = Booking.query.filter_by(user_id=session['user_id']).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/cancel-booking/<booking_id>')
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
    if booking.status != 'cancelled':
        seat_nums = booking.seat_numbers.split(',')
        seats = Seat.query.filter(
            Seat.schedule_id == booking.schedule_id,
            Seat.seat_number.in_(seat_nums),
        ).all()
        for seat in seats:
            seat.is_booked = False
            seat.gender = ''

        booking.schedule.available_seats += len(seats)
        booking.status = 'cancelled'
        db.session.commit()
        flash(f'Booking {booking_id} has been cancelled. Refund of ₹{booking.total_amount} will be processed.', 'info')
    return redirect(url_for('my_bookings'))


# ─── API endpoints ───────────────────────────────────────────────────────────

@app.route('/api/seats/<int:schedule_id>')
def api_seats(schedule_id):
    seats = Seat.query.filter_by(schedule_id=schedule_id).all()
    return jsonify([{
        'seat_number': s.seat_number,
        'is_booked': s.is_booked,
        'seat_type': s.seat_type,
        'gender': s.gender,
    } for s in seats])


@app.route('/api/check-seats', methods=['POST'])
def api_check_seats():
    data = request.get_json()
    schedule_id = data.get('schedule_id')
    seat_numbers = data.get('seats', [])
    seats = Seat.query.filter(
        Seat.schedule_id == schedule_id,
        Seat.seat_number.in_(seat_numbers),
    ).all()
    unavailable = [s.seat_number for s in seats if s.is_booked]
    return jsonify({'unavailable': unavailable})


# ─── Admin ───────────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin():
    buses = Bus.query.all()
    bookings = Booking.query.order_by(Booking.created_at.desc()).limit(50).all()
    total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
        Booking.status == 'confirmed'
    ).scalar() or 0
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='confirmed').count()
    paid_bookings = Booking.query.filter_by(payment_status='paid').count()
    schedules = Schedule.query.filter(Schedule.travel_date >= date.today()).order_by(Schedule.departure_time).limit(20).all()
    users = User.query.order_by(User.created_at.desc()).limit(20).all()
    return render_template('admin.html',
                           buses=buses,
                           bookings=bookings,
                           total_revenue=total_revenue,
                           total_bookings=total_bookings,
                           active_bookings=active_bookings,
                           paid_bookings=paid_bookings,
                           schedules=schedules,
                           users=users)


@app.route('/admin/add-bus', methods=['POST'])
@admin_required
def admin_add_bus():
    bus = Bus(
        bus_name=request.form['bus_name'],
        bus_type=request.form['bus_type'],
        total_seats=int(request.form['total_seats']),
        operator=request.form.get('operator', 'Ritesh Tours and Travels'),
        bus_number=request.form['bus_number'],
        amenities=request.form.get('amenities', ''),
    )
    db.session.add(bus)
    db.session.commit()
    flash(f'Bus {bus.bus_number} added successfully!', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/delete-bus/<int:bus_id>')
@admin_required
def admin_delete_bus(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    db.session.delete(bus)
    db.session.commit()
    flash(f'Bus {bus.bus_number} deleted.', 'info')
    return redirect(url_for('admin'))


@app.route('/admin/add-schedule', methods=['POST'])
@admin_required
def admin_add_schedule():
    bus = Bus.query.get_or_404(int(request.form['bus_id']))
    route = Route.query.first()
    d = date.fromisoformat(request.form['travel_date'])
    h, m = map(int, request.form['departure_time'].split(':'))
    dep = datetime(d.year, d.month, d.day, h, m)
    arr = dep + timedelta(hours=route.duration_hours)

    sched = Schedule(
        bus_id=bus.id,
        route_id=route.id,
        departure_time=dep,
        arrival_time=arr,
        price=float(request.form['price']),
        available_seats=bus.total_seats,
        travel_date=d,
        status='active',
    )
    db.session.add(sched)
    db.session.commit()
    create_seats_for_schedule(sched)
    flash(f'Schedule added for {bus.bus_name} on {d}', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/cancel-schedule/<int:schedule_id>')
@admin_required
def admin_cancel_schedule(schedule_id):
    sched = Schedule.query.get_or_404(schedule_id)
    sched.status = 'cancelled'
    for b in sched.bookings:
        if b.status == 'confirmed':
            b.status = 'cancelled'
    db.session.commit()
    flash('Schedule cancelled.', 'warning')
    return redirect(url_for('admin'))


@app.route('/admin/update-payment/<booking_id>', methods=['POST'])
@admin_required
def admin_update_payment(booking_id):
    booking = Booking.query.filter_by(booking_id=booking_id).first_or_404()
    new_status = request.form.get('payment_status', 'paid')
    booking.payment_status = new_status
    db.session.commit()
    flash(f'Payment status updated for {booking_id}', 'success')
    return redirect(url_for('admin'))


# ─── Init ────────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    seed_database()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
