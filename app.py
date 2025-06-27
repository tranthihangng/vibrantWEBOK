from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime, timedelta
import pandas as pd
import io
import threading
import time
from database_handler import DatabaseHandler

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread for real-time updates
thread = None
thread_lock = threading.Lock()

def get_pump_status():
    try:
        db = DatabaseHandler()
        success, result = db.get_latest_data(limit=1)
        
        if not success or result.empty:
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
        
        latest = result.iloc[0]
        
        return {
            'status': latest['status'].upper(),
            'last_updated': latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            'probabilities': {
                'normal': float(latest['normal_prob']),
                'rung_12_5': float(latest['rung_12_5_prob']),
                'rung_6': float(latest['rung_6_prob']),
                'stop': float(latest['stop_prob'])
            }
        }
    except Exception as e:
        print(f"Error getting pump status: {e}")
        return {
            'status': 'ERROR',
            'last_updated': None,
            'probabilities': {
                'normal': 0,
                'rung_12_5': 0,
                'rung_6': 0,
                'stop': 0
            }
        }

def get_daily_stats():
    try:
        db = DatabaseHandler()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        success, result = db.get_data_by_timerange(today, tomorrow)
        
        if not success:
            return None
            
        stats = {
            'total': len(result),
            'normal': len(result[result['status'] == 'normal']),
            'minor_faults': len(result[result['status'] == 'rung_6']),
            'major_faults': len(result[result['status'] == 'rung_12_5'])
        }
        
        return stats
    except Exception as e:
        print(f"Error getting daily stats: {e}")
        return None

def background_thread():
    """Thread that handles real-time updates"""
    while True:
        try:
            # Get latest status
            status_data = get_pump_status()
            if status_data:
                socketio.emit('status_update', status_data)
            
            # Get daily stats
            stats = get_daily_stats()
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
    status = get_pump_status()
    stats = get_daily_stats()
    
    # Format the pump status data structure
    pump_status = {
        'pump1': {
            'status': status['status'],
            'last_updated': status['last_updated'],
            'probabilities': status['probabilities']
        }
    }
    
    # Get recent predictions for the predictions table
    try:
        db = DatabaseHandler()
        success, result = db.get_latest_data(limit=10)
        predictions = []
        if success and not result.empty:
            for _, row in result.iterrows():
                predictions.append({
                    'id': row.name,  # Using index as ID
                    'time': row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    'status': row['status'].upper()
                })
    except Exception as e:
        print(f"Error getting predictions: {e}")
        predictions = []
    
    return render_template('index.html', 
                         pump_status=pump_status,
                         predictions=predictions,
                         daily_stats=stats)

@app.route('/history')
def history():
    """Render history page"""
    return render_template('history.html')

@app.route('/api/history')
def get_history():
    """API endpoint for history data"""
    try:
        db = DatabaseHandler()
        page = int(request.args.get('page', 1))
        limit = 50  # Records per page
        offset = (page - 1) * limit
        
        success, result = db.get_latest_data(limit=limit)
        
        if not success:
            return jsonify({'error': 'Failed to fetch history'}), 500
            
        return jsonify({
            'data': result.to_dict('records'),
            'page': page,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-csv')
def export_csv():
    try:
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        if not date_from or not date_to:
            return jsonify({'error': 'Date range required'}), 400
            
        date_from = datetime.strptime(date_from, '%Y-%m-%dT%H:%M')
        date_to = datetime.strptime(date_to, '%Y-%m-%dT%H:%M')
        
        db = DatabaseHandler()
        success, result = db.get_data_by_timerange(date_from, date_to)
        
        if not success:
            return jsonify({'error': 'Failed to fetch data'}), 500
            
        # Convert to CSV
        output = io.StringIO()
        result.to_csv(output, index=False)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'pump_data_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest')
def get_latest_predictions():
    """API endpoint for getting latest predictions"""
    try:
        db = DatabaseHandler()
        success, result = db.get_latest_data(limit=10)
        
        if not success:
            return jsonify({'error': 'Failed to fetch latest predictions'}), 500
            
        predictions = []
        for _, row in result.iterrows():
            predictions.append({
                'id': row.name,  # Using index as ID
                'time': row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                'status': row['status'].upper(),
                'normal_prob': float(row['normal_prob']),
                'fault_prob': float(row['rung_12_5_prob'] + row['rung_6_prob'])  # Combined fault probability
            })
            
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """API endpoint for getting current status"""
    try:
        status = get_pump_status()
        if not status:
            return jsonify({'error': 'Failed to get status'}), 500
            
        # Format the pump status data structure
        pump_status = {
            'pump1': {
                'status': status['status'],
                'last_updated': status['last_updated'],
                'probabilities': status['probabilities']
            }
        }
        return jsonify(pump_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True) 