# ============================================
#  generator.py – AI Data Generator v1.3+
#  Sinh dữ liệu giao thông giả lập cho Đà Nẵng
#  Thiết kế: Config-driven + Modular Architecture
#  Tác giả: Bạn + M365 Copilot 😀
# ============================================

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ==========================================================
# 1) CONFIG – Tất cả tham số nằm gọn trong 1 cấu hình duy nhất
#    → DỄ MỞ RỘNG: chỉ cần chỉnh CONFIG, hạn chế sửa logic
# ==========================================================
CONFIG = {
    # Số dòng dữ liệu cần sinh
    "num_rows": 1000,

    # File output
    "output_file": "data/raw_traffic_1000.csv",

    # Số ngày gần đây để sinh timestamp (vd: 2 ngày gần nhất)
    "time": {
        "start_days_ago": 2,
        # Nếu muốn sinh theo từng phút hoặc từng giờ cố định → có thể bổ sung thêm mode
    },

    # Danh sách đường thực tế Đà Nẵng + profile giao thông
    # Mỗi đường có 1 hệ số traffic riêng: đường lớn, đường ven biển, khu dân cư...
    "streets": {
        "Nguyễn Tất Thành": {"base_factor": 1.2, "type": "ven_bien"},
        "Điện Biên Phủ": {"base_factor": 1.5, "type": "truc_chinh"},
        "Ngô Quyền": {"base_factor": 1.4, "type": "truc_chinh"},
        "Trần Phú": {"base_factor": 1.1, "type": "trung_tam"},
        "Lê Duẩn": {"base_factor": 1.6, "type": "truc_chinh"},
        "Hải Phòng": {"base_factor": 1.3, "type": "truc_chinh"},
        "2 Tháng 9": {"base_factor": 1.4, "type": "truc_chinh"},
        "Hoàng Văn Thái": {"base_factor": 0.9, "type": "ngoai_thanh"},
        "Tôn Đức Thắng": {"base_factor": 1.2, "type": "truc_chinh"},
        "Ông Ích Khiêm": {"base_factor": 1.0, "type": "khu_dan_cu"},
    },

    # Định nghĩa khung giờ (0-23) theo "profile" giờ cao điểm / bình thường / đêm
    "time_profiles": {
        "rush_hours": [(7, 9), (16, 19)],  # mở rộng đến 2h và 3h chiều tối
        "night_hours": (22, 5),           # từ 22h đến 5h sáng hôm sau
    },

    # Biên độ số lượng xe (mức min/max chung)
    "vehicle_range": (5, 220),

    # Vận tốc trung bình (km/h)
    "speed_range": (5, 55),

    # Hệ số điều chỉnh theo loại ngày (weekday / weekend)
    "day_type": {
        "weekday_volume_factor": 1.0,
        "weekend_volume_factor": 0.7,  # cuối tuần ít xe hơn
        "weekend_night_boost": 1.3,    # nhưng buổi tối cuối tuần có thể đông hơn ở vài tuyến
    },

    # Công thức kẹt xe – ngưỡng tham khảo, để dễ tinh chỉnh
    "congestion": {
        "high_volume_threshold": 150,
        "medium_volume_threshold": 90,
        "low_speed_threshold": 15,
        "very_low_speed_threshold": 10,
    },

    # ==== KHUNG MỞ RỘNG CỘT DỮ LIỆU (FUTURE FIELDS) ====
    # Sau này bạn thêm: weather, event, vehicle_type distribution...
    # Chỉ cần bổ sung vào đây và viết thêm hàm generate_xxx tương ứng.
    "enable_future_fields": False,
}

faker = Faker("vi_VN")


# ==========================================================
# 2) MODULE: Utility – Kiểm tra loại ngày & giờ
# ==========================================================
def is_weekend(dt: datetime) -> bool:
    """Trả về True nếu là Thứ 7 / Chủ nhật."""
    return dt.weekday() >= 5  # 5: Thứ 7, 6: CN


def in_hour_range(hour: int, start: int, end: int) -> bool:
    """
    Kiểm tra hour (0-23) có nằm trong khoảng [start, end) hay không.
    Hỗ trợ trường hợp night_hours: (22, 5) → wrap qua 0h.
    """
    if start <= end:
        return start <= hour < end
    # wrap qua 0h (vd: 22 -> 5)
    return hour >= start or hour < end


