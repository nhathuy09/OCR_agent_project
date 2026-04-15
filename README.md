# 📑 Hệ Thống OCR Thông Minh & AI Agent Bóc Tách Hóa Đơn

Dự án nghiên cứu và xây dựng hệ thống nhận diện ký tự quang học (OCR) kết hợp với AI Agent để bóc tách dữ liệu từ hóa đơn và tài liệu một cách tự động và chính xác.

## 🌟 Tính năng nổi bật
- **Tiền xử lý ảnh nâng cao:** Sử dụng OpenCV để khử nhiễu, cân bằng sáng (CLAHE) và lọc kênh màu để xử lý hóa đơn bị mờ hoặc có dấu mộc.
- **Nhận diện chính xác:** Sử dụng Engine PaddleOCR với mô hình ngôn ngữ tiếng Việt.
- **Thuật toán GroupLines:** Tự động gom nhóm các từ rời rạc thành dòng văn bản dựa trên tọa độ hình học, giữ nguyên cấu trúc bảng biểu.
- **AI Agent Integration:** Sử dụng Gemini Flash để suy luận và chuyển đổi văn bản thô sang định dạng JSON có cấu trúc.

## 🛠 Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.9+
- **OCR Engine:** PaddleOCR
- **Xử lý ảnh:** OpenCV, NumPy
- **Backend:** FastAPI
- **AI Model:** Google Gemini API
- **Framework dữ liệu:** Pydantic

## 🚀 Hướng dẫn cài đặt


