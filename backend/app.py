from flask import Flask, redirect, url_for
from config import SECRET_KEY

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.secret_key = SECRET_KEY


# Import blueprints
from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.admin import admin_bp


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)


# Home route
@app.route('/')
def index():
    return redirect(url_for('auth.home'))

if __name__ == '__main__':
    app.run(debug=True)