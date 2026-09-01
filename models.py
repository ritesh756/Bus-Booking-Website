from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()


class Bus(db.Model):
    __tablename__ = 'buses'
    id = db.Column(db.Integer, primary_key=True)
    bus_name = db.Column(db.String(100), nullable=False)
    bus_type = db.Column(db.String(50), nullable=False)  # AC, Non-AC, Sleeper, Semi-Sleeper
    total_seats = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.String(200), default='')
    operator = db.Column(db.String(100), nullable=False)
    bus_number = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    schedules = db.relationship('Schedule', backref='bus', lazy=True, cascade='all, delete-orphan')


class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float, default=0)
    duration_hours = db.Column(db.Float, default=0)

    schedules = db.relationship('Schedule', backref='route', lazy=True, cascade='all, delete-orphan')


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, cancelled, completed

    seats = db.relationship('Seat', backref='schedule', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='schedule', lazy=True, cascade='all, delete-orphan')


class Seat(db.Model):
    __tablename__ = 'seats'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    seat_type = db.Column(db.String(20), default='seater')  # seater, sleeper, window, aisle
    is_booked = db.Column(db.Boolean, default=False)
    gender = db.Column(db.String(10), default='')  # M, F

    __table_args__ = (db.UniqueConstraint('schedule_id', 'seat_number'),)


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True, nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_email = db.Column(db.String(100), nullable=False)
    passenger_phone = db.Column(db.String(15), nullable=False)
    seat_numbers = db.Column(db.String(200), nullable=False)  # comma separated
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, completed
    boarding_point = db.Column(db.String(200), default='')
    dropping_point = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), default='cash')
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BoardingPoint(db.Model):
    __tablename__ = 'boarding_points'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    time_offset_min = db.Column(db.Integer, default=0)  # minutes from departure

    route = db.relationship('Route', backref='boarding_points')
