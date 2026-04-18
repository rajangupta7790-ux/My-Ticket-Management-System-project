from db import get_db_connection

# ========== USER FUNCTIONS ==========

def create_user(name, phone, email, hashed_password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, phone, email, password) VALUES (%s, %s, %s, %s)",
                (name, phone, email, hashed_password)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False

def get_user_by_email_or_phone(identifier):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s OR phone = %s",
            (identifier, identifier)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    return None

# ========== STATION FUNCTIONS ==========

def get_stations():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT station_name FROM stations ORDER BY station_name")
        stations = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return stations
    return []

# ========== SCHEDULE FUNCTIONS ==========

def search_schedules(from_station_id, to_station_id, from_text, to_text, journey_date, passengers_count):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # If text names provided, get or create station ids
        if from_text and to_text:
            from_station_id = get_or_create_station_by_name(from_text)
            to_station_id = get_or_create_station_by_name(to_text)
            
            if not from_station_id or not to_station_id:
                cursor.close()
                conn.close()
                return []
        
        query = """
            SELECT 
                s.id,
                t.train_no,
                t.train_name,
                st1.station_name AS from_station,
                st2.station_name AS to_station,
                s.departure_time,
                s.arrival_time,
                r.fare,
                s.available_seats
            FROM schedules s
            JOIN routes r ON s.route_id = r.id
            JOIN trains t ON r.train_id = t.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE r.from_station_id = %s
            AND r.to_station_id = %s
            AND s.journey_date = %s
            AND s.available_seats >= %s
        """
        cursor.execute(query, (from_station_id, to_station_id, journey_date, passengers_count))
        schedules = cursor.fetchall()
        
        # Add is_random flag
        for schedule in schedules:
            schedule['is_random'] = False
        
        cursor.close()
        conn.close()
        return schedules
    return []

# ========== BOOKING FUNCTIONS ==========

def create_booking(user_id, schedule_id, pnr, journey_date, total_fare):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO bookings (user_id, schedule_id, pnr, journey_date, total_fare, status)
                VALUES (%s, %s, %s, %s, %s, 'Confirmed')
            """, (user_id, schedule_id, pnr, journey_date, total_fare))
            conn.commit()
            booking_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return booking_id
        except Exception as e:
            print(f"Error creating booking: {e}")
            cursor.close()
            conn.close()
            return None
    return None

def get_booking_ticket(booking_id, user_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
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
        """, (booking_id, user_id))
        
        ticket = cursor.fetchone()
        
        if ticket:
            cursor.execute("""
                SELECT name, age, gender FROM passengers WHERE booking_id = %s
            """, (booking_id,))
            ticket['passengers'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return ticket
    return None

def create_payment(booking_id, amount, payment_method):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO payments (booking_id, amount, payment_method, payment_status)
                VALUES (%s, %s, %s, 'Success')
            """, (booking_id, amount, payment_method))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating payment: {e}")
            cursor.close()
            conn.close()
            return False
    return False

def list_user_bookings(user_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.id,
                b.pnr,
                b.journey_date,
                b.total_fare,
                b.status,
                st1.station_name AS from_station,
                st2.station_name AS to_station
            FROM bookings b
            JOIN schedules s ON b.schedule_id = s.id
            JOIN routes r ON s.route_id = r.id
            JOIN stations st1 ON r.from_station_id = st1.id
            JOIN stations st2 ON r.to_station_id = st2.id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
        """, (user_id,))
        
        bookings = cursor.fetchall()
        cursor.close()
        conn.close()
        return bookings
    return []

