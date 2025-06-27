from flask import Flask, request, jsonify
import csv
from datetime import datetime
import os

app = Flask(__name__)
 
def create_csv_file():
    # Tạo headers cho file CSV
    headers = [f"feature{i+1}" for i in range(54)] + ["state"]
    
    # Tạo file CSV nếu chưa tồn tại
    filename = 'f_normal.csv'
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
    return filename

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        # Nhận dữ liệu JSON
        data = request.get_json()

        # Kiểm tra dữ liệu là list
        if not isinstance(data, list):
            return jsonify({'error': 'Expected a JSON array'}), 400

        # Kiểm tra độ dài của dữ liệu
        if len(data) != 54:
            return jsonify({'error': f'Expected 36 features, got {len(data)}'}), 400

        print("Received array:", data)

        # Thêm trạng thái "normal" vào cuối
        data.append("normal")

        # Lưu vào file CSV
        filename = create_csv_file()
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

        return jsonify({
            'message': 'Data received and saved successfully',
            'features': len(data) - 1,  # Trừ đi cột state
            'state': 'normal'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Tạo file CSV với headers khi khởi động
    create_csv_file()
    # Chạy Flask server
    app.run(host='0.0.0.0', port=5000)
