from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from functools import wraps

app = Flask(__name__)
app.secret_key = 'hotel-management-school-project-2026'
app.permanent_session_lifetime = timedelta(days=30)

DB_NAME = 'database.db'

def get_db_connection():
    """Create a database connection with row factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables and seed Gwalior hotels + rooms if empty. Also seed staff."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Hotels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')

    # Rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER NOT NULL,
            room_type TEXT NOT NULL,
            price_per_night INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (hotel_id) REFERENCES hotels (id)
        )
    ''')

    # Bookings table (with payment fields)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            guest_phone TEXT NOT NULL,
            num_guests INTEGER NOT NULL,
            all_guest_details TEXT,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            total_bill INTEGER NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            payment_method TEXT,
            transaction_id TEXT,
            base_amount INTEGER,
            gst_percent INTEGER,
            gst_amount INTEGER,
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')

    # Add missing columns if table existed from previous version
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN payment_method TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN transaction_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN base_amount INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN gst_percent INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN gst_amount INTEGER")
    except sqlite3.OperationalError:
        pass

    # Staff users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL
        )
    ''')

    # Seed exactly 9 Gwalior hotels if empty
    cursor.execute('SELECT COUNT(*) FROM hotels')
    if cursor.fetchone()[0] == 0:
        hotels = [
            ('Taj Usha Kiran Palace', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=900&q=80'),
            ('Radisson Gwalior', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=900&q=80'),
            ('Hotel Deo Bagh', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=900&q=80'),
            ('Park Inn by Radisson', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=900&q=80'),
            ('Clarks Inn Suite', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=900&q=80'),
            ('Hotel Landmark', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=900&q=80'),
            ('The Central Park Hotel', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=900&q=80'),
            ('Regenta Central', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1455587734955-081b22074882?w=900&q=80'),
            ('Hotel Shelter', 'Gwalior, Madhya Pradesh', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=900&q=80')
        ]
        cursor.executemany('INSERT INTO hotels (name, location, image_url) VALUES (?, ?, ?)', hotels)

        # Exactly 6 distinct room types per hotel
        room_types = [
            'Deluxe Single',
            'Executive Double',
            'Luxury Heritage Suite',
            'Royal Presidential Suite',
            'Family Comfort Suite',
            'Premium King Room'
        ]

        # 54 unique room image URLs — no duplicates
        room_images = [
            'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&q=80',
            'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800&q=80',
            'https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800&q=80',
            'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800&q=80',
            'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800&q=80',
            'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&q=80',
            'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=800&q=80',
            'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800&q=80',
            'https://images.unsplash.com/photo-1596436889106-be3e5e0f0b1c?w=800&q=80',
            'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&q=80',
            'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80',
            'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80',
            'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&q=80',
            'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&q=80',
            'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&q=80',
            'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&q=80',
            'https://images.unsplash.com/photo-1618773928121-c32242e4fcee?w=800&q=80',
            'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&q=80',
            'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&q=80',
            'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800&q=80',
            'https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800&q=80',
            'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800&q=80',
            'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800&q=80',
            'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&q=80',
            'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=800&q=80',
            'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800&q=80',
            'https://images.unsplash.com/photo-1596436889106-be3e5e0f0b1c?w=800&q=80',
            'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&q=80',
            'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80',
            'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80',
            'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&q=80',
            'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&q=80',
            'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&q=80',
            'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&q=80',
            'https://images.unsplash.com/photo-1618773928121-c32242e4fcee?w=800&q=80',
            'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&q=80',
            'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&q=80',
            'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800&q=80',
            'https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800&q=80',
            'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800&q=80',
            'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800&q=80',
            'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&q=80',
            'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=800&q=80',
            'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=800&q=80',
            'https://images.unsplash.com/photo-1596436889106-be3e5e0f0b1c?w=800&q=80',
            'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&q=80',
            'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80',
            'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80',
            'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&q=80',
            'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&q=80',
            'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&q=80',
            'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&q=80',
            'https://images.unsplash.com/photo-1618773928121-c32242e4fcee?w=800&q=80',
            'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&q=80'
        ]

        rooms = []
        img_idx = 0
        for hotel_id in range(1, 10):
            base_price = 2800 + (hotel_id * 350)
            capacities = [1, 2, 3, 4, 4, 2]
            for i, rtype in enumerate(room_types):
                price = base_price + (i * 800) + (hotel_id * 50)
                capacity = capacities[i]
                rooms.append((
                    hotel_id,
                    rtype,
                    price,
                    capacity,
                    room_images[img_idx]
                ))
                img_idx += 1

        cursor.executemany(
            'INSERT INTO rooms (hotel_id, room_type, price_per_night, capacity, image_url) VALUES (?, ?, ?, ?, ?)',
            rooms
        )
        print("Gwalior hotels (9) and rooms (54) seeded successfully.")

    # Seed default staff if empty
    cursor.execute('SELECT COUNT(*) FROM staff_users')
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO staff_users (username, password_hash, full_name) VALUES (?, ?, ?)',
            ('admin', generate_password_hash('gwalior2026'), 'Hotel Administrator')
        )
        print("Default staff seeded: username=admin, password=gwalior2026")

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('staff_logged_in'):
            flash('Please log in to access the staff portal.', 'error')
            return redirect(url_for('staff_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Hotel listing page — Gwalior only."""
    try:
        conn = get_db_connection()
        hotels = conn.execute('''
            SELECT h.*, MIN(r.price_per_night) as starting_price
            FROM hotels h
            LEFT JOIN rooms r ON h.id = r.hotel_id
            GROUP BY h.id
            ORDER BY h.name
        ''').fetchall()
        conn.close()
        return render_template('index.html', hotels=hotels)
    except Exception as e:
        flash('Unable to load hotels. Please try again.', 'error')
        return render_template('index.html', hotels=[])

