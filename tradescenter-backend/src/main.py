import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from src.routes.admin import admin_bp
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.contractors import contractors_bp
from src.routes.projects import projects_bp
from src.routes.reviews import reviews_bp
from src.routes.social import social_bp
from src.routes.messages import messages_bp
from src.routes.tiers import tiers_bp
from src.routes.billing import billing_bp
from src.routes.verification import verification_bp
from src.routes.discovery import discovery_bp
from src.routes.profile_access import profile_access_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "tradescenter-dev-secret")

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(contractors_bp, url_prefix='/api')
app.register_blueprint(projects_bp, url_prefix='/api')
app.register_blueprint(reviews_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(social_bp, url_prefix='/api')
app.register_blueprint(messages_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(tiers_bp, url_prefix='/api')
app.register_blueprint(billing_bp, url_prefix='/api')
app.register_blueprint(verification_bp, url_prefix='/api')
app.register_blueprint(discovery_bp, url_prefix='/api')
app.register_blueprint(profile_access_bp, url_prefix='/api')

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "persistence": "supabase"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
