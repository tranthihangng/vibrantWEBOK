import mysql.connector
from supabase import create_client
import os
from datetime import datetime
import time
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv('supabase.env')

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in supabase.env file")

# MySQL configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'pump_monitoring'
}

def get_mysql_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

def get_last_sync_time():
    try:
        with open('last_sync.txt', 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    except:
        return datetime(2000, 1, 1)  # If no sync time found, sync all data

def save_sync_time(sync_time):
    with open('last_sync.txt', 'w') as f:
        f.write(sync_time.isoformat())

def sync_to_supabase():
    try:
        # Initialize Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get MySQL connection
        mysql_conn = get_mysql_connection()
        cursor = mysql_conn.cursor(dictionary=True)
        
        # Get last sync time
        last_sync = get_last_sync_time()
        current_time = datetime.now()
        
        # Get new records from MySQL
        query = """
            SELECT 
                time as timestamp,
                status,
                stop_prob,
                normal_prob,
                rung_6_prob,
                rung_12_5_prob,
                prediction_time_ms
            FROM predictions 
            WHERE time > %s
            ORDER BY time ASC
        """
        cursor.execute(query, (last_sync,))
        records = cursor.fetchall()
        
        if not records:
            print("No new records to sync")
            return
            
        # Process records for Supabase
        supabase_records = []
        for record in records:
            supabase_record = {
                'timestamp': record['timestamp'].isoformat(),
                'status': record['status'],
                'normal_prob': float(record['normal_prob']),
                'rung_12_5_prob': float(record['rung_12_5_prob']),
                'rung_6_prob': float(record['rung_6_prob']),
                'stop_prob': float(record['stop_prob']),
                'prediction_time_ms': record['prediction_time_ms']
            }
            supabase_records.append(supabase_record)
        
        # Insert records into Supabase in batches
        batch_size = 100
        for i in range(0, len(supabase_records), batch_size):
            batch = supabase_records[i:i + batch_size]
            result = supabase.table('sensor_data').insert(batch).execute()
            print(f"Synced batch {i//batch_size + 1} of {(len(supabase_records)-1)//batch_size + 1}")
        
        # Update last sync time
        save_sync_time(current_time)
        print(f"Successfully synced {len(supabase_records)} records")
        
    except Exception as e:
        print(f"Error during sync: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'mysql_conn' in locals():
            mysql_conn.close()

def run_continuous_sync(interval_seconds=60):
    """
    Run the sync process continuously with a specified interval
    """
    print(f"Starting continuous sync with {interval_seconds} seconds interval")
    while True:
        print(f"\nSync started at {datetime.now()}")
        sync_to_supabase()
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_continuous_sync() 