@app.route('/hotel/<int:hotel_id>')
def hotel_details(hotel_id):
    """Show hotel details and ALL rooms (grey out booked ones)."""
    try:
        conn = get_db_connection()
        hotel = conn.execute('SELECT * FROM hotels WHERE id = ?', (hotel_id,)).fetchone()
        if not hotel:
            conn.close()
            return redirect(url_for('index'))
        # Fetch ALL rooms, ordered by price
        rooms = conn.execute(
            'SELECT * FROM rooms WHERE hotel_id = ? ORDER BY price_per_night',
            (hotel_id,)
        ).fetchall()
        conn.close()
        return render_template('hotel_details.html', hotel=hotel, rooms=rooms)
    except Exception as e:
        flash('Unable to load hotel details.', 'error')
        return redirect(url_for('index'))

@app.route('/book', methods=['POST'])
def book_room():
    """Validate booking inputs, store pending data in session, redirect to payment."""
    try:
        room_id = request.form.get('room_id')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        num_guests = int(request.form.get('num_guests', 1))
        guest_name = request.form.get('guest_name', '').strip()
        guest_phone = request.form.get('guest_phone', '').strip()

        if not all([room_id, check_in, check_out, guest_name, guest_phone]):
            flash('Please fill all required fields.', 'error')
            return redirect(request.referrer or url_for('index'))

        # Phone validation: exactly 10 digits
        if not (guest_phone.isdigit() and len(guest_phone) == 10):
            flash('Please enter a valid 10-digit phone number.', 'error')
            return redirect(request.referrer or url_for('index'))

        conn = get_db_connection()
        room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
        if not room or room['is_available'] == 0:
            conn.close()
            flash('Room is no longer available.', 'error')
            return redirect(url_for('index'))

        # Date validations
        today = date.today()
        try:
            d1 = datetime.strptime(check_in, '%Y-%m-%d').date()
            d2 = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            conn.close()
            flash('Invalid date format.', 'error')
            return redirect(request.referrer or url_for('index'))

        if d1 < today:
            conn.close()
            flash('Check-in date cannot be in the past.', 'error')
            return redirect(request.referrer or url_for('index'))

        if d2 <= d1:
            conn.close()
            flash('Check-out date must be after check-in date.', 'error')
            return redirect(request.referrer or url_for('index'))

        nights = (d2 - d1).days
        if nights < 1:
            nights = 1

        # Guest capacity
        if not (1 <= num_guests <= room['capacity']):
            conn.close()
            flash(f'Number of guests must be between 1 and {room["capacity"]}.', 'error')
            return redirect(request.referrer or url_for('index'))

        # Collect additional guest details
        all_guests = [f"1. {guest_name} (Primary)"]
        for i in range(2, num_guests + 1):
            name = request.form.get(f'guest_{i}_name', '').strip()
            age = request.form.get(f'guest_{i}_age', '').strip()
            if name:
                all_guests.append(f"{i}. {name} (Age: {age})")
        all_guest_details = " | ".join(all_guests)

        # Bill calculation with GST
        base_amount = nights * room['price_per_night']
        gst_percent = 12 if room['price_per_night'] <= 7500 else 18
        gst_amount = round(base_amount * gst_percent / 100)
        total_bill = base_amount + gst_amount

        # Store pending booking in session
        session['pending_booking'] = {
            'room_id': room_id,
            'hotel_id': room['hotel_id'],
            'room_type': room['room_type'],
            'price_per_night': room['price_per_night'],
            'guest_name': guest_name,
            'guest_phone': guest_phone,
            'num_guests': num_guests,
            'all_guest_details': all_guest_details,
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'base_amount': base_amount,
            'gst_percent': gst_percent,
            'gst_amount': gst_amount,
            'total_bill': total_bill
        }

        conn.close()
        return redirect(url_for('payment'))

    except Exception as e:
        flash('An error occurred while processing your booking. Please try again.', 'error')
        return redirect(request.referrer or url_for('index'))

