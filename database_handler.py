from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import pandas as pd
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def insert_data(self, data):
        """
        Insert data into Supabase
        data: dictionary containing the data to insert
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
                
            # Insert data into the 'sensor_data' table
            result = self.supabase.table('sensor_data').insert(data).execute()
            return True, "Data inserted successfully"
        except Exception as e:
            return False, f"Error inserting data: {str(e)}"
    
    def get_latest_data(self, limit=10):
        """
        Get the latest records from the database
        limit: number of records to return
        """
        try:
            result = self.supabase.table('sensor_data')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(result.data)
            return True, df
        except Exception as e:
            return False, f"Error fetching data: {str(e)}"
    
    def get_data_by_timerange(self, start_time, end_time):
        """
        Get data within a specific time range
        start_time, end_time: datetime objects
        """
        try:
            result = self.supabase.table('sensor_data')\
                .select('*')\
                .gte('timestamp', start_time.isoformat())\
                .lte('timestamp', end_time.isoformat())\
                .execute()
            
            df = pd.DataFrame(result.data)
            return True, df
        except Exception as e:
            return False, f"Error fetching data: {str(e)}"