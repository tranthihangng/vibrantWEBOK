# import pandas as pd
# from database_handler import DatabaseHandler
# import time
# from datetime import datetime
# import os

# def monitor_and_save_predictions(pred_file="pred.csv", interval=5):
#     """
#     Theo dõi file pred.csv và lưu kết quả vào database
#     Args:
#         pred_file: Đường dẫn đến file chứa kết quả dự đoán
#         interval: Thời gian giữa các lần kiểm tra (giây)
#     """
#     # Khởi tạo kết nối database
#     db = DatabaseHandler()
    
#     print(f"🔄 Bắt đầu theo dõi file {pred_file}")
#     print(f"⏱️ Kiểm tra mỗi {interval} giây")
    
#     # Lưu thời gian sửa đổi cuối cùng
#     last_modified = 0
    
#     while True:
#         try:
#             # Kiểm tra xem file có thay đổi không
#             try:
#                 current_modified = os.path.getmtime(pred_file)
#             except FileNotFoundError:
#                 print(f"❌ Không tìm thấy file {pred_file}")
#                 time.sleep(interval)
#                 continue
                
#             if current_modified > last_modified:
#                 # Đọc kết quả dự đoán
#                 try:
#                     pred_data = pd.read_csv(pred_file)
#                     latest_pred = pred_data.iloc[-1]  # Lấy dự đoán mới nhất
                    
#                     # Chuyển đổi kết quả dự đoán thành trạng thái
#                     status = "fault" if latest_pred['prediction'] == 1 else "normal"
                    
#                     # Lưu vào database
#                     success = db.save_prediction(status=status)
                    
#                     if success:
#                         print(f"✅ [{datetime.now()}] Đã lưu trạng thái: {status}")
#                     else:
#                         print(f"❌ [{datetime.now()}] Lỗi khi lưu trạng thái")
                        
#                     last_modified = current_modified
                    
#                 except pd.errors.EmptyDataError:
#                     print(f"⚠️ File {pred_file} trống")
#                 except Exception as e:
#                     print(f"❌ Lỗi khi đọc file: {e}")
            
#             time.sleep(interval)
            
#         except KeyboardInterrupt:
#             print("\n👋 Dừng theo dõi")
#             break
#         except Exception as e:
#             print(f"❌ Lỗi không mong muốn: {e}")
#             time.sleep(interval)

# if __name__ == "__main__":
#     monitor_and_save_predictions() 