# predict_manual_input.py

import numpy as np
import joblib
import time
from datetime import datetime
import os
from database_writer import DatabaseWriter
from flask import Flask, request, jsonify
from telegram_notifier import TelegramNotifier
import json
import threading

# Khởi tạo Flask app
app = Flask(__name__)

# === Load mô hình và scaler đã lưu ===
model = joblib.load("practical_mlp_best_model.joblib")
scaler = joblib.load("practical_scaler.joblib")

print("📌 Các nhãn lớp:", model.classes_)

# Khởi tạo Telegram notifier
telegram = TelegramNotifier()
last_notification_time = 0
NOTIFICATION_INTERVAL = 120  # 2 phút = 120 giây

# Biến để kiểm soát timeout
last_data_received = 0
ESP32_TIMEOUT = 50  # 50 giây timeout


@app.route('/predict', methods=['POST'])
def receive_data():
    """Nhận dữ liệu từ client qua HTTP POST"""
    try:
        global last_data_received
        last_data_received = time.time()
        
        # Nhận dữ liệu JSON
        data = request.get_json()
        
        # Kiểm tra dữ liệu có tồn tại không
        if data is None:
            print("❌ Không nhận được dữ liệu")
            return jsonify({'error': 'No data received'}), 400

        # Kiểm tra dữ liệu là list
        if not isinstance(data, list):
            print("❌ Dữ liệu không phải là mảng")
            return jsonify({'error': 'Expected a JSON array'}), 400

        # Kiểm tra độ dài của dữ liệu (31 đặc trưng giống trong pred.py)
        expected_features = 54
        if len(data) != expected_features:
            print(f"❌ Số lượng đặc trưng không đúng: nhận {len(data)}, cần {expected_features}")
            return jsonify({'error': f'Expected {expected_features} features, got {len(data)}'}), 400

        print(f"📥 Dữ liệu nhận được từ ESP32: {data}")

        # Chuyển đổi dữ liệu thành float
        try:
            sensor_values = [float(val) for val in data]
        except (ValueError, TypeError) as e:
            print(f"❌ Lỗi định dạng dữ liệu: {str(e)}")
            return jsonify({'error': f'Invalid data format: {str(e)}'}), 400

        # Dự đoán
        prediction_result = predict_values(sensor_values)
        
        if prediction_result:
            return jsonify({
                'message': 'Prediction successful',
                'status': prediction_result['status'],
                'confidence': prediction_result['confidence'],
                'probabilities': prediction_result['probabilities']
            }), 200
        else:
            return jsonify({'error': 'Prediction failed'}), 500

    except Exception as e:
        print(f"❌ Lỗi khi nhận dữ liệu: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/data', methods=['POST'])
def receive_data_alt():
    """Endpoint bổ sung để nhận dữ liệu từ ESP32 thông qua /data"""
    return receive_data()  # Sử dụng lại hàm xử lý của /predict

def check_esp32_timeout():
    """Hàm kiểm tra nếu ESP32 không gửi dữ liệu trong 50 giây"""
    global last_data_received
    
    while True:
        current_time = time.time()
        if last_data_received > 0:  # Nếu đã nhận dữ liệu trước đó
            time_since_last = current_time - last_data_received
            if time_since_last > ESP32_TIMEOUT:
                print(f"⚠️ ESP32 TIMEOUT: Không nhận được dữ liệu trong {ESP32_TIMEOUT} giây")
                # Có thể thêm thông báo qua Telegram nếu cần
                last_data_received = current_time  # Reset để không báo liên tục
        
        time.sleep(5)  # Kiểm tra mỗi 5 giây

def get_status_from_probabilities(probabilities):
    """Hàm chuyển đổi xác suất thành trạng thái"""
    predicted_class = np.argmax(probabilities)
    prob_value = probabilities[predicted_class]
    
    # Ánh xạ index sang tên trạng thái
    status_mapping = {
        0: 'normal',
        1: 'rung_12_5',
        2: 'rung_6',
        3: 'stop'
    }
    
    return status_mapping[predicted_class]

def predict_values(sensor_values):
    """Hàm dự đoán từ giá trị cảm biến"""
    global last_notification_time
    
    try:
        current_time = time.time()
        time_since_last = current_time - last_notification_time

        # In ra dữ liệu gốc để debug
        print(f"📊 Dữ liệu cảm biến nhận được: {sensor_values}")
        print(f"📏 Số lượng đặc trưng: {len(sensor_values)}")

        # Chuyển thành mảng numpy và reshape
        try:
            X_input = np.array(sensor_values, dtype=np.float32).reshape(1, -1)
            print(f"✅ Chuyển đổi dữ liệu thành công: shape={X_input.shape}")
        except Exception as e:
            print(f"❌ Lỗi khi chuyển đổi dữ liệu sang numpy array: {e}")
            raise

        # Chuẩn hóa và dự đoán
        try:
            X_scaled = scaler.transform(X_input)
            print(f"✅ Chuẩn hóa dữ liệu thành công: shape={X_scaled.shape}")
        except Exception as e:
            print(f"❌ Lỗi khi chuẩn hóa dữ liệu: {e}")
            raise
        
        # Đo thời gian dự đoán
        start_time = time.time()
        try:
            probabilities = model.predict_proba(X_scaled)[0]
            print(f"✅ Dự đoán thành công: shape={probabilities.shape}")
        except Exception as e:
            print(f"❌ Lỗi khi dự đoán: {e}")
            raise
            
        end_time = time.time()
        elapsed_time_ms = (end_time - start_time) * 1000

        # Xử lý kết quả
        try:
            status = get_status_from_probabilities(probabilities)
            print(f"✅ Xác định trạng thái thành công: {status}")
        except Exception as e:
            print(f"❌ Lỗi khi xác định trạng thái: {e}")
            raise
        
        print(f"\n⏱️ [{datetime.now()}] Đã dự đoán xong")
        print(f"   Thời gian tính toán: {elapsed_time_ms:.3f} ms")
        print(f"   Trạng thái: {status}")
        print(f"   Xác suất:")
        print(f"   - Normal: {probabilities[0]:.3f}")
        print(f"   - Rung 12.5: {probabilities[1]:.3f}")
        print(f"   - Rung 6: {probabilities[2]:.3f}")
        print(f"   - Stop: {probabilities[3]:.3f}")
        
        # Lưu vào database
        db = DatabaseWriter()
        success = db.save_prediction(
            status=status,
            probabilities=probabilities.tolist(),
            sensor_data=sensor_values,
            prediction_time_ms=elapsed_time_ms
        )
        
        if success:
            print(f"✅ Đã lưu trạng thái vào database: {status}")
        else:
            print(f"❌ Lỗi khi lưu vào database")

        # Gửi thông báo Telegram mỗi 2 phút
        if time_since_last >= NOTIFICATION_INTERVAL:
            try:
                print(f"📱 Đang gửi thông báo đến Telegram...")
                telegram.send_notification(status)
                last_notification_time = current_time
                print(f"✅ Đã gửi thông báo thành công!")
            except Exception as e:
                print(f"❌ Lỗi khi gửi thông báo Telegram: {str(e)}")

        return {
            'status': status,
            'confidence': float(max(probabilities)),
            'probabilities': probabilities.tolist()
        }

    except Exception as e:
        print(f"❌ Lỗi trong quá trình dự đoán: {str(e)}")
        print(f"Chi tiết lỗi:", e.__class__.__name__)
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    print(f"📱 Thông báo Telegram sẽ được gửi mỗi {NOTIFICATION_INTERVAL} giây")
    print(f"⏱️ Timeout ESP32: {ESP32_TIMEOUT} giây")
    
    # Khởi chạy thread kiểm tra timeout
    timeout_thread = threading.Thread(target=check_esp32_timeout, daemon=True)
    timeout_thread.start()
    
    # Chạy Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)


