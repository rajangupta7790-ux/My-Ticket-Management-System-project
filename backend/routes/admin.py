from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from functools import wraps
from db import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==================== ADMIN LOGIN CREDENTIALS ====================
# CHANGE THESE TO YOUR DESIRED USERNAME AND PASSWORD
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ==================== ADMIN LOGIN ROUTE ====================
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    # If already logged in as admin, redirect to dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')
    
    return render_template('admin/login.html')

# ==================== ADMIN LOGOUT ROUTE ====================
@admin_bp.route('/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('admin.admin_login'))

# ==================== MODIFIED ADMIN REQUIRED DECORATOR ====================
# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # OLD CODE (COMMENTED OUT - User-based admin check)
        # if 'user_id' not in session:
        #     flash('Please login to continue', 'warning')
        #     return redirect(url_for('auth.login'))
        # if not session.get('is_admin'):
        #     flash('Access denied. Admin only.', 'danger')
        #     return redirect(url_for('booking.search'))
        
        # NEW CODE - Check if admin is logged in via /admin/login
        if not session.get('admin_logged_in'):
            flash('Please login as admin to continue', 'warning')
            return redirect(url_for('admin.admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    conn = get_db_connection()
    stats = {}
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get total stations
        cursor.execute("SELECT COUNT(*) as count FROM stations")
        stats['stations'] = cursor.fetchone()['count']
        
        # Get total trains
        cursor.execute("SELECT COUNT(*) as count FROM trains")
        stats['trains'] = cursor.fetchone()['count']
        
        # Get total routes
        cursor.execute("SELECT COUNT(*) as count FROM routes")
        stats['routes'] = cursor.fetchone()['count']
        
        # Get total bookings
        cursor.execute("SELECT COUNT(*) as count FROM bookings")
        stats['bookings'] = cursor.fetchone()['count']
        
        # Get total revenue (Confirmed bookings minus refunds)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN status = 'Confirmed' THEN total_fare ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN status = 'Cancelled' AND refund_status = 'REFUNDED' THEN refund_amount ELSE 0 END), 0) 
                as revenue 
            FROM bookings
        """)
        stats['revenue'] = cursor.fetchone()['revenue']
        
        cursor.close()
        conn.close()
    
    return render_template('admin/dashboard.html', stats=stats)

# ==================== STATIONS MANAGEMENT ====================

@admin_bp.route('/stations')
@admin_required
def stations():
    # Get search query from GET params
    search_query = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    stations = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM stations ORDER BY station_name")
        all_stations = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Filter stations based on search query (Python level)
        if search_query:
            search_lower = search_query.lower()
            stations = [
                s for s in all_stations 
                if search_lower in s['station_name'].lower() or search_lower in s['station_code'].lower()
            ]
        else:
            stations = all_stations
    
    return render_template('admin/stations.html', stations=stations)

@admin_bp.route('/stations/add', methods=['POST'])
@admin_required
def add_station():
    station_name = request.form['station_name'].strip().title()
    station_code = request.form['station_code'].strip().upper()
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO stations (station_name, station_code) VALUES (%s, %s)",
                (station_name, station_code)
            )
            conn.commit()
            flash('Station added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding station: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.stations'))

@admin_bp.route('/stations/delete/<int:station_id>', methods=['POST'])
@admin_required
def delete_station(station_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM stations WHERE id = %s", (station_id,))
            conn.commit()
            flash('Station deleted successfully!', 'success')
        except Exception as e:
            flash(f'Cannot delete station: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.stations'))

@admin_bp.route('/stations/delete-selected', methods=['POST'])
@admin_required
def delete_selected_stations():
    selected_ids = request.json.get('ids', [])
    
    if not selected_ids:
        return {'success': False, 'message': 'No stations selected'}, 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            deleted_count = 0
            for station_id in selected_ids:
                cursor.execute("DELETE FROM stations WHERE id = %s", (station_id,))
                deleted_count += cursor.rowcount
            
            conn.commit()
            flash(f'{deleted_count} station(s) deleted successfully!', 'success')
            return {'success': True, 'message': f'{deleted_count} station(s) deleted'}
        except Exception as e:
            flash(f'Error deleting stations: {str(e)}', 'danger')
            return {'success': False, 'message': str(e)}, 500
        finally:
            cursor.close()
            conn.close()
    
    return {'success': False, 'message': 'Database connection failed'}, 500

# ==================== TRAINS MANAGEMENT ====================

@admin_bp.route('/trains')
@admin_required
def trains():
    # Get search query from GET params
    search_query = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    trains = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM trains ORDER BY train_no")
        all_trains = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Filter trains based on search query (Python level)
        if search_query:
            search_lower = search_query.lower()
            trains = [
                t for t in all_trains 
                if search_lower in str(t['train_no']) or search_lower in t['train_name'].lower()
            ]
        else:
            trains = all_trains
    
    return render_template('admin/trains.html', trains=trains)

@admin_bp.route('/trains/add', methods=['POST'])
@admin_required
def add_train():
    train_no = request.form['train_no']
    train_name = request.form['train_name'].strip().title()
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO trains (train_no, train_name) VALUES (%s, %s)",
                (train_no, train_name)
            )
            conn.commit()
            flash('Train added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding train: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.trains'))

@admin_bp.route('/trains/delete/<int:train_id>', methods=['POST'])
@admin_required
def delete_train(train_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM trains WHERE id = %s", (train_id,))
            conn.commit()
            flash('Train deleted successfully!', 'success')
        except Exception as e:
            flash(f'Cannot delete train: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.trains'))

@admin_bp.route('/trains/delete-selected', methods=['POST'])
@admin_required
def delete_selected_trains():
    selected_ids = request.json.get('ids', [])
    
    if not selected_ids:
        return {'success': False, 'message': 'No trains selected'}, 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            deleted_count = 0
            for train_id in selected_ids:
                cursor.execute("DELETE FROM trains WHERE id = %s", (train_id,))
                deleted_count += cursor.rowcount
            
            conn.commit()
            flash(f'{deleted_count} train(s) deleted successfully!', 'success')
            return {'success': True, 'message': f'{deleted_count} train(s) deleted'}
        except Exception as e:
            flash(f'Error deleting trains: {str(e)}', 'danger')
            return {'success': False, 'message': str(e)}, 500
        finally:
            cursor.close()
            conn.close()
    
    return {'success': False, 'message': 'Database connection failed'}, 500

# ==================== ROUTES MANAGEMENT ====================

@admin_bp.route('/routes')
@admin_required
def routes():
    # Get search query from GET params
    search_query = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    all_routes = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                r.id,
                r.train_id,
                r.from_station_id,
                r.to_station_id,
                r.distance,
                r.fare,
                t.train_no,
                t.train_name,
                s1.station_name AS from_station,
                s2.station_name AS to_station
            FROM routes r
            JOIN trains t ON r.train_id = t.id
            JOIN stations s1 ON r.from_station_id = s1.id
            JOIN stations s2 ON r.to_station_id = s2.id
            ORDER BY t.train_no
        """)
        all_routes = cursor.fetchall()
        cursor.close()
        conn.close()
    
    # Filter routes based on search query (Python level)
    if search_query:
        search_lower = search_query.lower()
        routes = [
            route for route in all_routes 
            if search_lower in str(route['train_no']) or 
               search_lower in route['train_name'].lower() or
               search_lower in route['from_station'].lower() or
               search_lower in route['to_station'].lower()
        ]
    else:
        routes = all_routes
    
    # Get trains and stations for the form
    trains = []
    stations = []
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM trains ORDER BY train_no")
        trains = cursor.fetchall()
        cursor.execute("SELECT * FROM stations ORDER BY station_name")
        stations = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/routes.html', routes=routes, trains=trains, stations=stations)

@admin_bp.route('/routes/add', methods=['POST'])
@admin_required
def add_route():
    train_id = request.form['train_id']
    from_station_id = request.form['from_station_id']
    to_station_id = request.form['to_station_id']
    distance = request.form['distance']
    base_fare = request.form['base_fare']
    
    if from_station_id == to_station_id:
        flash('From and To stations cannot be the same!', 'danger')
        return redirect(url_for('admin.routes'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO routes (train_id, from_station_id, to_station_id, distance, fare) VALUES (%s, %s, %s, %s, %s)",
                (train_id, from_station_id, to_station_id, distance, base_fare)
            )
            conn.commit()
            flash('Route added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding route: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.routes'))

@admin_bp.route('/routes/delete/<int:route_id>', methods=['POST'])
@admin_required
def delete_route(route_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM routes WHERE id = %s", (route_id,))
            conn.commit()
            flash('Route deleted successfully!', 'success')
        except Exception as e:
            flash(f'Cannot delete route: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.routes'))

@admin_bp.route('/routes/delete-selected', methods=['POST'])
@admin_required
def delete_selected_routes():
    selected_ids = request.json.get('ids', [])
    
    if not selected_ids:
        return {'success': False, 'message': 'No routes selected'}, 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            deleted_count = 0
            for route_id in selected_ids:
                cursor.execute("DELETE FROM routes WHERE id = %s", (route_id,))
                deleted_count += cursor.rowcount
            
            conn.commit()
            flash(f'{deleted_count} route(s) deleted successfully!', 'success')
            return {'success': True, 'message': f'{deleted_count} route(s) deleted'}
        except Exception as e:
            flash(f'Error deleting routes: {str(e)}', 'danger')
            return {'success': False, 'message': str(e)}, 500
        finally:
            cursor.close()
            conn.close()
    
    return {'success': False, 'message': 'Database connection failed'}, 500

# ==================== SCHEDULES MANAGEMENT ====================

@admin_bp.route('/schedules')
@admin_required
def schedules():
    # Get search query from GET params
    search_query = request.args.get('q', '').strip()
    
    conn = get_db_connection()
    all_schedules = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                s.id,
                s.route_id,
                s.journey_date,
                s.departure_time,
                s.arrival_time,
                s.available_seats,
                r.id as route_id,
                t.train_no,
                t.train_name,
                st1.station_name AS from_station,
                st2.station_name AS to_station
            FROM schedules s
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            ORDER BY s.journey_date DESC
        """)
        all_schedules = cursor.fetchall()
        cursor.close()
        conn.close()
    
    # Filter schedules based on search query (Python level)
    if search_query:
        search_lower = search_query.lower()
        schedules = [
            schedule for schedule in all_schedules 
            if search_lower in str(schedule['train_no']) or 
               search_lower in schedule['train_name'].lower() or
               search_lower in schedule['from_station'].lower() or
               search_lower in schedule['to_station'].lower()
        ]
    else:
        schedules = all_schedules
    
    # Get routes for the form
    routes = []
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                r.id,
                t.train_no,
                t.train_name,
                s1.station_name AS from_station,
                s2.station_name AS to_station
            FROM routes r
            JOIN trains t ON r.train_id = t.id
            JOIN stations s1 ON r.from_station_id = s1.id
            JOIN stations s2 ON r.to_station_id = s2.id
            ORDER BY t.train_no
        """)
        routes = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/schedules.html', schedules=schedules, routes=routes)

@admin_bp.route('/schedules/add', methods=['POST'])
@admin_required
def add_schedule():
    route_id = request.form['route_id']
    journey_date = request.form['journey_date']
    departure_time = request.form['departure_time']
    arrival_time = request.form['arrival_time']
    available_seats = request.form['available_seats']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO schedules (route_id, journey_date, departure_time, arrival_time, available_seats) VALUES (%s, %s, %s, %s, %s)",
                (route_id, journey_date, departure_time, arrival_time, available_seats)
            )
            conn.commit()
            flash('Schedule added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding schedule: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.schedules'))

