from flask import Flask, render_template, jsonify, send_file, request
from database_reader import DatabaseReader
import json
from datetime import datetime, timedelta
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

STATUS_COLORS = {
    'normal': '#28a745',    # Green
    'rung_6': '#ffc107',    # Yellow
    'rung_12_5': '#dc3545', # Red
    'stop': '#6c757d'       # Gray
}

STATUS_LABELS = {
    'normal': 'Bình thường',
    'rung_6': 'Lỗi 1(rung nhẹ)',
    'rung_12_5': 'Lỗi 2(rung nặng)',
    'stop': 'Dừng'
}

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(obj, timedelta):
            return str(obj)
        return super().default(obj)

def format_datetime(dt):
    """Helper function to format datetime objects consistently"""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def get_pump_status():
    try:
        db = DatabaseReader()
        latest_predictions = db.get_recent_predictions(limit=1)
        
        status = {
            'pump1': {
                'status': 'Unknown',
                'status_label': 'Không xác định',
                'color': '#6c757d',
                'last_updated': None,
                'probabilities': {
                    'normal': 0,
                    'rung_6': 0,
                    'rung_12_5': 0,
                    'stop': 0
                }
            }
        }
        
        if latest_predictions:
            latest = latest_predictions[0]
            status['pump1'] = {
                'status': latest['status'],
                'status_label': STATUS_LABELS[latest['status']],
                'color': STATUS_COLORS[latest['status']],
                'last_updated': format_datetime(latest['time']),
                'probabilities': {
                    'normal': latest['normal_prob'],
                    'rung_6': latest['rung_6_prob'],
                    'rung_12_5': latest['rung_12_5_prob'],
                    'stop': latest['stop_prob']
                }
            }
        
        return status
    except Exception as e:
        app.logger.error(f"Error in get_pump_status: {str(e)}")
        return status

@app.route('/')
def index():
    try:
        db = DatabaseReader()
        latest_predictions = db.get_recent_predictions(limit=10)
        pump_status = get_pump_status()
        daily_stats = db.get_daily_stats(days=7)
        
        # Format datetime objects in latest_predictions
        for pred in latest_predictions:
            pred['time'] = format_datetime(pred['time'])
            
        # Format datetime objects in daily_stats
        for stat in daily_stats:
            stat['date'] = format_datetime(stat['date'])
            
        return render_template('dashboard.html', 
                             predictions=latest_predictions, 
                             pump_status=pump_status,
                             daily_stats=daily_stats,
                             status_colors=STATUS_COLORS,
                             status_labels=STATUS_LABELS)
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/history')
def history():
    return render_template('history.html',
                         status_colors=STATUS_COLORS,
                         status_labels=STATUS_LABELS)

@app.route('/api/latest')
def get_latest():
    try:
        db = DatabaseReader()
        latest_predictions = db.get_recent_predictions(limit=10)
        # Format datetime objects before serialization
        for pred in latest_predictions:
            pred['time'] = format_datetime(pred['time'])
        return jsonify(latest_predictions)
    except Exception as e:
        app.logger.error(f"Error in get_latest: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    try:
        status = get_pump_status()
        return jsonify(status)
    except Exception as e:
        app.logger.error(f"Error in get_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-stats')
def get_daily_stats():
    try:
        db = DatabaseReader()
        stats = db.get_daily_stats(days=7)
        # Format datetime objects before serialization
        for stat in stats:
            stat['date'] = format_datetime(stat['date'])
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Error in get_daily_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmap-data')
def get_heatmap_data():
    try:
        db = DatabaseReader()
        data = db.get_hourly_heatmap(days=7)
        # Format datetime objects before serialization
        for item in data:
            item['date'] = format_datetime(item['date'])
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error in get_heatmap_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history-data')
def get_history_data():
    try:
        db = DatabaseReader()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status_filter = request.args.get('status')
        
        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        predictions = db.get_predictions_by_timerange(start_date, end_date)
        
        if status_filter and status_filter != 'all':
            predictions = [p for p in predictions if p['status'] == status_filter]
        
        # Sort predictions by time in descending order (newest first)
        predictions.sort(key=lambda x: x['time'], reverse=True)
        
        # Format datetime objects before serialization
        for pred in predictions:
            pred['time'] = format_datetime(pred['time'])
        
        return jsonify(predictions)
    except Exception as e:
        app.logger.error(f"Error in get_history_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-csv')
def export_csv():
    try:
        db = DatabaseReader()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status_filter = request.args.get('status')

        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        predictions = db.get_predictions_by_timerange(start_date, end_date)
        
        if status_filter and status_filter != 'all':
            predictions = [p for p in predictions if p['status'] == status_filter]
        
        # Format datetime objects before creating DataFrame
        for pred in predictions:
            pred['time'] = format_datetime(pred['time'])
        
        # Chuyển thành DataFrame
        df = pd.DataFrame(predictions)
        
        # Tạo buffer để lưu file CSV
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, encoding='utf-8-sig')  # Use UTF-8 with BOM for Excel compatibility
        buffer.seek(0)
        
        filename = f'pump_predictions_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
        
        return send_file(
            io.BytesIO(buffer.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        app.logger.error(f"Error in export_csv: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-report')
def export_report():
    try:
        db = DatabaseReader()
        predictions = db.get_recent_predictions(limit=1000)
        stats = db.get_daily_stats(days=7)
        heatmap_data = db.get_hourly_heatmap(days=7)

        # Format datetime objects before creating DataFrames
        for pred in predictions:
            pred['time'] = format_datetime(pred['time'])
        for stat in stats:
            stat['date'] = format_datetime(stat['date'])
        for item in heatmap_data:
            item['date'] = format_datetime(item['date'])

        # Tạo DataFrame cho heatmap
        heatmap_df = pd.DataFrame(heatmap_data)
        pivot_table = heatmap_df.pivot(index='date', columns='hour', values='stop_count')

        # Tạo PDF report với matplotlib
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Heatmap
        plt.subplot(2, 1, 1)
        sns.heatmap(pivot_table, cmap='YlOrRd', annot=True, fmt='.0f')
        plt.title('Stop Events Heatmap')
        
        # Plot 2: Daily Stats
        stats_df = pd.DataFrame(stats)
        plt.subplot(2, 1, 2)
        stats_df.plot(x='date', y=['stop_count', 'rung_6_count', 'rung_12_5_count'])
        plt.title('Daily Statistics')
        
        # Lưu vào buffer
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
        app.logger.error(f"Error in export_report: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 