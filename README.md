# 🎫 Ticket Management System

A simple and efficient ticket booking system designed for trains. Users can easily book their tickets, 
and the entire system can be managed through the admin panel.

## ✨ Features

- **User Registration & Login** - Secure authentication system
- **Train Search** - Find available trains according to your selected dates
- **Ticket Booking** - Easily book tickets with passenger details
- **Payment Integration** - Online payment support(Dummp payment method)
- **Booking History** - View all your tickets in one place
- **Admin Dashboard** - Manage trains, schedules, and stations
- **Payment Verification** - Admin-based payment verification system
- **Analytics** - Booking statistics and reports

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript
- **Libraries**: Flask, mysql-connector-python, Werkzeug

## 📋 Requirements

```
Python 3.x
MySQL
```

## 🚀 Installation & Setup

### 1. Clone the Project
```bash
git clone <repository-link>
cd Ticket-Management-System
```

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup 
```bash
# Go to MySQL and run this command:
mysql -u root -p < ../database/schema.sql
```

### 4. Configure the Config File
`Add your settings in backend/config.py:
- Database credentials
- Secret key
- Any other configuration

## 🏃 How to Run

```bash
cd backend
python app.py
```

The application will automatically open at: http://localhost:5000 

## 📁 Project Structure

```
Ticket Management System/
├── backend/
│   ├── app.py           # Main Flask application
│   ├── config.py        # Configuration settings
│   ├── db.py            # Database connection
│   ├── models.py        # Database models
│   └── routes/
│       ├── auth.py      # Login/Register routes
│       ├── booking.py   # Booking routes
│       └── admin.py     # Admin panel routes
│
├── frontend/
│   ├── templates/       # HTML files
│   │   ├── auth/        # Login and Register pages
│   │   ├── booking/     # Booking related pages
│   │   └── admin/       # Admin panel pages
│   └── static/
│       ├── css/         # Styling
│       └── js/          # JavaScript
│
└── database/
    └── schema.sql       # Database schema
```

## 📖 Usage

1.Home Page     – The home page will appear when the app starts
2.Register      – Create a new account
3.Login         – Log in using your credentials
4.Search Trains – Select date and destination
5.Book Ticket   – Enter passenger details and make payment
6.Admin Panel   – Manage trains and schedules from the dashboard

## 🔒 Admin Access

How to access the admin panel:
- Use the admin-specific route
- Log in with admin credentials

## ⚠️ Important Notes

- Properly set database credentials in config.py
- MySQL server must be running
- Payment gateway must be properly configured (if being used)

## 👨‍💻 Author

Your Name / Your GitHub

## 📞 Support

If you face any problem:
1.Report it in the Issues section
2.Or contact directly

## 📄 License

This project is open source. You can use it for learning and development purposes.

---

**Happy Coding! 🚀**


                                        ## ---- SCREENSHOTS SECTIONS ----- ##

## ---- Admin Dashboard ----
<img width="1890" height="924" alt="Screenshot 2026-04-18 151930" src="https://github.com/user-attachments/assets/0a43aea2-5f73-452b-8219-4bdf7bdb0971" />


## ---- Home Page ----
<img width="1875" height="847" alt="Screenshot 2026-04-18 151709" src="https://github.com/user-attachments/assets/a6f53289-448f-43d1-b545-b3950536f50b" />


## ---- Features ---- 
<img width="1872" height="905" alt="Screenshot 2026-04-18 151727" src="https://github.com/user-attachments/assets/5d7b2893-c5f5-4abe-895b-c0ea7f3589a0" />


























