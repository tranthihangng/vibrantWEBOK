# Pump Monitoring System

A web application for monitoring pump/motor states, providing real-time visualization of sensor data and prediction results.

## Features

- **Authentication system** with login and registration
- **Dashboard** showing real-time pump status, charts, and statistics
- **History page** for viewing historical data with filtering and export options
- **Export capabilities** for CSV and PDF reports
- **Real-time updates** with automatic dashboard refreshing

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Charting**: Chart.js
- **Tables**: DataTables
- **Reporting**: Pandas, Matplotlib, Seaborn

## Setup Instructions

### Prerequisites

- Python 3.7+
- MySQL server
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone [repository_url]
   cd [repository_directory]
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the MySQL database:
   - Create a MySQL user (or use an existing one)
   - Update the database configuration in `database_handler.py`
   - Run the schema script: `mysql -u your_user -p < schema.sql`
   - Or let the application create the database structures automatically

5. Run the application:
   ```
   python app.py
   ```

6. Access the application at http://localhost:5000

### Default Login

- Username: admin
- Password: admin

## Project Structure

- **app.py** - Main Flask application
- **database_handler.py** - Database operations handler
- **templates/** - HTML templates
  - **base.html** - Base template with navigation
  - **login.html** - Login and registration forms
  - **dashboard.html** - Main dashboard display
  - **history.html** - History and export view
- **static/** - Static assets (CSS, JS)
- **schema.sql** - Database schema definition

## API Endpoints

- `/api/latest` - Get latest predictions
- `/api/status` - Get current pump status
- `/api/daily-stats` - Get daily statistics
- `/api/export-csv` - Export data as CSV
- `/api/export-report` - Export PDF report

## Security Considerations

- Passwords are hashed using bcrypt
- Session management for authentication
- Input validation for all forms
- Login required for all sensitive operations 