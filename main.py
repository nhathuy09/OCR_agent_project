import uvicorn
import uuid
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
load_dotenv()
from my_agent.agent import root_agent

APP_NAME = "agents"
session_service = None
runner = None
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "vohuy1275@gmail.com" 
SENDER_PASSWORD = "tppe dqiz qykv tmtp"
def _send_email_report(receiver_email, data_json):
    """Gửi kết quả bóc tách qua email dưới dạng báo cáo."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        doc_type = data_json.get('document_type', 'Tài liệu')
        
        # Tiêu đề email
        title_str = "Hóa Đơn / Biên Lai" if doc_type == "invoice" else "Văn Bản"
        msg['Subject'] = f"[Document AI] Báo cáo trích xuất dữ liệu - {title_str}"

        # ---------------------------------------------------------
        # TẠO GIAO DIỆN HTML (UI) CHO EMAIL
        # ---------------------------------------------------------
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333333; background-color: #f4f7f6; padding: 20px; }}
                .container {{ max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                .header {{ background-color: #2E86C1; color: #ffffff; padding: 20px; text-align: center; }}
                .header h2 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 25px; }}
                .info-box {{ background-color: #eaf2f8; padding: 15px; border-left: 5px solid #2E86C1; border-radius: 4px; margin-bottom: 20px; }}
                .total-text {{ color: #E74C3C; font-size: 18px; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
                th, td {{ border: 1px solid #dddddd; padding: 10px; text-align: left; }}
                th {{ background-color: #f2f2f2; color: #333; font-weight: bold; }}
                .footer {{ background-color: #f8f9f9; padding: 15px; text-align: center; font-size: 12px; color: #7f8c8d; border-top: 1px solid #eeeeee; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Báo Cáo Phân Tích Dữ Liệu AI 🧠</h2>
                </div>
                <div class="content">
                    <p>Chào bạn,</p>
                    <p>Hệ thống <strong>Document AI</strong> đã xử lý xong tài liệu của bạn. Dưới đây là kết quả chi tiết:</p>
        """

        # HIỂN THỊ NẾU LÀ HÓA ĐƠN (VẼ BẢNG)
        if doc_type == "invoice":
            seller = data_json.get('seller', {}).get('company_name', 'N/A')
            date = data_json.get('invoice_info', {}).get('date', 'N/A')
            total = data_json.get('invoice_info', {}).get('total_amount', 0)
            
            # Xử lý format dấu phẩy cho số tiền
            try:
                total_str = f"{int(total):,} VNĐ"
            except:
                total_str = str(total)

            html_body += f"""
                    <div class="info-box">
                        <strong>🏢 Cửa hàng / Công ty:</strong> {seller}<br>
                        <strong>📅 Ngày lập:</strong> {date}<br>
                        <span class="total-text">💰 Tổng tiền: {total_str}</span>
                    </div>
                    
                    <h3>📦 Chi tiết đơn hàng:</h3>
                    <table>
                        <tr>
                            <th>STT</th>
                            <th>Tên mặt hàng</th>
                            <th>SL</th>
                            <th>Đơn giá</th>
                            <th>Thành tiền</th>
                        </tr>
            """
            
            items = data_json.get('items', [])
            for idx, item in enumerate(items, 1):
                name = item.get('item_name', 'N/A')
                qty = item.get('qty', '-')
                
                # Format giá trị từng dòng
                try: price = f"{int(item.get('unit_price', 0)):,}"
                except: price = str(item.get('unit_price', ''))
                
                try: amt = f"{int(item.get('amount', 0)):,}"
                except: amt = str(item.get('amount', ''))

                html_body += f"""
                        <tr>
                            <td>{idx}</td>
                            <td>{name}</td>
                            <td>{qty}</td>
                            <td>{price}</td>
                            <td>{amt}</td>
                        </tr>
                """
            html_body += "</table>"

        # HIỂN THỊ NẾU LÀ VĂN BẢN (IN ĐOẠN VĂN)
        else:
            category = data_json.get('category', 'Không phân loại')
            summary = data_json.get('summary', 'Không có tóm tắt')
            clean_text = data_json.get('clean_text', '')

            html_body += f"""
                    <div class="info-box">
                        <strong> Phân loại:</strong> {category}<br>
                        <strong> Tóm tắt:</strong> {summary}
                    </div>
                    
                    <h3> Nội dung văn bản:</h3>
                    <div style="background: #fdfdfd; border: 1px dashed #cccccc; padding: 15px; border-radius: 4px; white-space: pre-wrap; font-family: 'Courier New', Courier, monospace;">{clean_text}</div>
            """

        # ĐÓNG THẺ HTML & THÊM CHỮ KÝ ĐỒ ÁN
        html_body += """
                </div>
                <div class="footer">
                    <p>Hệ thống tự động bóc tách dữ liệu sử dụng Tesseract OCR & Google Gemini.</p>
                    <p><strong>© 2026 - Đồ án tốt nghiệp | Sinh viên thực hiện: Võ Nhật Huy</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        # Kết nối và gửi
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False
#------vòng đời-----
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Đang khởi động OCR API...")
    global session_service, runner
    
    
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    yield
    print("Đang tắt ứng dụng...")

app = FastAPI(title="Smart Home AI Agent", lifespan=lifespan)
router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    image_path: str | None = None
    user_id: str | None = None 
    session_id: str | None = None
    email_to: str | None = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
class EmailRequest(BaseModel):
    email_to: str
    data_json: dict
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global session_service, runner

    user_id = request.user_id if request.user_id else str(uuid.uuid4())
    session_id = request.session_id if request.session_id else str(uuid.uuid4())
    full_query = request.query
    if request.image_path:
        # Xử lý dấu gạch chéo cho an toàn trên Windows
        safe_path = request.image_path.replace("\\", "/")
        full_query += f"\n\n[LỆNH BẮT BUỘC]: Bạn hãy gọi công cụ (tool) và truyền chính xác đường dẫn này vào tham số image_path: '{safe_path}'"
    print(f" Request: '{full_query}' | User: {user_id} | Session: {session_id}")

    try:
        try:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            pass
        user_message = types.Content(
            role="user", 
            parts=[types.Part.from_text(text=full_query)]
        )
        final_response_text = "Xin lỗi, tôi không nghe rõ."
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=user_message
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
        if request.email_to and final_response_text:
            try:
                data_to_send = json.loads(final_response_text)
                _send_email_report(request.email_to, data_to_send)
            except:
                pass
        print(f"Response: {final_response_text}")
        return ChatResponse(
            response=final_response_text,
            user_id=user_id,     
            session_id=session_id
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
@router.post("/send-email")
async def send_email_api(request: EmailRequest):
    # Gọi lại chính hàm bạn đã viết ở trên
    success = _send_email_report(request.email_to, request.data_json)
    if success:
        return {"message": "Đã gửi email thành công"}
    else:
        raise HTTPException(status_code=500, detail="Không thể gửi email. Vui lòng kiểm tra lại cấu hình SMTP.")
app.include_router(router, prefix="/api", tags=["Document Chat"])
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)