# ==========================================================
# 3) MODULE: Sinh timestamp
# ==========================================================
def generate_timestamp(start_days_ago: int = None) -> datetime:
    """
    Sinh timestamp ngẫu nhiên trong N ngày gần đây.
    Logic vẫn tách riêng để sau này có thể nâng cấp thành:
    - Sinh theo từng phút trong ngày
    - Sinh theo phân phối Gaussian quanh giờ cao điểm
    """
    if start_days_ago is None:
        start_days_ago = CONFIG["time"]["start_days_ago"]

    now = datetime.now()
    start_time = now - timedelta(days=start_days_ago)

    # Random theo uniform trong khoảng N ngày gần nhất
    random_seconds = random.randint(0, start_days_ago * 24 * 3600)
    random_time = start_time + timedelta(seconds=random_seconds)
    return random_time


# ==========================================================
# 4) MODULE: Chọn tên đường + profile
# ==========================================================
def generate_street():
    """
    Trả về (street_name, street_profile)
    để các hàm khác có thể dùng hệ số base_factor, type...
    """
    street_name = random.choice(list(CONFIG["streets"].keys()))
    profile = CONFIG["streets"][street_name]
    return street_name, profile


# ==========================================================
# 5) MODULE: Sinh số lượng xe (vehicle_count)
#    Thực tế hơn: phụ thuộc
#    - Giờ trong ngày (rush / normal / night)
#    - Loại ngày (weekday / weekend)
#    - Profile của đường (base_factor)
# ==========================================================
def generate_vehicle_count(timestamp: datetime, street_profile: dict) -> int:
    hour = timestamp.hour
    low, high = CONFIG["vehicle_range"]
    rush_hours = CONFIG["time_profiles"]["rush_hours"]
    night_start, night_end = CONFIG["time_profiles"]["night_hours"]

    base_factor = street_profile.get("base_factor", 1.0)

    # Loại ngày
    weekend = is_weekend(timestamp)
    if weekend:
        day_factor = CONFIG["day_type"]["weekend_volume_factor"]
    else:
        day_factor = CONFIG["day_type"]["weekday_volume_factor"]

    # Giờ trong ngày
    if any(in_hour_range(hour, rh[0], rh[1]) for rh in rush_hours):
        # Giờ cao điểm: nhiều xe nhất
        base_min = high * 0.5
        base_max = high * 1.0
    elif in_hour_range(hour, night_start, night_end):
        # Đêm khuya: ít xe
        base_min = low * 0.5
        base_max = low * 1.2
        # Nếu là cuối tuần, đường vui chơi có thể đông hơn chút
        if weekend:
            base_max *= CONFIG["day_type"]["weekend_night_boost"]
    else:
        # Giờ bình thường
        base_min = low * 1.0
        base_max = high * 0.6

    # Áp dụng hệ số theo từng đường
    base_min *= base_factor
    base_max *= base_factor

    # Thêm nhiễu ngẫu nhiên (noise) bằng normal distribution
    mean = (base_min + base_max) / 2
    std = max((base_max - base_min) / 6, 1)  # 3-sigma rule
    value = np.random.normal(loc=mean, scale=std)

    # Giới hạn trong khoảng vehicle_range tổng thể
    value = int(max(low, min(high, value)))

    # Đảm bảo >= 0
    return max(0, value)


# ==========================================================
# 6) MODULE: Sinh vận tốc trung bình (average_speed)
#    Thực tế hơn: phụ thuộc
#    - Giờ cao điểm → tốc độ giảm
#    - Số lượng xe càng đông → tốc độ càng thấp
#    - Đêm khuya → có thể chạy nhanh hơn
# ==========================================================
def generate_average_speed(timestamp: datetime,
                           vehicle_count: int,
                           street_profile: dict) -> float:
    hour = timestamp.hour
    low, high = CONFIG["speed_range"]
    rush_hours = CONFIG["time_profiles"]["rush_hours"]
    night_start, night_end = CONFIG["time_profiles"]["night_hours"]

    # Tốc độ "trung tính"
    base_speed_min = low
    base_speed_max = high

    # Điều chỉnh theo giờ
    if any(in_hour_range(hour, rh[0], rh[1]) for rh in rush_hours):
        # Cao điểm: tốc độ giảm mạnh
        base_speed_max = (low + high) / 2
    elif in_hour_range(hour, night_start, night_end):
        # Đêm khuya: đường vắng → chạy nhanh hơn
        base_speed_min = (low + high) / 2
    else:
        # Giờ thường: ở khoảng giữa
        base_speed_min = low * 1.2
        base_speed_max = high * 0.9

    # Điều chỉnh nhẹ theo loại đường (vd: đường ven biển ít đèn đỏ, chạy nhanh hơn)
    street_type = street_profile.get("type", "")
    if street_type in ["ven_bien", "ngoai_thanh"]:
        base_speed_min *= 1.1
        base_speed_max *= 1.1
    elif street_type in ["trung_tam", "khu_dan_cu"]:
        base_speed_min *= 0.9
        base_speed_max *= 0.9

    # Điều chỉnh theo mật độ xe: xe càng nhiều → tốc độ càng giảm
    vehicle_low, vehicle_high = CONFIG["vehicle_range"]
    density_ratio = (vehicle_count - vehicle_low) / max(
        (vehicle_high - vehicle_low), 1
    )
    # density_ratio ~ 0 → ít xe, ~1 → đông xe
    # Giảm tốc độ theo mật độ xe
    congestion_slowdown = density_ratio * 0.5  # tối đa giảm 50% range
    effective_max = base_speed_max * (1 - 0.3 * density_ratio)
    effective_min = base_speed_min * (1 - congestion_slowdown * 0.3)

    # Thêm noise
    speed = np.random.uniform(effective_min, effective_max)

    # Giới hạn trong [low, high]
    speed = max(low, min(high, speed))

    return round(float(speed), 2)


