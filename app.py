# Create an enhanced app.py
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Production configurations
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///weather_dashboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Production security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Error handling for production
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

db = SQLAlchemy(app)

# Database Models
class WeatherHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    temperature_max = db.Column(db.Float)
    temperature_min = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'date': self.date.isoformat(),
            'temperature_max': self.temperature_max,
            'temperature_min': self.temperature_min,
            'precipitation': self.precipitation,
            'created_at': self.created_at.isoformat()
        }

class UserSearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'searched_at': self.searched_at.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html', 
        config={
            'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY'),
            'OPENCAGE_API_KEY': os.getenv('OPENCAGE_API_KEY')
        }
    )

@app.route('/api/save-search', methods=['POST'])
def save_search():
    try:
        data = request.json
        search_record = UserSearchHistory(city=data['city'])
        db.session.add(search_record)
        db.session.commit()
        return jsonify({'message': 'Search saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/save-weather', methods=['POST'])
def save_weather():
    try:
        data = request.json
        weather_record = WeatherHistory(
            city=data['city'],
            date=datetime.fromisoformat(data['date']),
            temperature_max=data['temperature_max'],
            temperature_min=data['temperature_min'],
            precipitation=data['precipitation']
        )
        db.session.add(weather_record)
        db.session.commit()
        return jsonify({'message': 'Weather data saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/search-history', methods=['GET'])
def get_search_history():
    try:
        history = UserSearchHistory.query.order_by(
            UserSearchHistory.searched_at.desc()
        ).limit(10).all()
        return jsonify([record.to_dict() for record in history])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Don't run with debug=True in production
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
