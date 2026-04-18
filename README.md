# 🎫 Ticket Management System

Ek simple aur muskil ticket booking system jo trains ke liye banaya gaya hai. Users easily se apni tickets book kar sakte hain, aur admin panel se pura system manage kar sakte hain.

## ✨ Features

- **User Registration & Login** - Secure authentication system
- **Train Search** - Available trains dhundho apne dates ke according
- **Ticket Booking** - Asaan se ticket book karo at passenger details ke saath
- **Payment Integration** - Online payment support(Dummp payment method)
- **Booking History** - Apne saarey tickets dekho ek jagah
- **Admin Dashboard** - Trains, schedules, stations manage karo
- **Payment Verification** - Admin se payment verification system
- **Analytics** - Booking statistics aur reports

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

### 1. Project ko Clone Karo
```bash
git clone <repository-link>
cd Ticket-Management-System
```

### 2. Python Dependencies Install Karo
```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup Karo
```bash
# MySQL mein jaao aur ye command run karo:
mysql -u root -p < ../database/schema.sql
```

### 4. Config File Setup Karo
`backend/config.py` mein apni settings daalo:
- Database credentials
- Secret key
- Koi aur configuration

## 🏃 How to Run

```bash
cd backend
python app.py
```

Application automatically http://localhost:5000 par khul jaega

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
│   │   ├── auth/        # Login aur Register pages
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

1. **Home Page** - App khulte hi home page nazar aayega
2. **Register Karo** - Naya account banao
3. **Login Karo** - Apne credentials se login karo
4. **Trains Search Karo** - Date aur destination select karo
5. **Ticket Book Karo** - Passengers details aur make payment
6. **Admin Panel** (Admin ke liye) - Dashboard mein trains/schedules manage karo

## 🔒 Admin Access

Admin panel mein kaise jaao:
- Admin specific route use karo
- Admin credentials se login karo

## ⚠️ Important Notes

- Database credentials properly set karo config.py mein
- MySQL server chala skhe hona zaroori hai
- Payment gateway properly configure karna hoga (agar use kar rahe ho)

## 👨‍💻 Author

Your Name / Your GitHub

## 📞 Support

Koi problem ho toh:
1. Issues section mein report karo
2. Ya directly contact karo

## 📄 License

This project is open source. You can use it for learning and development purposes.

---

**Happy Coding! 🚀**
