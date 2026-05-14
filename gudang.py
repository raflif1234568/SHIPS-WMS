import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import time
from datetime import datetime, timedelta
import numpy as np

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="SHIPS Warehouse", layout="wide", page_icon="🏢", initial_sidebar_state="expanded")

# --- SISTEM NOTIFIKASI POP-UP (TOAST) ---
if 'toast_msg' in st.session_state:
    st.toast(st.session_state.toast_msg, icon='✅')
    del st.session_state.toast_msg

# ==========================================
# 2. INJEKSI CSS KELAS ENTERPRISE (PREMIUM UI)
# ==========================================
st.markdown("""
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .stApp, .main, [data-testid="stAppViewContainer"] { background-color: #F8FAFC !important; font-family: 'Inter', sans-serif; }
        p, span, label, h1, h2, h3, h4, li, div, b, strong { color: #0F172A !important; }
        
        [data-testid="stSidebar"] { 
            background: linear-gradient(180deg, #0A1931 0%, #112B54 100%) !important; 
            border-right: none !important; box-shadow: 4px 0 24px rgba(0,0,0,0.06);
        }
        [data-testid="stSidebar"] * { color: #CBD5E1 !important; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #FFFFFF !important; font-weight: 700; letter-spacing: 0.5px; }
        
        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            background-color: transparent; padding: 14px 24px; border-radius: 10px; margin: 6px 16px;
            transition: all 0.3s ease; cursor: pointer; border-left: 4px solid transparent;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: rgba(255,255,255,0.08) !important; color: #FFFFFF !important; transform: translateX(4px); }
        [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] { background-color: rgba(255, 122, 0, 0.15) !important; border-left: 4px solid #FF7A00 !important; }
        [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] * { color: #FFFFFF !important; font-weight: 600; }
        [data-testid="stSidebar"] .stRadio > div > label > div:first-child { display: none; }
        
        .erp-card {
            background-color: #FFFFFF !important; padding: 28px; border-radius: 20px;
            border: 1px solid #F1F5F9; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.03); transition: all 0.3s ease;
        }
        .erp-card:hover { box-shadow: 0 15px 35px rgba(0,0,0,0.06); transform: translateY(-3px); }
        
        .kpi-container { display: flex; gap: 24px; margin-bottom: 24px; }
        .kpi-box { 
            flex: 1; background: #FFFFFF !important; padding: 24px; border-radius: 20px; 
            border: 1px solid #F1F5F9; display: flex; justify-content: space-between; align-items: center; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.02); transition: all 0.3s ease; position: relative; overflow: hidden;
        }
        .kpi-box:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.05); }
        .kpi-box::before { content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #0A1931; }
        .kpi-box.warning::before { background: #F59E0B; }
        .kpi-box.danger::before { background: #EF4444; }
        
        .kpi-title { font-size: 13px !important; color: #64748B !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .kpi-value { font-size: 32px !important; font-weight: 800 !important; color: #0F172A !important; }
        .kpi-icon { width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 24px; }
        
        [data-testid="stTextInput"] input { background-color: #F1F5F9 !important; border: none !important; border-radius: 20px !important; padding: 10px 20px !important; font-size: 14px !important; color: #0F172A !important; }
        [data-testid="stTextInput"] input:focus { box-shadow: 0 0 0 2px rgba(10,25,49,0.1) !important; background-color: #FFFFFF !important; }
        
        [data-testid="stPopover"] button { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 20px !important; padding: 5px 15px !important; color: #0F172A !important; font-weight: 600 !important; }
        [data-testid="stPopover"] button:hover { background-color: #F8FAFC !important; border-color: #CBD5E1 !important; }

        .stButton>button { background-color: #0A1931 !important; border-radius: 12px !important; border: none !important; padding: 10px 20px !important; color: #FFFFFF !important; font-weight: 600 !important; }
        .stButton>button:hover { background-color: #FF7A00 !important; }
        
        .dataframe { border: none !important; background-color: #FFFFFF !important; width: 100%; border-collapse: separate; border-spacing: 0; }
        .dataframe th { background-color: #F8FAFC !important; color: #64748B !important; font-weight: 600 !important; font-size: 13px; text-transform: uppercase; padding: 16px !important; border-bottom: 2px solid #E2E8F0 !important; }
        .dataframe td { color: #334155 !important; font-size: 14px; font-weight: 500; padding: 16px !important; border-bottom: 1px solid #F1F5F9 !important; transition: background 0.2s; }
        .dataframe tr:hover td { background-color: #F8FAFC !important; }
        .footer { text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #E2E8F0; color: #94A3B8 !important; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GLOBAL DATABASE (TEMBUS ANTAR TAB)
# ==========================================
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file: return base64.b64encode(image_file.read()).decode()
    except: return ""

logo_base64 = get_base64_image('logo.jpeg')

@st.cache_resource
def get_global_db():
    return {
        'users': pd.DataFrame([
            {"Username": "admin", "Password": "123", "Nama": "Rafli Fadilah", "Role": "Master Admin"},
            {"Username": "spv", "Password": "123", "Nama": "Supervisor Operasional", "Role": "Supervisor"},
            {"Username": "stok", "Password": "123", "Nama": "Tim Gudang", "Role": "Staff (Admin Stok)"},
            {"Username": "cpan", "Password": "123", "Nama": "Tim CPAN", "Role": "Staff (Requestor)"},
            {"Username": "hino", "Password": "123", "Nama": "Tim Hino Trucktive", "Role": "Staff (Requestor)"}
        ]),
        'stok': pd.DataFrame([
            {"Kode": "EQ-001", "Nama Barang": "Hose Reel Assembly", "Kategori": "Fuelling Equipment", "Stok": 5, "Min": 2},
            {"Kode": "TR-001", "Nama Barang": "Brake Pad Heavy Duty", "Kategori": "Trucktive", "Stok": 12, "Min": 4},
            {"Kode": "LN-001", "Nama Barang": "Safety Gloves PPE", "Kategori": "Lainnya", "Stok": 20, "Min": 5}
        ]),
        'in': pd.DataFrame(columns=["ID", "Tgl", "Barang", "Qty", "User"]),
        # Penambahan kolom 'Approved_By' untuk tracking histori
        'req': pd.DataFrame(columns=["ID", "Tgl", "Pemohon", "Barang", "Qty", "Tujuan", "Status", "Approved_By"])
    }

db = get_global_db()

if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# ==========================================
# 4. HALAMAN LOGIN 
# ==========================================
if not st.session_state.logged_in:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div class='erp-card' style='text-align: center; padding: 50px;'>", unsafe_allow_html=True)
        if logo_base64: st.markdown(f'<img src="data:image/jpeg;base64,{logo_base64}" width="140" style="display: block; margin: 0 auto 15px auto; border-radius: 8px;"/>', unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 5px; font-weight:800; color:#0A1931;'>Warehouse SHIPS</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748B !important; margin-bottom: 40px; font-size:15px;'>Secure Login Portal for Personnel</p>", unsafe_allow_html=True)
        
        with st.form("login"):
            user = st.text_input("Corporate ID / Username")
            pwd = st.text_input("Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("AUTHENTICATE", use_container_width=True):
                match = db['users'][(db['users']['Username'] == user) & (db['users']['Password'] == pwd)]
                if not match.empty:
                    with st.spinner("⏳ Establishing secure connection..."): time.sleep(0.8)
                    st.session_state.logged_in = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.session_state.toast_msg = f"Selamat Datang, {match.iloc[0]['Nama']}!"
                    st.rerun()
                else: st.error("Authentication Failed. Invalid Credentials.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. HALAMAN UTAMA ENTERPRISE
# ==========================================
else:
    user_role = st.session_state.user['Role']
    user_name = st.session_state.user['Nama']

    st.markdown("<div style='background: white; padding: 15px 30px; border-radius: 16px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
    col_logo, col_search, col_profile = st.columns([1.5, 2, 1])
    
    with col_logo:
        st.markdown("<h3 style='margin:0; padding-top:5px; color:#0A1931 !important; font-weight:700;'><i class='fas fa-layer-group' style='color:#FF7A00; margin-right:10px;'></i> SHIPS Warehouse</h3>", unsafe_allow_html=True)
        
    with col_search:
        global_search = st.text_input("Search", placeholder="🔍 Ketik untuk mencari material (Menu Inventory)...", label_visibility="collapsed")
        
    with col_profile:
        with st.popover(f"👤 {user_name} ▼", use_container_width=True):
            st.markdown(f"**Role:** {user_role}")
            st.markdown("---")
            st.markdown("**Ganti Foto Profil**")
            st.file_uploader("Upload Foto", type=['jpg', 'png'], label_visibility="collapsed")
            st.markdown("---")
            if st.button("🚪 Logout System", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        if logo_base64: st.markdown(f'<div style="padding: 10px 0 30px 20px;"><img src="data:image/jpeg;base64,{logo_base64}" width="120" style="border-radius:8px;"/></div>', unsafe_allow_html=True)
        st.markdown("<div style='font-size:11px; font-weight:700; color:#64748B !important; padding-left:24px; margin-bottom:12px; letter-spacing:1px;'>SYSTEM MODULES</div>", unsafe_allow_html=True)
        
        # Penyesuaian Menu Akses
        if user_role == "Master Admin": 
            menu_list = ["📊 Dashboard Insight", "📦 Master Inventory", "📥 Inbound & Kelola Stok", "🛒 Request Material", "📤 Outbound Approval", "📜 Histori Transaksi", "⚙️ System Configuration"]
        elif user_role == "Supervisor": 
            menu_list = ["📊 Dashboard Insight", "📦 Master Inventory", "📤 Outbound Approval", "📜 Histori Transaksi"]
        elif user_role == "Staff (Admin Stok)": 
            menu_list = ["📊 Dashboard Insight", "📦 Master Inventory", "📥 Inbound & Kelola Stok", "📜 Histori Transaksi"]
        elif user_role == "Staff (Requestor)": 
            menu_list = ["📊 Dashboard Insight", "📦 Master Inventory", "🛒 Request Material"]
            
        menu = st.radio("MENU", menu_list, label_visibility="collapsed")

    # ==========================================
    # MODUL 1: DASHBOARD
    # ==========================================
    if menu == "📊 Dashboard Insight":
        tot_sku = len(db['stok'])
        low_stok = len(db['stok'][db['stok']['Stok'] <= db['stok']['Min']])
        tot_in = len(db['in'])
        pending = len(db['req'][db['req']['Status'] == 'Pending'])

        st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-box">
                    <div><div class="kpi-title">Total Active SKU</div><div class="kpi-value">{tot_sku}</div></div>
                    <div class="kpi-icon" style="background:#F1F5F9; color:#0A1931;"><i class="fas fa-boxes" style="color:#0A1931 !important;"></i></div>
                </div>
                <div class="kpi-box">
                    <div><div class="kpi-title">Inbound Processed</div><div class="kpi-value">{tot_in}</div></div>
                    <div class="kpi-icon" style="background:#ECFDF5; color:#059669;"><i class="fas fa-arrow-down" style="color:#059669 !important;"></i></div>
                </div>
                <div class="kpi-box warning">
                    <div><div class="kpi-title">Pending Requests</div><div class="kpi-value" style="color:#D97706 !important;">{pending}</div></div>
                    <div class="kpi-icon" style="background:#FFFBEB; color:#D97706;"><i class="fas fa-clipboard-list" style="color:#D97706 !important;"></i></div>
                </div>
                <div class="kpi-box danger">
                    <div><div class="kpi-title">Critical Stock Alert</div><div class="kpi-value" style="color:#DC2626 !important;">{low_stok}</div></div>
                    <div class="kpi-icon" style="background:#FEF2F2; color:#DC2626;"><i class="fas fa-exclamation-triangle" style="color:#DC2626 !important;"></i></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns([2.5, 1])
        with c1:
            st.markdown("<div class='erp-card'><h4>📈 Stock Movement Analytics</h4><br>", unsafe_allow_html=True)
            np.random.seed(42)
            dates = [(datetime.today() - timedelta(days=i)).strftime("%d %b") for i in range(6, -1, -1)]
            chart_data = pd.DataFrame({"Date": dates * 3, "Category": ["Fuelling Equipment"]*7 + ["Trucktive"]*7 + ["Lainnya"]*7, "Outbound Vol": np.random.randint(2, 20, 21)})
            fig = px.line(chart_data, x="Date", y="Outbound Vol", color="Category", markers=True, line_shape='spline', color_discrete_map={"Fuelling Equipment": "#0A1931", "Trucktive": "#FF7A00", "Lainnya": "#94A3B8"})
            fig.update_layout(font=dict(color="#0F172A"), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(color="#64748B", gridcolor="#F1F5F9", showline=False), yaxis=dict(color="#64748B", gridcolor="#F1F5F9", showline=False), legend=dict(font=dict(color="#0F172A"), orientation="h", y=1.1, title=""), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, theme=None)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown("""
                <div class='erp-card' style='height: 480px; overflow-y: auto;'>
                    <h4>⚠️ Restock Alerts</h4>
                    <p style='font-size:12px; color:#64748B !important; margin-bottom:15px; border-bottom:1px solid #F1F5F9; padding-bottom:10px;'>
                        Daftar material yang telah mencapai batas minimum stok.
                    </p>
            """, unsafe_allow_html=True)
            low_df = db['stok'][db['stok']['Stok'] <= db['stok']['Min']]
            if low_df.empty: st.info("Inventory levels are optimal.")
            else:
                for _, row in low_df.iterrows():
                    color = "#EF4444" if row['Stok'] == 0 else "#F59E0B"
                    st.markdown(f"<div style='display:flex; justify-content:space-between; margin-bottom:16px; border-bottom:1px solid #F1F5F9; padding-bottom:12px;'><div><strong style='font-size:14px; color:#0F172A !important;'>{row['Nama Barang']}</strong><br><span style='font-size:12px; color:#64748B !important;'>{row['Kode']} | {row['Kategori']}</span></div><div style='text-align:right;'><div style='font-weight:800; color:{color} !important; font-size:16px;'>{row['Stok']}</div><div style='font-size:11px; color:#94A3B8 !important;'>Min: {row['Min']}</div></div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # MODUL 2: INVENTORY DATABASE
    # ==========================================
    elif menu == "📦 Master Inventory":
        st.markdown("<div class='erp-card'><h4>🗄️ Enterprise Data Repository</h4><br>", unsafe_allow_html=True)
        df_show = db['stok'].copy()
        if global_search:
            st.success(f"Menampilkan hasil pencarian untuk: **{global_search}**")
            df_show = df_show[df_show['Nama Barang'].str.contains(global_search, case=False) | df_show['Kode'].str.contains(global_search, case=False)]
            
        def get_badge(row):
            if row['Stok'] == 0: return "🔴 Critical"
            elif row['Stok'] <= row['Min']: return "🟠 Warning"
            else: return "🟢 Safe"
        df_show['System Status'] = df_show.apply(get_badge, axis=1)
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # MODUL 3: KELOLA STOK
    # ==========================================
    elif menu == "📥 Inbound & Kelola Stok":
        st.markdown("<div class='erp-card'><h4>🛠️ Inventory Management Module</h4><br>", unsafe_allow_html=True)
        t_up, t_new, t_edit, t_del = st.tabs(["📥 Inbound (Update Stok)", "➕ Register New SKU", "✏️ Modify Details", "🗑️ Remove Record"])
        
        with t_up:
            with st.form("form_update"):
                brg = st.selectbox("Select Material Code/Name", db['stok']['Nama Barang'])
                qty = st.number_input("Inbound Quantity", min_value=1)
                if st.form_submit_button("PROCESS INBOUND", use_container_width=True):
                    with st.spinner("⏳ Mengamankan data ke sistem..."): time.sleep(1)
                    db['stok'].loc[db['stok']['Nama Barang'] == brg, 'Stok'] += qty
                    new_log = pd.DataFrame([{"ID": f"IN-{datetime.now().strftime('%y%m%d%H%M')}", "Tgl": datetime.now().strftime("%d-%m-%Y %H:%M"), "Barang": brg, "Qty": qty, "User": user_name}])
                    db['in'] = pd.concat([db['in'], new_log], ignore_index=True)
                    st.session_state.toast_msg = f"Stok {brg} berhasil ditambah {qty} unit!"
                    st.rerun()
                    
        with t_new:
            with st.form("form_baru"):
                c1, c2 = st.columns(2)
                n_kode = c1.text_input("New SKU / Asset Code")
                n_nama = c2.text_input("Full Equipment Name")
                n_kat = c1.selectbox("Asset Category", ["Fuelling Equipment", "Trucktive", "Lainnya"])
                n_lok = c2.text_input("Storage Location (Rack/Zone)")
                n_stok = c1.number_input("Initial Physical Stock", min_value=0)
                n_min = c2.number_input("Low Stock Threshold", min_value=1)
                if st.form_submit_button("REGISTER NEW ASSET", use_container_width=True):
                    with st.spinner("⏳ Mendaftarkan SKU baru..."): time.sleep(1)
                    new_item = pd.DataFrame([{"Kode": n_kode, "Nama Barang": n_nama, "Kategori": n_kat, "Lokasi": n_lok, "Stok": n_stok, "Min": n_min}])
                    db['stok'] = pd.concat([db['stok'], new_item], ignore_index=True)
                    st.session_state.toast_msg = "Asset baru berhasil diregistrasi!"
                    st.rerun()
                    
        with t_edit:
            brg_edit = st.selectbox("Select Asset to Modify", db['stok']['Nama Barang'])
            if brg_edit:
                curr_idx = db['stok'][db['stok']['Nama Barang'] == brg_edit].index[0]
                curr_data = db['stok'].loc[curr_idx]
                with st.form("form_edit"):
                    e1, e2 = st.columns(2)
                    e_kode = e1.text_input("SKU Code", value=curr_data['Kode'])
                    e_nama = e2.text_input("Material Name", value=curr_data['Nama Barang'])
                    e_kat = e1.selectbox("Category", ["Fuelling Equipment", "Trucktive", "Lainnya"], index=["Fuelling Equipment", "Trucktive", "Lainnya"].index(curr_data['Kategori']))
                    e_min = e2.number_input("Minimum Threshold", min_value=1, value=int(curr_data['Min']))
                    if st.form_submit_button("SAVE MODIFICATIONS", use_container_width=True):
                        with st.spinner("⏳ Memperbarui profil aset..."): time.sleep(1)
                        db['stok'].at[curr_idx, 'Kode'] = e_kode
                        db['stok'].at[curr_idx, 'Nama Barang'] = e_nama
                        db['stok'].at[curr_idx, 'Kategori'] = e_kat
                        db['stok'].at[curr_idx, 'Min'] = e_min
                        st.session_state.toast_msg = "Perubahan profil berhasil disimpan!"
                        st.rerun()
                        
        with t_del:
            with st.form("form_hapus"):
                brg_del = st.selectbox("Select Material for Deletion", db['stok']['Nama Barang'])
                if st.form_submit_button("PERMANENTLY DELETE ASSET", use_container_width=True):
                    with st.spinner("⏳ Menghapus data dari server..."): time.sleep(1)
                    db['stok'] = db['stok'][db['stok']['Nama Barang'] != brg_del]
                    st.session_state.toast_msg = "Aset telah dihapus secara permanen."
                    st.rerun()

    # ==========================================
    # MODUL REQUEST & SURAT JALAN (REVISI BARU)
    # ==========================================
    elif menu == "🛒 Request Material":
        st.markdown("<div class='erp-card'><h4>🛒 Formulir Permintaan Material (Outbound)</h4><br>", unsafe_allow_html=True)
        with st.form("req"):
            st.markdown("<p style='color:#64748B !important; font-size:14px; margin-bottom:20px;'>Isi form di bawah ini untuk mengajukan pengeluaran material ke atasan.</p>", unsafe_allow_html=True)
            r1, r2 = st.columns([2, 1])
            brg_req = r1.selectbox("Pilih Material yang Dibutuhkan", db['stok']['Nama Barang'])
            qty_req = r2.number_input("Jumlah (Qty)", min_value=1)
            tujuan_req = st.text_input("Tujuan / Unit Pekerjaan / Keterangan Lainnya")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("SUBMIT REQUEST", use_container_width=True):
                with st.spinner("⏳ Mengirim permintaan ke Supervisor..."): time.sleep(1.5)
                new_req = pd.DataFrame([{"ID": f"RQ-{datetime.now().strftime('%y%m%d%H%M')}", "Tgl": datetime.now().strftime("%d-%m-%Y %H:%M"), "Pemohon": user_name, "Barang": brg_req, "Qty": qty_req, "Tujuan": tujuan_req, "Status": "Pending", "Approved_By": "-"}])
                db['req'] = pd.concat([db['req'], new_req], ignore_index=True)
                st.session_state.toast_msg = "Request berhasil diajukan!"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # HISTORI REQUEST & TOMBOL CETAK (REVISI BARU)
        st.markdown("#### Histori Request & Dokumen Surat Jalan")
        my_req = db['req'][db['req']['Pemohon'] == user_name]
        
        if my_req.empty:
            st.info("Anda belum memiliki riwayat permintaan material.")
        else:
            for idx, row in my_req.sort_index(ascending=False).iterrows():
                # Tentukan warna status
                if row['Status'] == 'Pending': stat_col, stat_icon = "#F59E0B", "⏳"
                elif row['Status'] == 'Approved': stat_col, stat_icon = "#059669", "✅"
                else: stat_col, stat_icon = "#EF4444", "❌"
                
                with st.container():
                    st.markdown(f"""
                        <div style='border:1px solid #E2E8F0; padding:20px; border-radius:12px; margin-bottom:10px; background:#FFFFFF; box-shadow: 0 2px 10px rgba(0,0,0,0.02);'>
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <div>
                                    <span style='color:{stat_col} !important; font-weight:700; font-size:12px;'>{stat_icon} {row['Status'].upper()}</span><br>
                                    <strong style='font-size:16px; color:#0F172A !important;'>{row['ID']} - {row['Barang']} (Qty: {row['Qty']})</strong><br>
                                    <span style='font-size:13px; color:#64748B !important;'>Tujuan: {row['Tujuan']} | Tgl: {row['Tgl']}</span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # LOGIKA CETAK DOKUMEN JIKA DI-APPROVE
                    if row['Status'] == 'Approved':
                        # Format struk / surat jalan text
                        receipt_text = f"""
======================================================
SHIPS WAREHOUSE - MATERIAL RELEASE NOTE (SURAT JALAN)
======================================================
No. Dokumen : {row['ID']}
Tanggal Req : {row['Tgl']}

INFORMASI PEMOHON:
------------------------------------------------------
Nama Pemohon: {row['Pemohon']}
Tujuan Unit : {row['Tujuan']}

DETAIL MATERIAL YANG DISETUJUI:
------------------------------------------------------
Nama Material : {row['Barang']}
Jumlah / Qty  : {row['Qty']} Pcs

STATUS PERSETUJUAN:
------------------------------------------------------
Status        : {row['Status']}
Disetujui Oleh: {row['Approved_By']}

======================================================
Tanda Tangan Pemohon            Tanda Tangan Admin Stok


(..................)            (..................)
Harap bawa dokumen ini ke Admin Stok Gudang sebagai 
bukti sah pengambilan material fisik.
======================================================
                        """
                        # Tombol Download Text
                        st.download_button(
                            label="🖨️ Cetak Dokumen (Bawa ke Gudang)", 
                            data=receipt_text, 
                            file_name=f"Surat_Jalan_{row['ID']}.txt", 
                            mime="text/plain", 
                            key=f"print_{idx}"
                        )
                    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # MODUL APPROVAL (OUTBOUND)
    # ==========================================
    elif menu == "📤 Outbound Approval":
        st.markdown("<div class='erp-card'><h4>📝 Panel Otorisasi Permintaan</h4><br>", unsafe_allow_html=True)
        pending = db['req'][db['req']['Status'] == 'Pending']
        if pending.empty:
            st.info("Inbox Zero. Tidak ada pengajuan yang membutuhkan persetujuan Anda saat ini.")
        else:
            for idx, row in pending.iterrows():
                st.markdown(f"""
                    <div style='border:1px solid #E2E8F0; padding:20px; border-radius:12px; margin-bottom:16px; background:#F8FAFC;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <strong style='font-size:16px; color:#0F172A !important;'>{row['ID']} | {row['Barang']} (Qty: {row['Qty']})</strong><br>
                                <span style='font-size:13px; color:#64748B !important;'>Pemohon: <b>{row['Pemohon']}</b> untuk <b>{row['Tujuan']}</b> | {row['Tgl']}</span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                a1, a2, _ = st.columns([1, 1, 4])
                if a1.button("✅ AUTHORIZE", key=f"ac_{idx}", use_container_width=True):
                    with st.spinner("⏳ Memproses persetujuan..."): time.sleep(1)
                    stok_now = db['stok'].loc[db['stok']['Nama Barang'] == row['Barang'], 'Stok'].values[0]
                    if stok_now >= row['Qty']:
                        db['stok'].loc[db['stok']['Nama Barang'] == row['Barang'], 'Stok'] -= row['Qty']
                        db['req'].loc[idx, 'Status'] = "Approved"
                        db['req'].loc[idx, 'Approved_By'] = user_name # REVISI: Catat siapa yang approve
                        st.session_state.toast_msg = "Pengeluaran barang disetujui!"
                        st.rerun()
                    else: st.error("Authorization Failed: Stok fisik gudang tidak mencukupi!")
                if a2.button("❌ DECLINE", key=f"rj_{idx}", use_container_width=True):
                    with st.spinner("⏳ Membatalkan permintaan..."): time.sleep(1)
                    db['req'].loc[idx, 'Status'] = "Rejected"
                    db['req'].loc[idx, 'Approved_By'] = user_name # Tetap catat siapa yang mereject
                    st.session_state.toast_msg = "Permintaan telah ditolak."
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # MODUL HISTORI TRANSAKSI (REVISI BARU)
    # ==========================================
    elif menu == "📜 Histori Transaksi":
        st.markdown("<div class='erp-card'><h4>📜 Catatan Log Transaksi Gudang</h4><br>", unsafe_allow_html=True)
        
        tab_masuk, tab_keluar = st.tabs(["📥 Log Barang Masuk (Inbound)", "📤 Log Barang Keluar (Outbound)"])
        
        with tab_masuk:
            st.markdown("##### Histori Penambahan Stok Material")
            st.dataframe(db['in'], use_container_width=True, hide_index=True)
            
        with tab_keluar:
            st.markdown("##### Histori Permintaan & Persetujuan Material")
            # Tampilkan hanya yang sudah diproses (Approved / Rejected)
            hist_out = db['req'][db['req']['Status'] != 'Pending']
            st.dataframe(hist_out, use_container_width=True, hide_index=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # MODUL KELOLA AKUN
    # ==========================================
    elif menu == "⚙️ System Configuration":
        st.markdown("<div class='erp-card'><h4>⚙️ User Access Management</h4><br>", unsafe_allow_html=True)
        st.dataframe(db['users'], hide_index=True, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        t_add, t_edit, t_del = st.tabs(["➕ Create Account", "✏️ Modify Access", "🗑️ Revoke Account"])
        
        with t_add:
            with st.form("add_user"):
                st.markdown("<p style='color:#64748B !important; font-size:14px;'>Create new system credentials and assign operational roles.</p>", unsafe_allow_html=True)
                u_u = st.text_input("Corporate ID (Username)")
                u_p = st.text_input("Authentication Password", type="password")
                u_n = st.text_input("Personnel Full Name")
                u_r = st.selectbox("System Role & Access Level", ["Supervisor", "Staff (Admin Stok)", "Staff (Requestor)"])
                if st.form_submit_button("PROVISION ACCOUNT", use_container_width=True):
                    if u_u in db['users']['Username'].values: st.error("Corporate ID already exists!")
                    else:
                        with st.spinner("⏳ Mendaftarkan akses pengguna..."): time.sleep(1)
                        new_u = pd.DataFrame([{"Username": u_u, "Password": u_p, "Nama": u_n, "Role": u_r}])
                        db['users'] = pd.concat([db['users'], new_u], ignore_index=True)
                        st.session_state.toast_msg = "Akun karyawan berhasil dibuat!"
                        st.rerun()
                        
        with t_edit:
            user_edit = st.selectbox("Select Personnel ID to Modify", db['users']['Username'])
            if user_edit:
                idx_u = db['users'][db['users']['Username'] == user_edit].index[0]
                curr_u = db['users'].loc[idx_u]
                with st.form("edit_u"):
                    eu_n = st.text_input("Personnel Full Name", value=curr_u['Nama'])
                    eu_p = st.text_input("Reset Password", value=curr_u['Password'])
                    eu_r = st.selectbox("Update Role", ["Supervisor", "Staff (Admin Stok)", "Staff (Requestor)", "Master Admin"], index=["Supervisor", "Staff (Admin Stok)", "Staff (Requestor)", "Master Admin"].index(curr_u['Role']))
                    if st.form_submit_button("UPDATE CREDENTIALS", use_container_width=True):
                        with st.spinner("⏳ Memperbarui profil keamanan..."): time.sleep(1)
                        db['users'].at[idx_u, 'Nama'] = eu_n
                        db['users'].at[idx_u, 'Password'] = eu_p
                        db['users'].at[idx_u, 'Role'] = eu_r
                        st.session_state.toast_msg = "Kredensial akun diupdate!"
                        st.rerun()
                        
        with t_del:
            with st.form("del_u"):
                u_del = st.selectbox("Select Personnel ID to Revoke", db['users']['Username'])
                if st.form_submit_button("REVOKE ACCESS PERMANENTLY", use_container_width=True):
                    if u_del == "admin": st.error("System violation: Cannot revoke Primary Master Admin account.")
                    else:
                        with st.spinner("⏳ Mencabut hak akses..."): time.sleep(1)
                        db['users'] = db['users'][db['users']['Username'] != u_del]
                        st.session_state.toast_msg = "Akses akun telah dicabut permanen."
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)