def cancel_booking(booking_id, user_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Check if booking belongs to user and is confirmed
            cursor.execute("""
                SELECT b.*, s.id as schedule_id
                FROM bookings b
                JOIN schedules s ON b.schedule_id = s.id
                WHERE b.id = %s AND b.user_id = %s AND b.status = 'Confirmed'
            """, (booking_id, user_id))
            
            booking = cursor.fetchone()
            
            if booking:
                # Get passenger count
                cursor.execute("SELECT COUNT(*) as count FROM passengers WHERE booking_id = %s", (booking_id,))
                passenger_count = cursor.fetchone()['count']
                
                # Update booking status
                cursor.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = %s", (booking_id,))
                
                # Restore seats
                cursor.execute("""
                    UPDATE schedules SET available_seats = available_seats + %s
                    WHERE id = %s
                """, (passenger_count, booking['schedule_id']))
                
                conn.commit()
                cursor.close()
                conn.close()
                return True
            else:
                cursor.close()
                conn.close()
                return False
        except Exception as e:
            print(f"Error cancelling booking: {e}")
            cursor.close()
            conn.close()
            return False
    return False

def get_or_create_station_by_name(station_name):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Trim and title-case
        station_name = station_name.strip().title()
        
        # Check if station exists
        cursor.execute("SELECT id FROM stations WHERE station_name = %s", (station_name,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return existing['id']
        
        # Generate station code
        clean_name = station_name.replace(' ', '').upper()
        station_code = clean_name[:4].ljust(4, 'X')
        
        # Check uniqueness
        cursor.execute("SELECT id FROM stations WHERE station_code = %s", (station_code,))
        if cursor.fetchone():
            import random
            station_code = station_code[:2] + str(random.randint(10, 99))
        
        # Insert new station
        try:
            cursor.execute(
                "INSERT INTO stations (station_name, station_code) VALUES (%s, %s)",
                (station_name, station_code)
            )
            conn.commit()
            station_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return station_id
        except Exception as e:
            print(f"Error creating station: {e}")
            cursor.close()
            conn.close()
            return None
    return None

def generate_random_schedules(from_name, to_name, journey_date, pax, count=8):
    import random
    from datetime import datetime, timedelta
    
    train_names = [
        "Rajdhani Express",
        "Shatabdi Express",
        "Duronto Express",
        "Garib Rath",
        "Superfast Express",
        "Intercity Express",
        "Jan Shatabdi",
        "Humsafar Express",
        "Vande Bharat Express",
        "Tejas Express"
    ]
    
    # Get or create station IDs
    from_station_id = get_or_create_station_by_name(from_name)
    to_station_id = get_or_create_station_by_name(to_name)
    
    if not from_station_id or not to_station_id:
        return []
    
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    schedules = []
    
    try:
        for i in range(count):
            # Random departure time
            dep_hour = random.randint(5, 22)
            dep_min = random.choice([0, 15, 30, 45])
            departure = f"{dep_hour:02d}:{dep_min:02d}"
            
            # Random journey duration (2-8 hours)
            duration_hours = random.randint(2, 8)
            duration_mins = random.choice([0, 15, 30, 45])
            
            dep_dt = datetime.strptime(departure, "%H:%M")
            arr_dt = dep_dt + timedelta(hours=duration_hours, minutes=duration_mins)
            arrival = arr_dt.strftime("%H:%M")
            
            # Random fare
            base_fare = random.randint(120, 950)
            
            # Random seats
            seats = random.randint(pax, pax + random.randint(10, 50))
            
            # Random train details
            train_no = str(random.randint(10000, 99999))
            train_name = random.choice(train_names)
            
            # Insert demo train
            cursor.execute("""
                INSERT INTO trains (train_no, train_name, total_seats)
                VALUES (%s, %s, %s)
            """, (train_no, train_name, seats))
            train_id = cursor.lastrowid
            
            # Insert demo route
            cursor.execute("""
                INSERT INTO routes (train_id, from_station_id, to_station_id, distance, fare)
                VALUES (%s, %s, %s, %s, %s)
            """, (train_id, from_station_id, to_station_id, 200, base_fare))
            route_id = cursor.lastrowid
            
            # Insert demo schedule
            cursor.execute("""
                INSERT INTO schedules (route_id, departure_time, arrival_time, available_seats, journey_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (route_id, departure, arrival, seats, journey_date))
            schedule_id = cursor.lastrowid
            
            schedule = {
                'id': schedule_id,
                'train_no': train_no,
                'train_name': train_name,
                'from_station': from_name,
                'to_station': to_name,
                'departure_time': departure,
                'arrival_time': arrival,
                'fare': base_fare,
                'available_seats': seats,
                'is_random': True
            }
            
            schedules.append(schedule)
        
        conn.commit()
        
    except Exception as e:
        print(f"Error generating random schedules: {e}")
        conn.rollback()
        schedules = []
    finally:
        cursor.close()
        conn.close()
    
    return schedules