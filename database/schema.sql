-- ═══════════════════════════════════════════════════════════════════════════════════
-- RAILWAY TICKET BOOKING SYSTEM - DATABASE SCHEMA (TRAINS ONLY)
-- Created: 2025 | Completely Fresh Database Structure
-- ═══════════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────────
-- CREATE DATABASE & SELECT
-- ─────────────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS ticket_db;
USE ticket_db;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 1: USERS (User Registration & Login)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_email (email),
    KEY idx_phone (phone),
    KEY idx_admin (is_admin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 2: STATIONS (Train Stations Database)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE stations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    station_name VARCHAR(100) NOT NULL UNIQUE,
    station_code VARCHAR(10) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_station_code (station_code),
    KEY idx_station_name (station_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 3: TRAINS (Train Master Data)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE trains (
    id INT PRIMARY KEY AUTO_INCREMENT,
    train_no VARCHAR(20) NOT NULL UNIQUE,
    train_name VARCHAR(100) NOT NULL,
    total_seats INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    KEY idx_train_no (train_no),
    KEY idx_train_name (train_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 4: ROUTES (Train Routes - From Station to Station)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE routes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    train_id INT NOT NULL,
    from_station_id INT NOT NULL,
    to_station_id INT NOT NULL,
    distance INT DEFAULT 0,
    fare DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE,
    FOREIGN KEY (from_station_id) REFERENCES stations(id) ON DELETE CASCADE,
    FOREIGN KEY (to_station_id) REFERENCES stations(id) ON DELETE CASCADE,
    
    KEY idx_train_id (train_id),
    KEY idx_from_station (from_station_id),
    KEY idx_to_station (to_station_id),
    UNIQUE KEY unique_route (train_id, from_station_id, to_station_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 5: SCHEDULES (Train Schedules - Departure & Arrival Times)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    route_id INT NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    available_seats INT NOT NULL,
    journey_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
    
    KEY idx_route_id (route_id),
    KEY idx_journey_date (journey_date),
    KEY idx_available_seats (available_seats),
    UNIQUE KEY unique_schedule (route_id, journey_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 6: BOOKINGS (Train Ticket Bookings)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE bookings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    schedule_id INT NOT NULL,
    pnr VARCHAR(20) NOT NULL UNIQUE,
    journey_date DATE NOT NULL,
    total_fare DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    booking_status VARCHAR(30) DEFAULT 'PENDING_ADMIN',
    payment_status VARCHAR(20) DEFAULT 'UNPAID',
    payment_verified TINYINT DEFAULT 0,
    txn_id VARCHAR(50) NULL,
    refund_amount DECIMAL(10, 2) DEFAULT 0,
    refund_status VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    
    KEY idx_user_id (user_id),
    KEY idx_schedule_id (schedule_id),
    KEY idx_pnr (pnr),
    KEY idx_status (status),
    KEY idx_payment_status (payment_status),
    KEY idx_booking_status (booking_status),
    KEY idx_journey_date (journey_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 7: PASSENGERS (Passenger Details in Each Booking)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE passengers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    
    KEY idx_booking_id (booking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═════════════════════════════════════════════════════════════════════════════════
-- TABLE 8: PAYMENTS (Payment Records)
-- ═════════════════════════════════════════════════════════════════════════════════

CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'Success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    
    KEY idx_booking_id (booking_id),
    KEY idx_payment_status (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ═══════════════════════════════════════════════════════════════════════════════════
-- SAMPLE DATA (Optional - Remove after testing)
-- ═══════════════════════════════════════════════════════════════════════════════════

-- Sample Stations
INSERT INTO stations (station_name, station_code) VALUES
('Mumbai Central', 'MUM'),
('Delhi New Delhi', 'DEL'),
('Bangalore City', 'BLR'),
('Kolkata Howrah', 'KOL'),
('Chennai Central', 'CHE'),
('Hyderabad Nampally', 'HYD'),
('Pune Junction', 'PUN'),
('Ahmedabad Junction', 'AHM');

-- Sample Trains
INSERT INTO trains (train_no, train_name, total_seats) VALUES
('12015', 'Shatabdi Express', 120),
('12019', 'Rajdhani Express', 150),
('12810', 'Duronto Express', 140),
('12345', 'Jan Shatabdi', 100),
('12456', 'Garib Rath', 110),
('12567', 'Superfast Express', 130);

-- Sample Routes (after stations & trains are created)
-- NOTE: Insert these after ensuring station and train IDs match your data

-- ═══════════════════════════════════════════════════════════════════════════════════
-- VERIFY DATABASE STRUCTURE
-- ═══════════════════════════════════════════════════════════════════════════════════

SHOW TABLES;
SHOW TABLE STATUS;
ALTER TABLE bookings ADD COLUMN admin_note VARCHAR(255) NULL AFTER txn_id;
ALTER TABLE bookings ADD COLUMN approved_at DATETIME NULL AFTER admin_note;
ALTER TABLE bookings ADD COLUMN verified_at DATETIME NULL AFTER approved_at;


-- ==================== REFUND FEATURE MIGRATION ====================
-- Add refund columns to bookings table

-- ALTER TABLE bookings 
-- ADD COLUMN refund_amount DECIMAL(10,2) DEFAULT 0 AFTER total_fare;

-- ALTER TABLE bookings 
-- ADD COLUMN refund_status VARCHAR(20) DEFAULT 'NOT_REFUNDED' AFTER refund_amount;

DESCRIBE bookings;


-- Update existing cancelled bookings to show refund
UPDATE bookings 
SET refund_amount = total_fare, 
    refund_status = 'REFUNDED' 
WHERE status = 'Cancelled';

