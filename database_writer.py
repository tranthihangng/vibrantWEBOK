import mysql.connector
from datetime import datetime
import json

class DatabaseWriter:
    def __init__(self):
        # MySQL connection configuration
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',  # Change password if needed
            'database': 'pump_monitoring'
        }
        self.init_database()

    def init_database(self):
        """Initialize database and tables if they don't exist"""
        try:
            # Connect to MySQL Server
            conn = mysql.connector.connect(
                host=self.config['host'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()

            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
            cursor.execute(f"USE {self.config['database']}")

            # Create predictions table with new structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    time DATETIME,
                    status VARCHAR(50),
                    stop_prob FLOAT,
                    normal_prob FLOAT,
                    rung_6_prob FLOAT,
                    rung_12_5_prob FLOAT,
                    sensor_data JSON,
                    prediction_time_ms FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database initialized successfully")

        except mysql.connector.Error as err:
            print(f"❌ Error initializing database: {err}")

    def save_prediction(self, status, probabilities, sensor_data=None, prediction_time_ms=None):
        """Save prediction results to database"""
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()

            query = """
                INSERT INTO predictions 
                (time, status, stop_prob, normal_prob, rung_6_prob, rung_12_5_prob, 
                sensor_data, prediction_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Convert sensor_data to JSON string if provided
            sensor_data_json = json.dumps(sensor_data) if sensor_data else None
            
            # Extract probabilities
            # probabilities list order: [normal, rung_12_5, rung_6, stop]
            normal_prob = probabilities[0]
            rung_12_5_prob = probabilities[1]
            rung_6_prob = probabilities[2]
            stop_prob = probabilities[3]
            
            values = (
                datetime.now(),  # time
                status,
                stop_prob,
                normal_prob,
                rung_6_prob,
                rung_12_5_prob,
                sensor_data_json,
                prediction_time_ms
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            cursor.close()
            conn.close()
            return True

        except mysql.connector.Error as err:
            print(f"❌ Error saving prediction: {err}")
            return False 