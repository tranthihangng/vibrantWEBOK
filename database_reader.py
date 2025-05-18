import mysql.connector
import json

class DatabaseReader:
    def __init__(self):
        # MySQL connection configuration
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',  # Change password if needed
            'database': 'pump_monitoring'
        }

    def get_recent_predictions(self, limit=10):
        """Get most recent predictions"""
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT * FROM predictions 
                ORDER BY time DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()

            # Convert JSON string to dict
            for row in results:
                if row['sensor_data']:
                    row['sensor_data'] = json.loads(row['sensor_data'])

            cursor.close()
            conn.close()
            return results

        except mysql.connector.Error as err:
            print(f"❌ Error querying data: {err}")
            return []

    def get_predictions_by_timerange(self, start_time, end_time):
        """Get predictions within a time range"""
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT * FROM predictions 
                WHERE time BETWEEN %s AND %s
                ORDER BY time DESC
            """
            cursor.execute(query, (start_time, end_time))
            results = cursor.fetchall()

            for row in results:
                if row['sensor_data']:
                    row['sensor_data'] = json.loads(row['sensor_data'])

            cursor.close()
            conn.close()
            return results

        except mysql.connector.Error as err:
            print(f"❌ Error querying data: {err}")
            return []

    def get_daily_stats(self, days=7):
        """Get daily statistics"""
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    DATE(time) as date,
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN status = 'stop' THEN 1 ELSE 0 END) as stop_count,
                    SUM(CASE WHEN status = 'rung_6' THEN 1 ELSE 0 END) as rung_6_count,
                    SUM(CASE WHEN status = 'rung_12_5' THEN 1 ELSE 0 END) as rung_12_5_count,
                    AVG(normal_prob) as avg_normal_prob,
                    AVG(prediction_time_ms) as avg_prediction_time
                FROM predictions 
                WHERE time >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
                GROUP BY DATE(time)
                ORDER BY date DESC
            """
            cursor.execute(query, (days,))
            results = cursor.fetchall()

            cursor.close()
            conn.close()
            return results

        except mysql.connector.Error as err:
            print(f"❌ Error querying statistics: {err}")
            return []

    def get_hourly_heatmap(self, days=7):
        """Get hourly heatmap data"""
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    HOUR(time) as hour,
                    DATE(time) as date,
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status = 'stop' THEN 1 ELSE 0 END) as stop_count,
                    SUM(CASE WHEN status = 'rung_6' THEN 1 ELSE 0 END) as rung_6_count,
                    SUM(CASE WHEN status = 'rung_12_5' THEN 1 ELSE 0 END) as rung_12_5_count
                FROM predictions 
                WHERE time >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
                GROUP BY DATE(time), HOUR(time)
                ORDER BY date DESC, hour ASC
            """
            cursor.execute(query, (days,))
            results = cursor.fetchall()

            cursor.close()
            conn.close()
            return results

        except mysql.connector.Error as err:
            print(f"❌ Error querying heatmap data: {err}")
            return [] 