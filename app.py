import streamlit as st
import pandas as pd
from PIL import Image
import requests
import json
import uuid
import os

# Cấu hình URL của Backend
BACKEND_URL = "http://localhost:8000/api/chat"
EMAIL_API_URL = "http://localhost:8000/api/send-email"

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

st.set_page_config(page_title="Hệ thống Document AI", page_icon="🧠", layout="wide")
st.markdown("""
<style>
/* Ép chữ của Metric nhỏ lại và cho phép tự động xuống dòng */
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;  /* Giảm size chữ (mặc định là ~2rem) */
    white-space: normal !important; /* Bắt buộc xuống dòng nếu text quá dài */
    line-height: 1.3 !important;    /* Chỉnh khoảng cách dòng cho đẹp */
}
</style>
""", unsafe_allow_html=True)
# KHỞI TẠO BỘ NHỚ TẠM (Rất quan trọng để không mất dữ liệu khi UI load lại)
if "user_session_id" not in st.session_state:
    st.session_state["user_session_id"] = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "user_streamlit_01"
if "extracted_data" not in st.session_state:
    st.session_state["extracted_data"] = None
if "raw_result" not in st.session_state:
    st.session_state["raw_result"] = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Bảng Điều Khiển")
    st.markdown("Hệ thống tự động phân loại và bóc tách dữ liệu sử dụng **Paddle OCR** và **Gemini AI**.")
    app_mode = st.radio("Gợi ý loại tài liệu cho AI:", ("🧾 Hóa đơn / Biên lai", "📄 Văn bản chung"))
    st.markdown("---")
    if st.button("🗑️ Làm mới (Reset)", use_container_width=True):
        st.session_state["user_session_id"] = str(uuid.uuid4())
        st.session_state["extracted_data"] = None # Xóa kết quả cũ
        st.success("Đã làm mới hệ thống!")

# --- MAIN GIAO DIỆN ---
st.title("Hệ Thống Trích Xuất Dữ Liệu Thông Minh")
st.markdown("---")

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.header("1. Tải ảnh tài liệu")
    uploaded_file = st.file_uploader("Kéo thả hoặc chọn file ảnh", type=['jpg', 'jpeg', 'png'])
    temp_file_path = None

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh gốc", use_container_width=True)
        temp_file_path = os.path.abspath(os.path.join(TEMP_DIR, uploaded_file.name))
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

with col_right:
    st.header("2. Kết quả AI Phân tích")
    
    # KHI BẤM NÚT TRÍCH XUẤT
    if uploaded_file and st.button("🚀 Bắt đầu trích xuất dữ liệu", type="primary", use_container_width=True):
        with st.spinner("🧠 AI đang phân tích hình ảnh..."):
            try:
                hint = "Hóa đơn" if "Hóa đơn" in app_mode else "Văn bản"
                query_text = f"Hãy bóc tách dữ liệu từ ảnh này. Cấu trúc gợi ý: {hint}"
                payload = {
                    "query": query_text,
                    "image_path": temp_file_path,
                    "user_id": st.session_state["user_id"],
                    "session_id": st.session_state["user_session_id"]
                }
                
                response = requests.post(BACKEND_URL, json=payload)
                if response.status_code == 200:
                    raw_text = response.json().get("response", "")
                    
                    # Lọc JSON
                    clean_text = raw_text.strip()
                    if clean_text.startswith("```"):
                        start, end = clean_text.find("{"), clean_text.rfind("}")
                        if start != -1 and end != -1:
                            clean_text = clean_text[start:end+1]
                            
                    # LƯU VÀO SESSION STATE ĐỂ RENDER UI
                    st.session_state["raw_result"] = raw_text
                    st.session_state["extracted_data"] = json.loads(clean_text)
                else:
                    st.error(f"Lỗi Backend: {response.text}")
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

    # HIỂN THỊ KẾT QUẢ TỪ SESSION STATE (Đảm bảo không bị mất đi khi bấm gửi mail)
    if st.session_state["extracted_data"]:
        result_data = st.session_state["extracted_data"]
        raw_result = st.session_state["raw_result"]
        doc_type = result_data.get("document_type", "document")
        
        if doc_type == "invoice":
            st.success("Nhận diện thành công: **Hóa đơn / Bảng biểu**")
            c1, c2, c3 = st.columns([2, 1, 1.2])
            c1.metric("Cửa hàng", result_data.get('seller', {}).get('company_name', 'N/A'))
            c2.metric("Ngày", result_data.get('invoice_info', {}).get('date', 'N/A'))
            total = result_data.get('invoice_info', {}).get('total_amount')
            c3.metric("Tổng tiền", f"{total:,} VNĐ" if isinstance(total, int) else "N/A")
            
            items = result_data.get('items', [])
            if items:
                st.subheader(" Chi tiết đơn hàng")
                df = pd.DataFrame(items)
                df.index = df.index + 1 
                st.dataframe(df, use_container_width=True)
        else: 
            st.success(" Nhận diện thành công: **Văn bản thuần**")
            st.info(f" Phân loại: {result_data.get('category', 'N/A')}\n\nTóm tắt: {result_data.get('summary', 'N/A')}")
            st.text_area("Nội dung văn bản:", value=result_data.get('clean_text', ''), height=200)

        with st.expander(" Xem cấu trúc JSON gốc"):
            st.json(result_data)
            
        st.markdown("---")
        st.subheader("📧 Chia sẻ kết quả qua Email")
        
        # FORM GỬI EMAIL ĐƯỢC ĐẶT Ở ĐÂY
        with st.form("share_form"):
            col_email, col_btn = st.columns([3, 1])
            email_input = col_email.text_input("Nhập địa chỉ Email người nhận:", placeholder="abc@gmail.com")
            submit_btn = col_btn.form_submit_button("Gửi Email")
            
            if submit_btn:
                if email_input:
                    with st.spinner("Đang gửi mail..."):
                        mail_payload = {
                            "email_to": email_input,
                            "data_json": result_data
                        }
                        try:
                            mail_res = requests.post(EMAIL_API_URL, json=mail_payload)
                            if mail_res.status_code == 200:
                                st.success(f" Đã gửi báo cáo thành công tới {email_input}!")
                            else:
                                st.error(f"Lỗi gửi mail: {mail_res.text}")
                        except Exception as e:
                            st.error(f"Mất kết nối API: {e}")
                else:
                    st.warning("Vui lòng nhập địa chỉ Email!")