# ============================================
#  generator.py  –  AI Data Generator v1.3
#  Sinh dữ liệu giao thông giả lập cho Đà Nẵng
#  Thiết kế: Config-driven + Modular Architecture
# ============================================

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker

# ==========================================================
# 1) CONFIG – Tất cả tham số nằm gọn trong 1 cấu hình duy nhất
#    → Tương lai muốn mở rộng thêm cột, thêm logic, chỉ cần chỉnh config
# ==========================================================
CONFIG = {
    "num_rows": 1000,   # Tăng lên 500k / 1M chỉ cần chỉnh số này
    "output_file": "data/raw_traffic_1000.csv",

    # Danh sách đường thực tế Đà Nẵng
    "streets": [
        "Nguyễn Tất Thành", "Điện Biên Phủ", "Ngô Quyền",
        "Trần Phú", "Lê Duẩn", "Hải Phòng", "2 Tháng 9",
        "Hoàng Văn Thái", "Tôn Đức Thắng", "Ông Ích Khiêm"
    ],

    # Giờ cao điểm
    "rush_hours": [(7, 8), (17, 18)],

    # Giới hạn ngẫu nhiên
    "vehicle_range": (5, 200),
    "speed_range": (10, 50)  # km/h
}

faker = Faker("vi_VN")


# ==========================================================
# 2) MODULE: Sinh timestamp
# ==========================================================
def generate_timestamp(start_days_ago=2):
    """
    Sinh timestamp ngẫu nhiên trong 2 ngày gần đây.
    Hàm này tách riêng để dễ thay đổi logic thời gian trong tương lai.
    """
    now = datetime.now()
    start_time = now - timedelta(days=start_days_ago)
    random_time = start_time + timedelta(
        seconds=random.randint(0, start_days_ago * 24 * 3600)
    )
    return random_time


# ==========================================================
# 3) MODULE: Chọn tên đường
# ==========================================================
def generate_street_name():
    return random.choice(CONFIG["streets"])


# ==========================================================
# 4) MODULE: Sinh số lượng xe (vehicle_count)
# ==========================================================
def generate_vehicle_count(timestamp):
    hour = timestamp.hour
    low, high = CONFIG["vehicle_range"]

    # Nếu là giờ cao điểm → xe tăng mạnh
    for start, end in CONFIG["rush_hours"]:
        if start <= hour < end:
            return random.randint(high // 2, high)

    return random.randint(low, high // 2)


# ==========================================================
# 5) MODULE: Sinh vận tốc trung bình
# ==========================================================
def generate_average_speed(timestamp):
    hour = timestamp.hour
    low, high = CONFIG["speed_range"]

    # Giờ cao điểm → tốc độ thấp
    for start, end in CONFIG["rush_hours"]:
        if start <= hour < end:
            return round(random.uniform(low, (low + high) / 2), 2)

    return round(random.uniform((low + high) / 2, high), 2)


# ==========================================================
# 6) MODULE: Tính mức độ kẹt xe theo công thức đơn giản
# ==========================================================
def calculate_congestion(vehicle_count, average_speed):
    """
    Congestion level: 0-3
    - Nhiều xe + tốc độ thấp = kẹt nặng
    - Dễ mở rộng bằng mô hình AI sau này
    """
    if vehicle_count > 150 or average_speed < 15:
        return 3
    if vehicle_count > 100:
        return 2
    if vehicle_count > 50:
        return 1
    return 0


# ==========================================================
# 7) MODULE CHÍNH: Sinh 1 record dữ liệu
# ==========================================================
def generate_record():
    timestamp = generate_timestamp()
    street = generate_street_name()
    vehicle = generate_vehicle_count(timestamp)
    speed = generate_average_speed(timestamp)
    congestion = calculate_congestion(vehicle, speed)

    return {
        "timestamp": timestamp,
        "street_name": street,
        "vehicle_count": vehicle,
        "average_speed": speed,
        "congestion_level": congestion
    }


# ==========================================================
# 8) MAIN FUNCTION – Sinh toàn bộ dataset
# ==========================================================
def generate_dataset():
    rows = [generate_record() for _ in range(CONFIG["num_rows"])]
    df = pd.DataFrame(rows)

    # Xử lý đường dẫn lưu file an toàn
    output_path = os.path.abspath(CONFIG["output_file"])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"✔ Đã sinh {CONFIG['num_rows']} dòng dữ liệu")
    print(f"📁 File lưu tại: {output_path}")


# ==========================================================
# 9) ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    generate_dataset()