# ==========================================================
# 7) MODULE: Tính mức độ kẹt xe theo công thức linh hoạt
#    Sử dụng nhiều yếu tố hơn:
#    - vehicle_count
#    - average_speed
#    - Có thể mở rộng thêm: loại đường, thời tiết, sự kiện...
# ==========================================================
def calculate_congestion(vehicle_count: int,
                         average_speed: float,
                         street_profile: dict) -> int:
    cong_cfg = CONFIG["congestion"]

    # Bắt đầu với 0
    score = 0

    # Component 1: dựa trên số lượng xe
    if vehicle_count > cong_cfg["high_volume_threshold"]:
        score += 2
    elif vehicle_count > cong_cfg["medium_volume_threshold"]:
        score += 1

    # Component 2: dựa trên tốc độ
    if average_speed < cong_cfg["very_low_speed_threshold"]:
        score += 2
    elif average_speed < cong_cfg["low_speed_threshold"]:
        score += 1

    # Component 3: loại đường – đường trung tâm dễ kẹt hơn
    street_type = street_profile.get("type", "")
    if street_type in ["trung_tam", "truc_chinh"]:
        score += 0.5

    # Map điểm tổng sang level 0–3
    if score >= 3:
        level = 3
    elif score >= 2:
        level = 2
    elif score >= 1:
        level = 1
    else:
        level = 0

    return int(level)


# ==========================================================
# 8) (OPTIONAL) MODULE: Sinh thêm các trường tương lai
#    Ví dụ: thời tiết, sự kiện, loại phương tiện...
#    → Hiện tại chưa bật, nhưng kiến trúc đã sẵn sàng
# ==========================================================
def generate_future_fields(timestamp: datetime, street_profile: dict) -> dict:
    """
    Placeholder cho các field mở rộng:
    - weather: nắng / mưa / âm u...
    - event: bắn pháo hoa, lễ hội, sự kiện thể thao...
    - dominant_vehicle_type: car / motorbike / truck...
    """
    if not CONFIG.get("enable_future_fields", False):
        return {}

    # Ví dụ demo (đang tắt):
    weather_options = ["nắng", "mưa", "âm u", "nhiều mây"]
    weather = random.choice(weather_options)

    return {
        "weather": weather
    }


# ==========================================================
# 9) MODULE CHÍNH: Sinh 1 record dữ liệu
# ==========================================================
def generate_record() -> dict:
    timestamp = generate_timestamp()
    street_name, street_profile = generate_street()

    vehicle = generate_vehicle_count(timestamp, street_profile)
    speed = generate_average_speed(timestamp, vehicle, street_profile)
    congestion = calculate_congestion(vehicle, speed, street_profile)

    record = {
        "timestamp": timestamp,
        "street_name": street_name,
        "vehicle_count": vehicle,
        "average_speed": speed,
        "congestion_level": congestion,
    }

    # Gộp thêm các field tương lai (nếu enable)
    record.update(generate_future_fields(timestamp, street_profile))

    return record


# ==========================================================
# 10) MAIN FUNCTION – Sinh toàn bộ dataset
# ==========================================================
def generate_dataset():
    rows = [generate_record() for _ in range(CONFIG["num_rows"])]
    df = pd.DataFrame(rows)

    # Xử lý đường dẫn lưu file an toàn
    output_path = os.path.abspath(CONFIG["output_file"])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Lưu CSV
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"✔ Đã sinh {CONFIG['num_rows']} dòng dữ liệu")
    print(f"📁 File lưu tại: {output_path}")


# ==========================================================
# 11) ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    generate_dataset()