@admin_bp.route('/schedules/delete/<int:schedule_id>', methods=['POST'])
@admin_required
def delete_schedule(schedule_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
            conn.commit()
            flash('Schedule deleted successfully!', 'success')
        except Exception as e:
            flash(f'Cannot delete schedule: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.schedules'))

@admin_bp.route('/schedules/delete-selected', methods=['POST'])
@admin_required
def delete_selected_schedules():
    selected_ids = request.json.get('ids', [])
    
    if not selected_ids:
        return {'success': False, 'message': 'No schedules selected'}, 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            deleted_count = 0
            for schedule_id in selected_ids:
                cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
                deleted_count += cursor.rowcount
            
            conn.commit()
            flash(f'{deleted_count} schedule(s) deleted successfully!', 'success')
            return {'success': True, 'message': f'{deleted_count} schedule(s) deleted'}
        except Exception as e:
            flash(f'Error deleting schedules: {str(e)}', 'danger')
            return {'success': False, 'message': str(e)}, 500
        finally:
            cursor.close()
            conn.close()
    
    return {'success': False, 'message': 'Database connection failed'}, 500

# ==================== BOOKINGS MANAGEMENT ====================

@admin_bp.route('/bookings')
@admin_required
def bookings():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    conn = get_db_connection()
    all_bookings = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                b.booking_status,
                b.payment_status,
                b.payment_verified,
                b.refund_status,
                b.refund_amount,
                b.created_at,
                u.name AS user_name,
                u.email AS user_email,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                t.train_no,
                t.train_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            ORDER BY b.created_at DESC
        """)
        all_bookings = cursor.fetchall()
        cursor.close()
        conn.close()
    
    # Filter bookings based on status
    if status_filter and status_filter != "All":
        if status_filter == "Pending":
            # Pending means booking_status == "PENDING_ADMIN"
            all_bookings = [
                b for b in all_bookings 
                if b.get('booking_status') == 'PENDING_ADMIN'
            ]
        elif status_filter == "Confirmed":
            all_bookings = [
                b for b in all_bookings 
                if b.get('status') == 'Confirmed'
            ]
        elif status_filter == "Cancelled":
            all_bookings = [
                b for b in all_bookings 
                if b.get('status') == 'Cancelled'
            ]
    
    # Filter bookings based on search query
    if search_query:
        search_lower = search_query.lower()
        bookings = [
            booking for booking in all_bookings 
            if search_lower in booking['pnr'].lower() or 
               search_lower in booking['user_name'].lower() or
               search_lower in booking['user_email'].lower() or
               search_lower in str(booking['train_no'])
        ]
    else:
        bookings = all_bookings
    
    return render_template('admin/bookings.html', bookings=bookings)

@admin_bp.route('/bookings/<int:booking_id>')
@admin_required
def booking_details(booking_id):
    conn = get_db_connection()
    booking = None
    passengers = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get booking details
        cursor.execute("""
            SELECT 
                b.*,
                u.name AS user_name,
                u.email AS user_email,
                u.phone AS user_phone,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                t.train_no,
                t.train_name,
                s.departure_time,
                s.arrival_time
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.id = %s
        """, (booking_id,))
        booking = cursor.fetchone()
        
        # Get passengers
        cursor.execute("SELECT * FROM passengers WHERE booking_id = %s", (booking_id,))
        passengers = cursor.fetchall()
        
        cursor.close()
        conn.close()
    
    if not booking:
        flash('Booking not found!', 'danger')
        return redirect(url_for('admin.bookings'))
    
    return render_template('admin/booking_details.html', booking=booking, passengers=passengers)

@admin_bp.route('/bookings/delete/<int:booking_id>', methods=['POST'])
@admin_required
def delete_booking(booking_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Delete passengers first (foreign key constraint)
            cursor.execute("DELETE FROM passengers WHERE booking_id = %s", (booking_id,))
            
            # Delete payment records if any
            cursor.execute("DELETE FROM payments WHERE booking_id = %s", (booking_id,))
            
            # Delete booking
            cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
            conn.commit()
            flash('Booking deleted successfully!', 'success')
        except Exception as e:
            flash(f'Cannot delete booking: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.bookings'))

@admin_bp.route('/bookings/delete-selected', methods=['POST'])
@admin_required
def delete_selected_bookings():
    selected_ids = request.json.get('ids', [])
    
    if not selected_ids:
        return {'success': False, 'message': 'No bookings selected'}, 400
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            deleted_count = 0
            for booking_id in selected_ids:
                # Check if booking exists
                cursor.execute("SELECT id FROM bookings WHERE id = %s", (booking_id,))
                if cursor.fetchone():
                    
                    # Delete passengers first (foreign key constraint)
                    cursor.execute("DELETE FROM passengers WHERE booking_id = %s", (booking_id,))
                    
                    # Delete payment records if any
                    cursor.execute("DELETE FROM payments WHERE booking_id = %s", (booking_id,))
                    
                    # Delete booking
                    cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
                    deleted_count += 1
            
            conn.commit()
            flash(f'{deleted_count} booking(s) deleted successfully!', 'success')
            return {'success': True, 'message': f'{deleted_count} booking(s) deleted'}
        except Exception as e:
            flash(f'Error deleting bookings: {str(e)}', 'danger')
            return {'success': False, 'message': str(e)}, 500
        finally:
            cursor.close()
            conn.close()
    
    return {'success': False, 'message': 'Database connection failed'}, 500

# ==================== PENDING BOOKINGS (APPROVAL) ====================

@admin_bp.route('/pending-bookings')
@admin_required
def pending_bookings():
    conn = get_db_connection()
    pending_bookings = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                b.booking_status,
                b.created_at,
                u.name AS user_name,
                u.email AS user_email,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                t.train_no,
                t.train_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.booking_status = 'PENDING_ADMIN'
            ORDER BY b.created_at ASC
        """)
        pending_bookings = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/pending_bookings.html', pending_bookings=pending_bookings)

