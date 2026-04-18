from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from db import get_db_connection
from models import get_stations
import qrcode
import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

booking_bp = Blueprint('booking', __name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@booking_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        from_station = request.form.get('from_station', '')
        to_station = request.form.get('to_station', '')
        from_text = request.form.get('from_text', '')
        to_text = request.form.get('to_text', '')
        journey_date = request.form['journey_date']
        passengers_count = request.form['passengers_count']
        
        return redirect(url_for('booking.trains', 
                               from_id=from_station, 
                               to_id=to_station,
                               from_text=from_text,
                               to_text=to_text,
                               date=journey_date,
                               pax=passengers_count))
    
    stations = get_stations()
    return render_template('booking/search.html', stations=stations)

# ==================== MODIFIED: TRAINS ROUTE WITH FILTER & SORT ====================
@booking_bp.route('/trains')
@login_required
def trains():
    from_id = request.args.get('from_id', '')
    to_id = request.args.get('to_id', '')
    from_text = request.args.get('from_text', '')
    to_text = request.args.get('to_text', '')
    journey_date = request.args.get('date', '')
    passengers_count = int(request.args.get('pax', 1))
    
    # FILTER & SORT PARAMS (GET params)
    min_fare = request.args.get('min_fare', '', type=str)
    max_fare = request.args.get('max_fare', '', type=str)
    departure_from = request.args.get('departure_from', '', type=str)
    departure_to = request.args.get('departure_to', '', type=str)
    only_available = request.args.get('only_available', '', type=str)
    sort_by = request.args.get('sort_by', '', type=str)
    
    if not journey_date:
        flash('Please search for trains first', 'warning')
        return redirect(url_for('booking.search'))
    
    # Import functions
    from models import search_schedules, generate_random_schedules
    
    # Search in database
    schedules = search_schedules(from_id, to_id, from_text, to_text, journey_date, passengers_count)
    
    # If no results, generate random demo trains
    if not schedules:
        from_station_name = from_text if from_text else 'Unknown'
        to_station_name = to_text if to_text else 'Unknown'
        schedules = generate_random_schedules(from_station_name, to_station_name, journey_date, passengers_count, count=4)
    
    # ==================== APPLY FILTERS ====================
    try:
        # Filter by fare range
        if min_fare:
            min_fare_val = float(min_fare)
            schedules = [s for s in schedules if s.get('fare', 0) >= min_fare_val]
        
        if max_fare:
            max_fare_val = float(max_fare)
            schedules = [s for s in schedules if s.get('fare', 0) <= max_fare_val]
        
        # Filter by departure time range
        if departure_from:
            schedules = [s for s in schedules if s.get('departure_time', '') >= departure_from]
        
        if departure_to:
            schedules = [s for s in schedules if s.get('departure_time', '') <= departure_to]
        
        # Filter by available seats (only if checkbox is checked)
        if only_available == 'on' or only_available == 'true':
            schedules = [s for s in schedules if s.get('available_seats', 0) > 0]
    except (ValueError, TypeError):
        # Silently ignore invalid filter values
        pass
    
    # ==================== APPLY SORTING ====================
    try:
        if sort_by == 'fare_asc':
            schedules = sorted(schedules, key=lambda x: x.get('fare', 0))
        elif sort_by == 'fare_desc':
            schedules = sorted(schedules, key=lambda x: x.get('fare', 0), reverse=True)
        elif sort_by == 'depart_asc':
            schedules = sorted(schedules, key=lambda x: x.get('departure_time', ''))
        elif sort_by == 'depart_desc':
            schedules = sorted(schedules, key=lambda x: x.get('departure_time', ''), reverse=True)
    except (ValueError, TypeError, KeyError):
        # Silently ignore invalid sort values
        pass
    
    return render_template('booking/trains.html', 
                         schedules=schedules,
                         min_fare=min_fare,
                         max_fare=max_fare,
                         departure_from=departure_from,
                         departure_to=departure_to,
                         only_available=only_available,
                         sort_by=sort_by)

@booking_bp.route('/passengers/<schedule_id>', methods=['GET', 'POST'])
@login_required
def passengers(schedule_id):
    passengers_count = request.args.get('pax', 1, type=int)
    
    if request.method == 'POST':
        # Collect passenger data
        passenger_list = []
        for i in range(passengers_count):
            passenger = {
                'name': request.form[f'name_{i}'],
                'age': request.form[f'age_{i}'],
                'gender': request.form[f'gender_{i}']
            }
            passenger_list.append(passenger)
        
        # Get schedule details
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT s.*, r.fare, s.journey_date
                FROM schedules s
                JOIN routes r ON s.route_id = r.id
                WHERE s.id = %s
            """, (schedule_id,))
            schedule = cursor.fetchone()
            
            if schedule and schedule['available_seats'] >= passengers_count:
                # Generate PNR
                import random
                pnr = ''.join([str(random.randint(0, 9)) for _ in range(10)])
                
                # Calculate total fare
                total_fare = schedule['fare'] * passengers_count
                
                # Create booking with PENDING_ADMIN status
                cursor.execute("""
                    INSERT INTO bookings (user_id, schedule_id, pnr, journey_date, total_fare, status, booking_status, payment_status, payment_verified)
                    VALUES (%s, %s, %s, %s, %s, 'Pending', 'PENDING_ADMIN', 'UNPAID', 0)
                """, (session['user_id'], schedule_id, pnr, schedule['journey_date'], total_fare))
                
                booking_id = cursor.lastrowid
                
                # Add passengers
                for passenger in passenger_list:
                    cursor.execute("""
                        INSERT INTO passengers (booking_id, name, age, gender)
                        VALUES (%s, %s, %s, %s)
                    """, (booking_id, passenger['name'], passenger['age'], passenger['gender']))
                
                # Update available seats
                cursor.execute("""
                    UPDATE schedules SET available_seats = available_seats - %s
                    WHERE id = %s
                """, (passengers_count, schedule_id))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                flash('Request sent to admin. Waiting for approval.', 'info')
                return redirect(url_for('booking.my_bookings'))
            else:
                flash('Not enough seats available', 'danger')
                cursor.close()
                conn.close()
    
    return render_template('booking/passenger.html', pax_count=passengers_count)

@booking_bp.route('/ticket/<int:booking_id>')
@login_required
def ticket(booking_id):
    conn = get_db_connection()
    ticket_data = None
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get booking details
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                b.booking_status,
                t.train_no,
                t.train_name,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                s.departure_time,
                s.arrival_time
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.id = %s AND b.user_id = %s
        """, (booking_id, session['user_id']))
        
        ticket_data = cursor.fetchone()
        
        if ticket_data:
            # Only show ticket if CONFIRMED
            if ticket_data['booking_status'] != 'CONFIRMED':
                flash('Ticket not available. Booking must be confirmed first.', 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('booking.my_bookings'))
            
            # Get passengers
            cursor.execute("""
                SELECT name, age, gender FROM passengers WHERE booking_id = %s
            """, (booking_id,))
            ticket_data['passengers'] = cursor.fetchall()
            ticket_data['train'] = f"{ticket_data['train_no']} - {ticket_data['train_name']}"
            
            # Generate QR Code with complete ticket details
            passenger_names = ', '.join([p['name'] for p in ticket_data['passengers']])
            
            qr_data = f"""🎫 TICKET CONFIRMED SUCCESSFULLY! 🎫

PNR: {ticket_data['pnr']}
Status: {ticket_data['status']}

TRAIN DETAILS:
Train: {ticket_data['train']}
From: {ticket_data['from_station']}
To: {ticket_data['to_station']}
Date: {ticket_data['journey_date']}
Departure: {ticket_data['departure_time']}
Arrival: {ticket_data['arrival_time']}

PASSENGER(S):
{passenger_names}

Total Fare: ₹{ticket_data['total_fare']}

THANK YOU FOR BOOKING WITH US!"""
            
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            ticket_data['qr_code'] = f"data:image/png;base64,{img_str}"
        
        cursor.close()
        conn.close()
    
    if not ticket_data:
        flash('Ticket not found', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    return render_template('booking/ticket.html', ticket=ticket_data)

# ==================== MODIFIED: MY_BOOKINGS ROUTE WITH FILTER ====================
@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    conn = get_db_connection()
    bookings = []
    
    # FILTER PARAMS (GET params)
    search_query = request.args.get('search', '', type=str).strip()
    status_filter = request.args.get('status', '', type=str).strip()
    from_date = request.args.get('from_date', '', type=str).strip()
    to_date = request.args.get('to_date', '', type=str).strip()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get all bookings for this user
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                b.booking_status,
                b.payment_status,
                b.admin_note,
                b.refund_amount,
                b.refund_status,
                t.train_no,
                t.train_name,
                st1.station_name AS from_station,
                st2.station_name AS to_station
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.user_id = %s
            ORDER BY b.journey_date DESC
        """, (session['user_id'],))
        
        bookings = cursor.fetchall()
        cursor.close()
        conn.close()
    
    # ==================== APPLY FILTERS (Python-level) ====================
    try:
        # Search filter: PNR / Train No / Train Name / From / To
        if search_query:
            search_lower = search_query.lower()
            bookings = [
                b for b in bookings 
                if (search_lower in b['pnr'].lower() or
                    search_lower in str(b['train_no']).lower() or
                    search_lower in b['train_name'].lower() or
                    search_lower in b['from_station'].lower() or
                    search_lower in b['to_station'].lower())
            ]
        
        # Status filter
        if status_filter:
            if status_filter == 'Pending':
                bookings = [b for b in bookings if b['booking_status'] == 'PENDING_ADMIN']
            elif status_filter == 'Approved':
                bookings = [b for b in bookings if b['booking_status'] == 'APPROVED']
            elif status_filter == 'Paid':
                bookings = [b for b in bookings if b['payment_status'] == 'PAID']
            elif status_filter == 'Confirmed':
                bookings = [b for b in bookings if b['booking_status'] == 'CONFIRMED']
            elif status_filter == 'Cancelled':
                bookings = [b for b in bookings if b['status'] == 'Cancelled']
        
        # Date range filter
        if from_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            bookings = [b for b in bookings if datetime.strptime(b['journey_date'], '%Y-%m-%d').date() >= from_date_obj]
        
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            bookings = [b for b in bookings if datetime.strptime(b['journey_date'], '%Y-%m-%d').date() <= to_date_obj]
    
    except (ValueError, TypeError, KeyError):
        # Silently ignore invalid filter values
        pass
    
    return render_template('booking/my_bookings.html', 
                         bookings=bookings,
                         search_query=search_query,
                         status_filter=status_filter,
                         from_date=from_date,
                         to_date=to_date)

@booking_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    conn = get_db_connection()
    success = False
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get booking details
        cursor.execute("""
            SELECT b.id, b.user_id, b.schedule_id, b.status, b.total_fare
            FROM bookings b
            WHERE b.id = %s
        """, (booking_id,))
        
        booking = cursor.fetchone()
        
        if booking and booking['user_id'] == session['user_id'] and booking['status'] == 'Confirmed':
            # Get passenger count
            cursor.execute("SELECT COUNT(*) as count FROM passengers WHERE booking_id = %s", (booking_id,))
            result = cursor.fetchone()
            passenger_count = result['count'] if result else 0
            
            # Cancel booking and process refund
            cursor.execute("""
                UPDATE bookings 
                SET status = 'Cancelled', 
                    refund_amount = %s, 
                    refund_status = 'REFUNDED' 
                WHERE id = %s
            """, (booking['total_fare'], booking_id))
            
            # Restore seats
            cursor.execute("""
                UPDATE schedules SET available_seats = available_seats + %s
                WHERE id = %s
            """, (passenger_count, booking['schedule_id']))
            
            conn.commit()
            success = True
        
        cursor.close()
        conn.close()
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': success}), 200 if success else 400
    else:
        # Regular form submission - redirect as before
        if not success:
            flash('Booking not found or already cancelled', 'danger')
        return redirect(url_for('booking.my_bookings'))

# ==================== PAYMENT ROUTES ====================

@booking_bp.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    conn = get_db_connection()
    payment_data = None
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get booking details
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                b.booking_status,
                b.payment_status,
                t.train_no,
                t.train_name,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                s.departure_time,
                s.arrival_time
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.id = %s AND b.user_id = %s
        """, (booking_id, session['user_id']))
        
        payment_data = cursor.fetchone()
        
        if payment_data:
            # Check if payment is allowed
            if payment_data['booking_status'] != 'APPROVED':
                flash('Payment not allowed. Booking must be approved by admin first.', 'warning')
                cursor.close()
                conn.close()
                return redirect(url_for('booking.my_bookings'))
            
            if payment_data['payment_status'] != 'UNPAID':
                flash('Payment already completed for this booking.', 'info')
                cursor.close()
                conn.close()
                return redirect(url_for('booking.my_bookings'))
            
            # Get passengers
            cursor.execute("""
                SELECT name, age, gender FROM passengers WHERE booking_id = %s
            """, (booking_id,))
            payment_data['passengers'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
    
    if not payment_data:
        flash('Booking not found', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    return render_template('booking/payment.html', booking=payment_data)

@booking_bp.route('/payment/<int:booking_id>/pay', methods=['POST'])
@login_required
def process_payment(booking_id):
    entered_amount = request.form.get('amount', '').strip()
    
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get booking details
        cursor.execute("""
            SELECT 
                b.id,
                b.total_fare,
                b.booking_status,
                b.payment_status
            FROM bookings b
            WHERE b.id = %s AND b.user_id = %s
        """, (booking_id, session['user_id']))
        
        booking = cursor.fetchone()
        
        if not booking:
            flash('Booking not found', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('booking.my_bookings'))
        
        # Validate booking status
        if booking['booking_status'] != 'APPROVED':
            flash('Payment not allowed. Booking must be approved by admin first.', 'warning')
            cursor.close()
            conn.close()
            return redirect(url_for('booking.my_bookings'))
        
        if booking['payment_status'] != 'UNPAID':
            flash('Payment already completed for this booking.', 'info')
            cursor.close()
            conn.close()
            return redirect(url_for('booking.my_bookings'))
        
        # Validate amount
        try:
            entered_amount_float = float(entered_amount)
        except ValueError:
            flash('Invalid amount entered. Please enter a valid number.', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('booking.payment', booking_id=booking_id))
        
        if entered_amount_float != float(booking['total_fare']):
            flash(f'Amount mismatch. Enter exact amount: ₹{booking["total_fare"]}', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('booking.payment', booking_id=booking_id))
        
        # Generate fake transaction ID
        import random
        date_str = datetime.now().strftime('%Y%m%d')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        txn_id = f'FAKE-{date_str}-{random_digits}'
        
        # Update payment status
        cursor.execute("""
            UPDATE bookings 
            SET payment_status = 'PAID', txn_id = %s
            WHERE id = %s
        """, (txn_id, booking_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Payment successful! Transaction ID: {txn_id}. Waiting for admin verification.', 'success')
        return redirect(url_for('booking.payment_success', booking_id=booking_id, txn_id=txn_id))
    
    flash('Payment failed. Please try again.', 'danger')
    return redirect(url_for('booking.payment', booking_id=booking_id))

@booking_bp.route('/payment-success/<int:booking_id>')
@login_required
def payment_success(booking_id):
    txn_id = request.args.get('txn_id', '')
    
    conn = get_db_connection()
    booking_data = None
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.total_fare,
                b.txn_id,
                t.train_no,
                t.train_name,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                b.journey_date
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.id = %s AND b.user_id = %s
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        cursor.close()
        conn.close()
    
    if not booking_data:
        flash('Booking not found', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    return render_template('booking/payment_success.html', booking=booking_data, txn_id=txn_id)

# ==================== DOWNLOAD TICKET (PDF) ====================

@booking_bp.route('/ticket/<int:booking_id>/download')
@login_required
def download_ticket(booking_id):
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Get booking details
    cursor.execute("""
        SELECT b.*, t.train_no, t.train_name, 
               st1.station_name as from_station, 
               st2.station_name as to_station,
               s.departure_time, s.arrival_time
        FROM bookings b
        JOIN schedules s ON b.schedule_id = s.id
        JOIN routes r ON s.route_id = r.id
        JOIN trains t ON r.train_id = t.id
        JOIN stations st1 ON r.from_station_id = st1.id
        JOIN stations st2 ON r.to_station_id = st2.id
        WHERE b.id = %s AND b.user_id = %s
    """, (booking_id, session['user_id']))
    
    booking = cursor.fetchone()
    
    if not booking:
        flash('Ticket not found', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    # Get passengers
    cursor.execute("SELECT * FROM passengers WHERE booking_id = %s", (booking_id,))
    passengers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Create PDF
    from io import BytesIO
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # Header
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(200, 800, "🚂 RAILWAY TICKET")
    
    # PNR
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 750, f"PNR: {booking['pnr']}")
    pdf.drawString(400, 750, f"Status: {booking['status']}")
    
    # Train Details
    pdf.setFont("Helvetica", 12)
    y = 700
    pdf.drawString(50, y, f"Train: {booking['train_no']} - {booking['train_name']}")
    y -= 30
    pdf.drawString(50, y, f"From: {booking['from_station']}")
    pdf.drawString(300, y, f"Depart: {booking['departure_time']}")
    y -= 30
    pdf.drawString(50, y, f"To: {booking['to_station']}")
    pdf.drawString(300, y, f"Arrive: {booking['arrival_time']}")
    y -= 30
    pdf.drawString(50, y, f"Journey Date: {booking['journey_date']}")
    
    # Passengers
    y -= 50
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Passengers:")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for i, p in enumerate(passengers, 1):
        pdf.drawString(50, y, f"{i}. {p['name']} | Age: {p['age']} | Gender: {p['gender']}")
        y -= 20
    
    # Fare
    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, f"Total Fare: ₹{booking['total_fare']}")
    
    pdf.save()
    buffer.seek(0)
    
    from flask import send_file
    return send_file(buffer, as_attachment=True, download_name=f"ticket_{booking['pnr']}.pdf", mimetype='application/pdf')