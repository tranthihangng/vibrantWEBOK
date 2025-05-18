from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import mysql.connector
import json
from datetime import datetime, timedelta
import pandas as pd
import io
import threading
import time
from database_handler import DatabaseHandler

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'pump_monitoring'
}

# Thread for real-time updates
thread = None
thread_lock = threading.Lock()

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_pump_status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get latest prediction
        cursor.execute("""
            SELECT time, status, features
            FROM predictions
            ORDER BY time DESC
            LIMIT 1
        """)
        latest = cursor.fetchone()
        
        if not latest:
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
        
        # Parse features JSON
        probabilities = {
            'normal': 0,
            'rung_12_5': 0,
            'rung_6': 0,
            'stop': 0
        }
        
        if latest['features']:
            features = json.loads(latest['features'])
            if isinstance(features, dict):
                if 'probabilities' in features:
                    probabilities = features['probabilities']
                elif all(key in features for key in probabilities.keys()):
                    probabilities = {k: float(features[k]) for k in probabilities.keys()}
        
        cursor.close()
        conn.close()
        
        return {
            'status': latest['status'].upper(),
            'last_updated': "2025-05-18 13:10:54",
            'probabilities': probabilities
        }
    except Exception as e:
        print(f"Error getting pump status: {e}")
        return None

def get_daily_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        
        # Get today's statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'normal' THEN 1 ELSE 0 END) as normal_count,
                SUM(CASE WHEN status = 'rung_6' THEN 1 ELSE 0 END) as rung_6_count,
                SUM(CASE WHEN status = 'rung_12_5' THEN 1 ELSE 0 END) as rung_12_5_count
            FROM predictions
            WHERE DATE(time) = %s
        """, (today,))
        
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            'total': stats['total'] or 0,
            'normal': stats['normal_count'] or 0,
            'minor_faults': stats['rung_6_count'] or 0,
            'major_faults': stats['rung_12_5_count'] or 0
        }
    except Exception as e:
        print(f"Error getting daily stats: {e}")
        return None

def background_thread():
    """Thread that handles real-time updates"""
    db = DatabaseHandler()
    
    while True:
        try:
            # Get latest prediction
            latest = db.get_latest_prediction()
            if latest:
                # Format data for frontend
                status_data = {
                    'status': latest['status'].upper(),
                    'last_updated': latest['time'].strftime("%Y-%m-%d %H:%M:%S"),
                    'probabilities': latest['features'].get('probabilities', {}) if latest['features'] else {}
                }
                socketio.emit('status_update', status_data)
            
            # Get daily stats
            stats = db.get_daily_stats()
            if stats:
                socketio.emit('stats_update', stats)
                
        except Exception as e:
            print(f"Error in background thread: {e}")
            
        time.sleep(1)  # Update every second

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    global thread
    with thread_lock:
        if thread is None:
            thread = threading.Thread(target=background_thread)
            thread.daemon = True
            thread.start()

@app.route('/')
def index():
    """Render main dashboard"""
    db = DatabaseHandler()
    latest = db.get_latest_prediction()
    stats = db.get_daily_stats()
    
    return render_template('index.html', 
                         latest_prediction=latest,
                         daily_stats=stats)

@app.route('/history')
def history():
    """Render history page"""
    return render_template('history.html')

@app.route('/api/history')
def get_history():
    """API endpoint for history data"""
    db = DatabaseHandler()
    page = int(request.args.get('page', 1))
    result = db.get_predictions_by_timerange(page=page)
    
    if result:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch history'}), 500

@app.route('/api/export-csv')
def export_csv():
    try:
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        status = request.args.get('status', 'all')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build query conditions
        conditions = ["1=1"]
        params = []
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%dT%H:%M')
            conditions.append("time >= %s")
            params.append(date_from)
            
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%dT%H:%M')
            conditions.append("time <= %s")
            params.append(date_to)
            
        if status and status.lower() != 'all':
            conditions.append("status = %s")
            params.append(status)
            
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT time, status, features
            FROM predictions
            WHERE {where_clause}
            ORDER BY time DESC
        """
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Prepare data for CSV
        data = []
        for row in results:
            probabilities = {
                'normal': 0,
                'rung_12_5': 0,
                'rung_6': 0,
                'stop': 0
            }
            
            if row['features']:
                features = json.loads(row['features'])
                if isinstance(features, dict):
                    if 'probabilities' in features:
                        probabilities = features['probabilities']
                    elif all(key in features for key in probabilities.keys()):
                        probabilities = {k: float(features[k]) for k in probabilities.keys()}
            
            data.append({
                'Time': row['time'].strftime("%Y-%m-%d %H:%M:%S"),
                'Status': row['status'].upper(),
                'Normal Probability': f"{probabilities['normal']*100:.2f}%",
                'Rung 12.5Hz Probability': f"{probabilities['rung_12_5']*100:.2f}%",
                'Rung 6Hz Probability': f"{probabilities['rung_6']*100:.2f}%",
                'Stop Probability': f"{probabilities['stop']*100:.2f}%",
                'Confidence': f"{max(probabilities.values())*100:.2f}%"
            })
        
        cursor.close()
        conn.close()
        
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

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000) 