@admin_bp.route('/bookings/approve/<int:booking_id>', methods=['POST'])
@admin_required
def approve_booking(booking_id):
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE bookings 
                SET booking_status = 'APPROVED', approved_at = NOW()
                WHERE id = %s AND booking_status = 'PENDING_ADMIN'
            """, (booking_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                flash('Booking approved successfully! User can now proceed with payment.', 'success')
            else:
                flash('Booking not found or already processed.', 'warning')
        except Exception as e:
            flash(f'Error approving booking: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.pending_bookings'))

@admin_bp.route('/bookings/reject/<int:booking_id>', methods=['POST'])
@admin_required
def reject_booking(booking_id):
    admin_note = request.form.get('admin_note', '').strip()
    
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get booking to restore seats
            cursor.execute("""
                SELECT b.*, s.id as schedule_id
                FROM bookings b
                JOIN schedules s ON b.schedule_id = s.id
                WHERE b.id = %s AND b.booking_status = 'PENDING_ADMIN'
            """, (booking_id,))
            
            booking = cursor.fetchone()
            
            if booking:
                # Get passenger count
                cursor.execute("SELECT COUNT(*) as count FROM passengers WHERE booking_id = %s", (booking_id,))
                passenger_count = cursor.fetchone()['count']
                
                # Update booking status to rejected
                cursor.execute("""
                    UPDATE bookings 
                    SET booking_status = 'REJECTED', 
                        admin_note = %s, 
                        approved_at = NOW()
                    WHERE id = %s
                """, (admin_note if admin_note else None, booking_id))
                
                # Restore seats
                cursor.execute("""
                    UPDATE schedules SET available_seats = available_seats + %s
                    WHERE id = %s
                """, (passenger_count, booking['schedule_id']))
                
                conn.commit()
                flash('Booking rejected successfully. Seats have been restored.', 'success')
            else:
                flash('Booking not found or already processed.', 'warning')
        except Exception as e:
            flash(f'Error rejecting booking: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.pending_bookings'))

# ==================== PAYMENT VERIFICATION ====================

@admin_bp.route('/payment-verification')
@admin_required
def payment_verification():
    conn = get_db_connection()
    paid_bookings = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                b.booking_status,
                b.payment_status,
                b.txn_id,
                b.created_at,
                u.name AS user_name,
                u.email AS user_email,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                t.train_no,
                t.train_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.payment_status = 'PAID' AND b.payment_verified = 0
            ORDER BY b.created_at ASC
        """)
        paid_bookings = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('admin/payment_verification.html', paid_bookings=paid_bookings)

