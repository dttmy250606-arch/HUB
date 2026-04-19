pip install gtts
import streamlit as st
import time
from gtts import gTTS
import io
import pygame # Thư viện mới để phát nhạc trực tiếp

# ==========================================
# 1. CẤU HÌNH TRANG WEB
# ==========================================
st.set_page_config(
    page_title="Smart Bank - Thao Vy", 
    layout="wide", 
    page_icon="🏦",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS GIAO DIỆN & VÉ IN
# ==========================================
st.markdown("""
<style>
    /* Nền & Bản đồ */
    .stApp {
        background: linear-gradient(135deg, #E0EAFC 0%, #CFDEF3 100%);
        background-attachment: fixed;
    }
    .stApp::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-size: contain; background-position: center; background-repeat: no-repeat;
        opacity: 0.08; z-index: 0; pointer-events: none;
    }

    /* CARD KÍNH MỜ */
    .glass-card {
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px);
        border-radius: 20px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        padding: 20px; margin-bottom: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.8);
    }

    /* SỐ TO TRÊN BẢNG */
    .num-display { font-size: 80px; font-weight: 900; margin: 0; line-height: 1.1; }
    .vip-text { background: linear-gradient(to right, #FF416C, #FF4B2B); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .norm-text { background: linear-gradient(to right, #00B4DB, #0083B0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

    /* DANH SÁCH CHỜ */
    .queue-item {
        padding: 12px; border-radius: 10px; margin-bottom: 8px; 
        background: rgba(255,255,255,0.9); border-left-width: 6px; border-left-style: solid;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); font-size: 0.95rem;
    }
    .q-vip { border-left-color: #FF4B2B; }
    .q-norm { border-left-color: #0083B0; }

    /* === GIAO DIỆN VÉ IN RA === */
    .ticket-box {
        border: 2px dashed #999; padding: 20px; border-radius: 15px;
        background: #fff; text-align: center; margin-top: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        animation: popUp 0.5s ease;
    }
    .ticket-vip { border-color: #FF4B2B; background: #FFF5F5; }
    .ticket-norm { border-color: #0083B0; background: #F0F9FF; }
    
    .t-title { font-weight: bold; font-size: 1.2rem; text-transform: uppercase; margin-bottom: 5px;}
    .t-code { font-size: 3.5rem; font-weight: 900; margin: 10px 0; letter-spacing: 2px; }
    .t-info { font-size: 1rem; color: #555; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 5px;}
    .t-loc { font-size: 1.3rem; font-weight: bold; margin-top: 10px; color: #333; }

    @keyframes popUp { from {transform: scale(0.8); opacity: 0;} to {transform: scale(1); opacity: 1;} }
    
    /* NÚT BẤM */
    div.stButton > button:first-child { font-weight: bold; border-radius: 10px; height: 3.5em; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. KHỞI TẠO DỮ LIỆU
# ==========================================
if 'queues' not in st.session_state:
    st.session_state.queues = {'vip': [], 'normal': []}
if 'counters' not in st.session_state:
    st.session_state.counters = {'vip': 0, 'normal': 0}
if 'display' not in st.session_state:
    st.session_state.display = {
        'vip': {'code': '--', 'name': '...', 'loc': ''}, 
        'normal': {'code': '--', 'name': '...', 'loc': ''}
    }
if 'vip_streak' not in st.session_state:
    st.session_state.vip_streak = 0
if 'last_ticket' not in st.session_state:
    st.session_state.last_ticket = None

# ==========================================
# 4. HÀM ÂM THANH (DÙNG PYGAME PHÁT TRỰC TIẾP)
# ==========================================
def speak(text):
    try:
        # 1. Tạo file âm thanh ảo trong RAM (không cần lưu ra ổ cứng)
        tts = gTTS(text=text, lang='vi')
        sound_file = io.BytesIO()
        tts.write_to_fp(sound_file)
        sound_file.seek(0)
        
        # 2. Dùng Pygame phát trực tiếp ra loa máy tính
        pygame.mixer.init()
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        
        # Lưu ý: Không cần chờ nhạc chạy hết để tránh treo web
    except Exception as e:
        st.toast(f"Lỗi loa: {e}", icon="⚠️")

# ==========================================
# 5. LOGIC XỬ LÝ
# ==========================================
def process_ticket():
    name = st.session_state.name_input
    amount = st.session_state.amount_input
    
    if not name or amount <= 0:
        st.error("Vui lòng nhập đủ Tên và Tiền!"); return

    # Phân loại
    if amount >= 1_000_000_000:
        cat = 'vip'; prefix = 'V'; loc = "Phòng VIP - Lầu 1"
        type_label = "KHÁCH HÀNG VIP"
        css_class = "ticket-vip"
        color = "#FF4B2B"
    else:
        cat = 'normal'
        if amount < 200_000_000:
            prefix = 'N'; loc = "Quầy 1 - 2"; type_label = "KHÁCH THƯỜNG (NHANH)"
        else:
            prefix = 'G'; loc = "Quầy 3 - 4"; type_label = "KHÁCH PHỔ THÔNG"
        css_class = "ticket-norm"
        color = "#0083B0"

    st.session_state.counters[cat] += 1
    code = f"{prefix}{str(st.session_state.counters[cat]).zfill(3)}"
    
    ticket = {
        "code": code, "name": name, 
        "amount": f"{amount:,.0f} đ", "loc": loc, 
        "type": type_label, "css": css_class, "color": color
    }
    
    st.session_state.queues[cat].append(ticket)
    st.session_state.last_ticket = ticket

def auto_call_next():
    vip_q = st.session_state.queues['vip']
    norm_q = st.session_state.queues['normal']
    streak = st.session_state.vip_streak
    target_queue = None; target_cat = ''

    # Logic 3 VIP - 1 Thường
    if (streak < 3 and len(vip_q) > 0) or (len(norm_q) == 0 and len(vip_q) > 0):
        target_queue = vip_q; target_cat = 'vip'; st.session_state.vip_streak += 1
    elif len(norm_q) > 0:
        target_queue = norm_q; target_cat = 'normal'; st.session_state.vip_streak = 0
    else:
        st.toast("Hàng chờ trống!", icon="💤"); return

    ticket = target_queue.pop(0)
    st.session_state.display[target_cat] = ticket
    
    # Đọc loa
    action = "lên" if target_cat == 'vip' else "đến"
    
    # Phát thông báo Toast trước
    st.toast(f"Đang gọi: {ticket['code']}", icon="🔊")
    
    # Phát âm thanh trực tiếp
    speak(f"Mời khách hàng {ticket['name']}, số vé {ticket['code']}, {action} {ticket['loc']}")

# ==========================================
# 6. GIAO DIỆN
# ==========================================
st.markdown("""
<div style="background: #004e92; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
    <marquee direction="left">🎉 CHÀO MỪNG QUÝ KHÁCH! --- GIỜ LÀM VIỆC: 8:00 - 17:00 --- KÍNH CHÚC QUÝ KHÁCH NHIỀU SỨC KHỎE! 🎉</marquee>
</div>
""", unsafe_allow_html=True)

st.title("🏦 HỆ THỐNG GIAO DỊCH THÔNG MINH")

# BẢNG ĐIỆN TỬ
c1, c2 = st.columns(2)
with c1:
    d = st.session_state.display['vip']
    st.markdown(f"""
    <div class="glass-card" style="border-top: 5px solid #FF4B2B;">
        <div style="color:#FF4B2B; font-weight:bold;">ĐANG GỌI VIP</div>
        <div class="num-display vip-text">{d['code']}</div>
        <div style="font-size:25px; font-weight:bold;">{d['name']}</div>
        <div style="color:#555;">📍 {d['loc']}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    d = st.session_state.display['normal']
    st.markdown(f"""
    <div class="glass-card" style="border-top: 5px solid #0083B0;">
        <div style="color:#0083B0; font-weight:bold;">ĐANG GỌI PHỔ THÔNG</div>
        <div class="num-display norm-text">{d['code']}</div>
        <div style="font-size:25px; font-weight:bold;">{d['name']}</div>
        <div style="color:#555;">📍 {d['loc']}</div>
    </div>""", unsafe_allow_html=True)

st.write("---")

# KHU VỰC ĐIỀU KHIỂN
cc1, cc2 = st.columns([1, 2])
with cc1:
    # Nút bấm quan trọng
    st.button("🔔 GỌI KHÁCH TIẾP THEO", on_click=auto_call_next, type="primary", use_container_width=True)
with cc2:
    s = st.session_state.vip_streak
    st.info(f"**🤖 Auto-Dispatch:** Đã gọi **{s}/3** VIP. Tiếp theo ưu tiên: **{'Khách Thường' if s>=3 else 'VIP'}**.")

st.write("---")

# KHU VỰC KIOSK & LIST
col_kiosk, col_list = st.columns([1, 1])

# KIOSK
with col_kiosk:
    st.subheader("🎫 Kiosk Cấp Số")
    with st.container(border=True):
        st.text_input("Tên Khách Hàng", key="name_input")
        st.number_input("Số Tiền (VNĐ)", min_value=0, step=10000000, key="amount_input", format="%d")
        st.button("🖨️ IN VÉ NGAY", on_click=process_ticket, use_container_width=True)
    
    # --- PHẦN HIỂN THỊ VÉ ĐẦY ĐỦ THÔNG TIN ---
    if st.session_state.last_ticket:
        t = st.session_state.last_ticket
        st.markdown(f"""
        <div class="ticket-box {t['css']}">
            <div class="t-title" style="color:{t['color']}">{t['type']}</div>
            <div class="t-code" style="color:{t['color']}">{t['code']}</div>
            <div class="t-info">👤 Khách hàng: <b>{t['name']}</b></div>
            <div class="t-info">💰 Giao dịch: <b>{t['amount']}</b></div>
            <div class="t-loc">👉 {t['loc']}</div>
            <div style="margin-top:10px; font-size:0.8rem; color:#888;"><i>(Vui lòng chờ đến lượt gọi)</i></div>
        </div>
        """, unsafe_allow_html=True)

# LIST
with col_list:
    st.subheader("📋 Danh Sách Chờ")
    tv, tn = st.tabs([f"VIP ({len(st.session_state.queues['vip'])})", f"Thường ({len(st.session_state.queues['normal'])})"])
    
    with tv:
        if st.session_state.queues['vip']:
            for t in st.session_state.queues['vip']:
                st.markdown(f"""<div class="queue-item q-vip"><b>{t['code']}</b> - {t['name']} <br><small>💰 {t['amount']}</small></div>""", unsafe_allow_html=True)
        else: st.caption("Trống")
    with tn:
        if st.session_state.queues['normal']:
            for t in st.session_state.queues['normal']:
                st.markdown(f"""<div class="queue-item q-norm"><b>{t['code']}</b> - {t['name']} <br><small>💰 {t['amount']}</small></div>""", unsafe_allow_html=True)
        else: st.caption("Trống")

st.markdown("<br><hr><center><small>System developed by Thao Vy</small></center>", unsafe_allow_html=True)
