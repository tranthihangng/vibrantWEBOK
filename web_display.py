from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from database_handler import DatabaseHandler
import json
from datetime import datetime, timedelta
import pandas as pd
import io
import threading
import time
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread for real-time updates
thread = None
thread_lock = threading.Lock()

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

def get_pump_status():
    try:
        db = DatabaseHandler()
        latest_predictions = db.get_recent_predictions(limit=1)
        
        if not latest_predictions:
            return {
                'status': 'UNKNOWN',
                'last_updated': None,
                'probabilities': {
                    'normal': 0,
                    'rung_12_5': 0,
                    'rung_6': 0,
                    'stop': 0
                }
            }
        
        latest = latest_predictions[0]
        probabilities = {
            'normal': 0,
            'rung_12_5': 0,
            'rung_6': 0,
            'stop': 0
        }
        
        if 'features' in latest and latest['features']:
            features = json.loads(latest['features']) if isinstance(latest['features'], str) else latest['features']
            if isinstance(features, dict):
                if 'probabilities' in features:
                    probabilities = features['probabilities']
                elif all(key in features for key in probabilities.keys()):
                    probabilities = {k: float(features[k]) for k in probabilities.keys()}
        
        return {
            'status': latest['status'].upper(),
            'last_updated': "2025-05-18 13:10:54",  # Fixed timestamp
            'probabilities': probabilities
        }
    except Exception as e:
        print(f"Error getting pump status: {e}")
        return None

def get_daily_stats():
    try:
        db = DatabaseHandler()
        today = datetime.now().date()
        stats = db.get_daily_stats(days=1)
        
        if not stats:
            return {
                'total': 0,
                'normal': 0,
                'minor_faults': 0,
                'major_faults': 0
            }
        
        today_stats = next((s for s in stats if s['date'].date() == today), None)
        
        if not today_stats:
            return {
                'total': 0,
                'normal': 0,
                'minor_faults': 0,
                'major_faults': 0
            }
        
        return {
            'total': today_stats.get('total_predictions', 0),
            'normal': today_stats.get('normal_count', 0),
            'minor_faults': today_stats.get('rung_6_count', 0),
            'major_faults': today_stats.get('rung_12_5_count', 0)
        }
    except Exception as e:
        print(f"Error getting daily stats: {e}")
        return None

def background_thread():
    while True:
        try:
            status = get_pump_status()
            if status:
                socketio.emit('status_update', status)
            
            stats = get_daily_stats()
            if stats:
                socketio.emit('stats_update', stats)
                
        except Exception as e:
            print(f"Error in background thread: {e}")
        
        time.sleep(1)

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = threading.Thread(target=background_thread)
            thread.daemon = True
            thread.start()
    
    # Send initial data
    status = get_pump_status()
    if status:
        emit('status_update', status)
    
    stats = get_daily_stats()
    if stats:
        emit('stats_update', stats)

@app.route('/')
def index():
    return render_template('index.html',
                         pump_status=get_pump_status(),
                         daily_stats=get_daily_stats())

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def get_history():
    try:
        db = DatabaseHandler()
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        status = request.args.get('status', 'all')

        # Build query parameters
        params = {}
        if date_from:
            params['start_time'] = datetime.strptime(date_from, '%Y-%m-%dT%H:%M')
        if date_to:
            params['end_time'] = datetime.strptime(date_to, '%Y-%m-%dT%H:%M')
        if status and status.lower() != 'all':
            params['status'] = status

        # Get total count and paginated data
        total = db.get_predictions_count(**params)
        predictions = db.get_predictions_paginated(page=page, per_page=per_page, **params)
        
        # Format results
        formatted_data = []
        for pred in predictions:
            probabilities = {
                'normal': 0,
                'rung_12_5': 0,
                'rung_6': 0,
                'stop': 0
            }
            
            if pred.get('features'):
                features = json.loads(pred['features']) if isinstance(pred['features'], str) else pred['features']
                if isinstance(features, dict):
                    if 'probabilities' in features:
                        probabilities = features['probabilities']
                    elif all(key in features for key in probabilities.keys()):
                        probabilities = {k: float(features[k]) for k in probabilities.keys()}
            
            formatted_data.append({
                'time': pred['time'],
                'status': pred['status'].upper(),
                'probabilities': probabilities,
                'confidence': max(probabilities.values())
            })
        
        return jsonify({
            'data': formatted_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-csv')
def export_csv():
    try:
        db = DatabaseHandler()
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        status = request.args.get('status', 'all')

        # Build query parameters
        params = {}
        if date_from:
            params['start_time'] = datetime.strptime(date_from, '%Y-%m-%dT%H:%M')
        if date_to:
            params['end_time'] = datetime.strptime(date_to, '%Y-%m-%dT%H:%M')
        if status and status.lower() != 'all':
            params['status'] = status

        predictions = db.get_predictions_by_timerange(**params)
        
        # Prepare data for CSV
        data = []
        for pred in predictions:
            probabilities = {
                'normal': 0,
                'rung_12_5': 0,
                'rung_6': 0,
                'stop': 0
            }
            
            if pred.get('features'):
                features = json.loads(pred['features']) if isinstance(pred['features'], str) else pred['features']
                if isinstance(features, dict):
                    if 'probabilities' in features:
                        probabilities = features['probabilities']
                    elif all(key in features for key in probabilities.keys()):
                        probabilities = {k: float(features[k]) for k in probabilities.keys()}
            
            data.append({
                'Time': pred['time'].strftime("%Y-%m-%d %H:%M:%S"),
                'Status': pred['status'].upper(),
                'Normal Probability': f"{probabilities['normal']*100:.2f}%",
                'Rung 12.5Hz Probability': f"{probabilities['rung_12_5']*100:.2f}%",
                'Rung 6Hz Probability': f"{probabilities['rung_6']*100:.2f}%",
                'Stop Probability': f"{probabilities['stop']*100:.2f}%",
                'Confidence': f"{max(probabilities.values())*100:.2f}%"
            })
        
        # Create CSV
        df = pd.DataFrame(data)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        
        return send_file(
            io.BytesIO(buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'pump_predictions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-report')
def export_report():
    try:
        db = DatabaseHandler()
        predictions = db.get_recent_predictions(limit=1000)
        stats = db.get_daily_stats(days=7)
        heatmap_data = db.get_hourly_heatmap(days=7)

        # Create DataFrame for heatmap
        heatmap_df = pd.DataFrame(heatmap_data)
        pivot_table = heatmap_df.pivot(index='date', columns='hour', values='fault_count')

        # Create PDF report with matplotlib
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Heatmap
        plt.subplot(2, 1, 1)
        sns.heatmap(pivot_table, cmap='YlOrRd', annot=True, fmt='.0f')
        plt.title('Fault Occurrence Heatmap')
        
        # Plot 2: Daily Stats
        stats_df = pd.DataFrame(stats)
        plt.subplot(2, 1, 2)
        stats_df.plot(x='date', y=['fault_rate', 'avg_normal_prob', 'avg_fault_prob'])
        plt.title('Daily Statistics')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='pdf', bbox_inches='tight')
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'pump_report_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        print(f"Error exporting report: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000) 