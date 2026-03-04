# 🤖 SYSTEM CONTEXT & GUIDELINES FOR AI AGENTS
# Tên dự án: AI Traffic Da Nang (Hệ thống AI Phân tích & Dự báo Giao thông Đà Nẵng)

## 1. PROJECT OBJECTIVE (MỤC TIÊU DỰ ÁN)
Bạn là AI Agent hỗ trợ code cho dự án này. Nhiệm vụ của hệ thống là:
1. Thu thập dữ liệu giao thông (giả lập bằng Faker hoặc thực tế qua TomTom/Goong API).
2. Huấn luyện mô hình AI (Linear Regression/Random Forest) để dự báo ùn tắc.
3. Hiển thị dữ liệu lên Web Dashboard bằng Streamlit.

## 2. TECH STACK & ENVIRONMENT (CÔNG NGHỆ BẮT BUỘC)
- Ngôn ngữ: Python 3.11 (Môi trường `traffic_env`).
- UI/Frontend: Chỉ sử dụng `streamlit` (Tuyệt đối không dùng Flask/Django/HTML/CSS).
- Data Processing: `pandas`, `numpy`.
- Machine Learning: `scikit-learn`.
- API/Network: `requests`.
- Database: Tạm thời dùng `.csv`, tương lai dùng `sqlite3`.

## 3. STRICT DATA CONTRACT (CẤU TRÚC DỮ LIỆU CỐT LÕI - Cập nhật v1.1)
Mọi file CSV BẮT BUỘC phải có chính xác 7 trường (cột) sau:
1. `timestamp` (string/datetime): Thời gian ghi nhận.
2. `street_name` (string): Tên tuyến đường thực tế tại Đà Nẵng.
3. `latitude` (float): Vĩ độ của tuyến đường (VD: 16.0610).
4. `longitude` (float): Kinh độ của tuyến đường (VD: 108.2248).
5. `vehicle_count` (int): Số lượng phương tiện đếm được/giả lập.
6. `average_speed` (float): Vận tốc trung bình (km/h).
7. `congestion_level` (int): Mức độ kẹt xe (0: Thông thoáng, 1: Bình thường, 2: Ùn ứ, 3: Tắc nghẽn).

## 4. AGENT CODING RULES (QUY TẮC VIẾT CODE CHO AGENT)
Khi được người dùng (SV1, SV2, SV3) yêu cầu viết code, bạn PHẢI tuân thủ:
- **Modular Design:** Tách biệt hàm xử lý data, hàm train AI và hàm vẽ UI. Không gộp tất cả vào 1 file.
- **No Hardcoding Keys:** TUYỆT ĐỐI KHÔNG in ra màn hình hoặc gõ cứng mã API Key thật vào code. Luôn sử dụng `os.getenv("TOMTOM_API_KEY")` hoặc thư viện `python-dotenv`.
- **Error Handling:** Khi gọi API (TomTom/Goong), luôn dùng `try-except` và `timeout` để tránh treo hệ thống Web.
- **Language:** Viết comment giải thích code bằng Tiếng Việt.

## 5. PROJECT WORKFLOW (TIẾN ĐỘ HIỆN TẠI)
- Nếu người dùng nhắc đến **"Sprint 1"**: Chỉ viết code dùng thư viện `Faker` để tạo dữ liệu giả.
- Nếu người dùng nhắc đến **"Sprint 2"**: Viết code kết nối trực tiếp TomTom API / Goong API.
- Nếu người dùng nhắc đến **"Sprint 3"**: Tập trung viết code tối ưu caching (`@st.cache_data`) và Docker.