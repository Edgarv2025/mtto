from flask import Flask
from config import Config
from db import init_app_db

# Import Blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.suppliers import suppliers_bp
from routes.maintenance import maintenance_bp
from routes.reports import reports_bp

app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(reports_bp)

# Initialize DB and migrations if needed
with app.app_context():
    init_app_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