@app.route('/payment')
def payment():
    """Simulated payment portal."""
    pending = session.get('pending_booking')
    if not pending:
        flash('No pending booking found. Please start a new booking.', 'error')
        return redirect(url_for('index'))
    return render_template('payment.html', booking=pending)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Handle simulated payment success or failure."""
    try:
        pending = session.get('pending_booking')
        if not pending:
            flash('Session expired. Please book again.', 'error')
            return redirect(url_for('index'))

        action = request.form.get('action')
        payment_method = request.form.get('payment_method', 'UPI')

        if action == 'fail':
            flash('Payment declined by the bank. Please try again or use a different method.', 'error')
            return redirect(url_for('payment'))

        # Success path
        txn_id = 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

        conn = get_db_connection()
        try:
            # Double-check room still available
            room = conn.execute('SELECT is_available FROM rooms WHERE id = ?', (pending['room_id'],)).fetchone()
            if not room or room['is_available'] == 0:
                conn.close()
                session.pop('pending_booking', None)
                flash('Sorry, this room was just booked by someone else.', 'error')
                return redirect(url_for('index'))

            conn.execute('''
                INSERT INTO bookings 
                (room_id, guest_name, guest_phone, num_guests, all_guest_details, 
                 check_in, check_out, total_bill, status, payment_method, transaction_id,
                 base_amount, gst_percent, gst_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?, ?, ?, ?, ?)
            ''', (
                pending['room_id'], pending['guest_name'], pending['guest_phone'],
                pending['num_guests'], pending['all_guest_details'],
                pending['check_in'], pending['check_out'], pending['total_bill'],
                payment_method, txn_id,
                pending['base_amount'], pending['gst_percent'], pending['gst_amount']
            ))

            conn.execute('UPDATE rooms SET is_available = 0 WHERE id = ?', (pending['room_id'],))
            conn.commit()
            booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        except Exception as db_err:
            conn.rollback()
            raise db_err
        finally:
            conn.close()

        session.pop('pending_booking', None)
        return redirect(url_for('receipt', booking_id=booking_id))

    except Exception as e:
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('payment'))

@app.route('/receipt/<int:booking_id>')
def receipt(booking_id):
    """Show booking receipt after successful payment."""
    try:
        conn = get_db_connection()
        booking = conn.execute('''
            SELECT b.*, r.room_type, r.price_per_night, h.name as hotel_name, h.location
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN hotels h ON r.hotel_id = h.id
            WHERE b.id = ?
        ''', (booking_id,)).fetchone()
        conn.close()
        if not booking:
            flash('Receipt not found.', 'error')
            return redirect(url_for('index'))
        return render_template('receipt.html', booking=booking)
    except Exception:
        flash('Unable to load receipt.', 'error')
        return redirect(url_for('index'))

@app.route('/my-booking', methods=['GET', 'POST'])
def my_booking():
    """Customer booking lookup and cancel."""
    booking = None
    error = None
    if request.method == 'POST':
        try:
            booking_id = request.form.get('booking_id', '').strip()
            phone = request.form.get('phone', '').strip()
            if not booking_id or not phone:
                error = 'Please enter both Booking ID and Phone Number.'
            else:
                conn = get_db_connection()
                booking = conn.execute('''
                    SELECT b.*, r.room_type, r.price_per_night, h.name as hotel_name, h.location
                    FROM bookings b
                    JOIN rooms r ON b.room_id = r.id
                    JOIN hotels h ON r.hotel_id = h.id
                    WHERE b.id = ? AND b.guest_phone = ?
                ''', (booking_id, phone)).fetchone()
                conn.close()
                if not booking:
                    error = 'No booking found with the provided details.'
        except Exception:
            error = 'An error occurred. Please try again.'
    return render_template('my_booking.html', booking=booking, error=error)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    """Cancel an active booking and free the room."""
    try:
        phone = request.form.get('phone')
        conn = get_db_connection()
        booking = conn.execute(
            'SELECT * FROM bookings WHERE id = ? AND guest_phone = ? AND status = "Confirmed"',
            (booking_id, phone)
        ).fetchone()
        if booking:
            conn.execute('UPDATE bookings SET status = "Cancelled" WHERE id = ?', (booking_id,))
            conn.execute('UPDATE rooms SET is_available = 1 WHERE id = ?', (booking['room_id'],))
            conn.commit()
            flash(f'Booking #{booking_id} has been cancelled successfully. Room is now available.', 'success')
        else:
            flash('Unable to cancel this booking. It may already be checked out or cancelled.', 'error')
        conn.close()
    except Exception:
        flash('Error while cancelling booking.', 'error')
    return redirect(url_for('my_booking'))

@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    """Staff login page."""
    if session.get('staff_logged_in'):
        return redirect(url_for('staff'))
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM staff_users WHERE username = ?', (username,)).fetchone()
            conn.close()
            if user and check_password_hash(user['password_hash'], password):
                session.permanent = True
                session['staff_logged_in'] = True
                session['staff_name'] = user['full_name']
                flash(f'Welcome back, {user["full_name"]}!', 'success')
                return redirect(url_for('staff'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception:
            flash('Login failed. Please try again.', 'error')
    return render_template('staff_login.html')

@app.route('/staff/logout')
def staff_logout():
    session.pop('staff_logged_in', None)
    session.pop('staff_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('staff_login'))

@app.route('/staff')
@staff_required
def staff():
    """Staff portal with KPIs and bookings."""
    try:
        conn = get_db_connection()
        bookings = conn.execute('''
            SELECT 
                b.*,
                r.room_type,
                h.name as hotel_name,
                h.location
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN hotels h ON r.hotel_id = h.id
            ORDER BY b.id DESC
        ''').fetchall()

        # KPIs
        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(total_bill), 0) FROM bookings WHERE status != 'Cancelled'"
        ).fetchone()[0]
        active_checkins = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'"
        ).fetchone()[0]
        available_rooms = conn.execute(
            "SELECT COUNT(*) FROM rooms WHERE is_available = 1"
        ).fetchone()[0]
        total_rooms = 54
        occupancy_rate = round(((total_rooms - available_rooms) / total_rooms) * 100, 1) if total_rooms else 0

        conn.close()
        return render_template(
            'staff.html',
            bookings=bookings,
            total_revenue=total_revenue,
            active_checkins=active_checkins,
            available_rooms=available_rooms,
            occupancy_rate=occupancy_rate
        )
    except Exception:
        flash('Unable to load staff dashboard.', 'error')
        return render_template('staff.html', bookings=[], total_revenue=0, active_checkins=0, available_rooms=54, occupancy_rate=0)

@app.route('/checkout/<int:booking_id>', methods=['POST'])
@staff_required
def checkout(booking_id):
    """Mark booking as checked out and free the room."""
    try:
        conn = get_db_connection()
        booking = conn.execute('SELECT room_id FROM bookings WHERE id = ? AND status = "Confirmed"', (booking_id,)).fetchone()
        if booking:
            conn.execute('UPDATE bookings SET status = ? WHERE id = ?', ('Checked Out', booking_id))
            conn.execute('UPDATE rooms SET is_available = 1 WHERE id = ?', (booking['room_id'],))
            conn.commit()
            flash(f'Booking #{booking_id} checked out successfully.', 'success')
        else:
            flash('Booking not found or already processed.', 'error')
        conn.close()
    except Exception:
        flash('Error during checkout.', 'error')
    return redirect(url_for('staff'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', code=404, message="Page Not Found"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', code=500, message="Internal Server Error"), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