@admin_bp.route('/payments/verify/<int:booking_id>', methods=['POST'])
@admin_required
def verify_payment(booking_id):
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor()
        try:
            # Update payment verification and booking status
            cursor.execute("""
                UPDATE bookings 
                SET payment_verified = 1, 
                    verified_at = NOW(), 
                    booking_status = 'CONFIRMED',
                    status = 'Confirmed'
                WHERE id = %s AND payment_status = 'PAID' AND payment_verified = 0
            """, (booking_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                flash('Payment verified successfully! Booking is now CONFIRMED and ticket is available.', 'success')
            else:
                flash('Booking not found or already verified.', 'warning')
        except Exception as e:
            flash(f'Error verifying payment: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('admin.payment_verification'))

# ==================== ANALYTICS DASHBOARD ====================

@admin_bp.route('/analytics')
@admin_required
def analytics():
    conn = get_db_connection()
    chart_data = {}
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Revenue trend (last 7 days)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                SUM(CASE WHEN status = 'Confirmed' THEN total_fare ELSE 0 END) as revenue
            FROM bookings
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """)
        revenue_data = cursor.fetchall()
        chart_data['revenue'] = revenue_data
        
        # 2. Booking status distribution
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM bookings
            GROUP BY status
        """)
        status_data = cursor.fetchall()
        chart_data['status'] = status_data
        
        # 3. Top 5 popular routes
        cursor.execute("""
            SELECT 
                CONCAT(st1.station_name, ' → ', st2.station_name) as route_name,
                COUNT(b.id) as bookings
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            GROUP BY r.id, route_name
            ORDER BY bookings DESC
            LIMIT 5
        """)
        routes_data = cursor.fetchall()
        chart_data['routes'] = routes_data
        
        cursor.close()
        conn.close()
    
    return render_template('admin/analytics.html', chart_data=chart_data)