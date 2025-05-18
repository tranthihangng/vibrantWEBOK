# import mysql.connector
# from datetime import datetime
# import json

# class DatabaseHandler:
#     def __init__(self):
#         # MySQL connection configuration
#         self.config = {
#             'host': 'localhost',
#             'user': 'root',
#             'password': '123456',  # Change password if needed
#             'database': 'pump_monitoring'
#         }
#         self.init_database()

#     def init_database(self):
#         """Initialize database and tables if they don't exist"""
#         try:
#             # Connect to MySQL Server
#             conn = mysql.connector.connect(
#                 host=self.config['host'],
#                 user=self.config['user'],
#                 password=self.config['password']
#             )
#             cursor = conn.cursor()

#             # Create database if not exists
#             cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
#             cursor.execute(f"USE {self.config['database']}")

#             # Create predictions table with new structure
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS predictions (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     time DATETIME,
#                     status VARCHAR(50),
#                     stop_prob FLOAT,
#                     normal_prob FLOAT,
#                     rung_6_prob FLOAT,
#                     rung_12_5_prob FLOAT,
#                     sensor_data JSON,
#                     prediction_time_ms FLOAT,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 );
#             """)

#             conn.commit()
#             cursor.close()
#             conn.close()
#             print("✅ Database initialized successfully")

#         except mysql.connector.Error as err:
#             print(f"❌ Error initializing database: {err}")

#     def save_prediction(self, status, probabilities, sensor_data=None, prediction_time_ms=None):
#         """Save prediction results to database"""
#         try:
#             conn = mysql.connector.connect(**self.config)
#             cursor = conn.cursor()

#             query = """
#                 INSERT INTO predictions 
#                 (time, status, stop_prob, normal_prob, rung_6_prob, rung_12_5_prob, 
#                 sensor_data, prediction_time_ms)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """
            
#             # Convert sensor_data to JSON string if provided
#             sensor_data_json = json.dumps(sensor_data) if sensor_data else None
            
#             # Extract probabilities
#             # probabilities list order: [normal, rung_12_5, rung_6, stop]
#             normal_prob = probabilities[0]
#             rung_12_5_prob = probabilities[1]
#             rung_6_prob = probabilities[2]
#             stop_prob = probabilities[3]
            
#             values = (
#                 datetime.now(),  # time
#                 status,
#                 stop_prob,
#                 normal_prob,
#                 rung_6_prob,
#                 rung_12_5_prob,
#                 sensor_data_json,
#                 prediction_time_ms
#             )
            
#             cursor.execute(query, values)
#             conn.commit()
            
#             cursor.close()
#             conn.close()
#             return True

#         except mysql.connector.Error as err:
#             print(f"❌ Error saving prediction: {err}")
#             return False

#     def get_recent_predictions(self, limit=10):
#         """Get most recent predictions"""
#         try:
#             conn = mysql.connector.connect(**self.config)
#             cursor = conn.cursor(dictionary=True)

#             query = """
#                 SELECT * FROM predictions 
#                 ORDER BY time DESC 
#                 LIMIT %s
#             """
#             cursor.execute(query, (limit,))
#             results = cursor.fetchall()

#             # Convert JSON string to dict
#             for row in results:
#                 if row['sensor_data']:
#                     row['sensor_data'] = json.loads(row['sensor_data'])

#             cursor.close()
#             conn.close()
#             return results

#         except mysql.connector.Error as err:
#             print(f"❌ Error querying data: {err}")
#             return []

#     def get_predictions_by_timerange(self, start_time, end_time):
#         """Get predictions within a time range"""
#         try:
#             conn = mysql.connector.connect(**self.config)
#             cursor = conn.cursor(dictionary=True)

#             query = """
#                 SELECT * FROM predictions 
#                 WHERE time BETWEEN %s AND %s
#                 ORDER BY time ASC
#             """
#             cursor.execute(query, (start_time, end_time))
#             results = cursor.fetchall()

#             for row in results:
#                 if row['sensor_data']:
#                     row['sensor_data'] = json.loads(row['sensor_data'])

#             cursor.close()
#             conn.close()
#             return results

#         except mysql.connector.Error as err:
#             print(f"❌ Error querying data: {err}")
#             return []

#     def get_daily_stats(self, days=7):
#         """Get daily statistics"""
#         try:
#             conn = mysql.connector.connect(**self.config)
#             cursor = conn.cursor(dictionary=True)

#             query = """
#                 SELECT 
#                     DATE(time) as date,
#                     COUNT(*) as total_predictions,
#                     SUM(CASE WHEN status = 'stop' THEN 1 ELSE 0 END) as stop_count,
#                     SUM(CASE WHEN status = 'rung_6' THEN 1 ELSE 0 END) as rung_6_count,
#                     SUM(CASE WHEN status = 'rung_12_5' THEN 1 ELSE 0 END) as rung_12_5_count,
#                     AVG(normal_prob) as avg_normal_prob,
#                     AVG(prediction_time_ms) as avg_prediction_time
#                 FROM predictions 
#                 WHERE time >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
#                 GROUP BY DATE(time)
#                 ORDER BY date DESC
#             """
#             cursor.execute(query, (days,))
#             results = cursor.fetchall()

#             cursor.close()
#             conn.close()
#             return results

#         except mysql.connector.Error as err:
#             print(f"❌ Error querying statistics: {err}")
#             return []

#     def get_hourly_heatmap(self, days=7):
#         """Lấy dữ liệu cho heatmap theo giờ"""
#         try:
#             conn = mysql.connector.connect(**self.config)
#             cursor = conn.cursor(dictionary=True)

#             query = """
#                 SELECT 
#                     HOUR(created_at) as hour,
#                     DATE(created_at) as date,
#                     COUNT(*) as total_count,
#                     SUM(CASE WHEN status = 'stop' THEN 1 ELSE 0 END) as stop_count
#                 FROM predictions 
#                 WHERE created_at >= DATE_SUB(CURRENT_DATE, INTERVAL %s DAY)
#                 GROUP BY DATE(created_at), HOUR(created_at)
#                 ORDER BY date DESC, hour ASC
#             """
#             cursor.execute(query, (days,))
#             results = cursor.fetchall()

#             cursor.close()
#             conn.close()
#             return results

#         except mysql.connector.Error as err:
#             print(f"❌ Lỗi khi truy vấn dữ liệu heatmap: {err}")
#             return []