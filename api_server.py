from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)  # Cho phép cross-origin requests

# API endpoints
@app.route('/api/status')
def get_status():
    # TODO: Thay thế bằng dữ liệu thực từ model của bạn
    return jsonify({
        'status': 'normal',
        'probabilities': {
            'normal': 0.85,
            'rung_6': 0.1,
            'rung_12_5': 0.03,
            'stop': 0.02
        },
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/daily-stats')
def get_daily_stats():
    # TODO: Thay thế bằng dữ liệu thực từ database của bạn
    dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
    data = []
    
    for date in dates:
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'normal_count': np.random.randint(50, 100),
            'rung_6_count': np.random.randint(10, 30),
            'rung_12_5_count': np.random.randint(5, 15),
            'stop_count': np.random.randint(0, 10)
        })
    
    return jsonify(data)

@app.route('/api/heatmap-data')
def get_heatmap_data():
    # TODO: Thay thế bằng dữ liệu thực từ database của bạn
    hours = list(range(24))
    dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
    data = []
    
    for date in dates:
        for hour in hours:
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'hour': hour,
                'normal_count': np.random.randint(30, 70),
                'rung_6_count': np.random.randint(5, 20),
                'rung_12_5_count': np.random.randint(0, 10),
                'stop_count': np.random.randint(0, 5)
            })
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 