import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import time
from datetime import datetime, timedelta
import numpy as np
from fpdf import FPDF 
import io

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="SHIPS Warehouse V3", layout="wide", page_icon="🏢", initial_sidebar_state="expanded")

if 'toast_msg' in st.session_state:
    st.toast(st.session_state.toast_msg, icon='✅')
    del st.session_state.toast_msg

# ==========================================
# 2. INJEKSI CSS PREMIUM & FONT PROFESIONAL
# ==========================================
st.markdown("""
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Menggunakan Font Plus Jakarta Sans yang sangat elegan untuk Enterprise */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [class*="css"], .stApp, p, h1, h2, h3, h4, h5, h6, span, div { 
            font-family: 'Plus Jakarta Sans', sans-serif !important; 
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            padding: 12px 20px; border-radius: 8px; margin: 4px 10px;
            transition: all 0.3s ease; border-left: 4px solid transparent;
            font-weight: 600; font-size: 15px;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: var(--secondary-background-color); transform: translateX(5px); }
        [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] { 
            background-color: var(--secondary-background-color); border-left: 4px solid #0052CC !important; color: #0052CC !important;
        }
        
        /* Card Styling Modern */
        .erp-card {
            background-color: var(--background-color); padding: 24px; border-radius: 16px;
            border: 1px solid var(--secondary-background-color); margin-bottom: 20px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }
        
        /* KPI Box */
        .kpi-box { 
            background-color: var(--background-color); padding: 20px; border-radius: 16px; 
            border: 1px solid var(--secondary-background-color); display: flex; justify-content: space-between; align-items: center; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.03); position: relative; overflow: hidden;
        }
        .kpi-box::before { content: ""; position: absolute; top: 0; left: 0; width: 5px; height: 100%; background: #0052CC; }
        .kpi-box.warning::before { background: #F59E0B; }
        .kpi-box.danger::before { background: #EF4444; }
        .kpi-title { font-size: 13px !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.7; margin-bottom: 5px; }
        .kpi-value { font-size: 36px !important; font-weight: 800 !important; letter-spacing: -1px; }
        
        .stButton>button { border-radius: 8px !important; font-weight: 600 !important; letter-spacing: 0.5px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GLOBAL DATABASE & CORE LOGIC
# ==========================================
# Perbaikan Gambar Logo agar 100% muncul
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
            {"Username": "cpan", "Password": "123", "Nama": "Tim CPAN", "Role": "Staff (Requestor)"}
        ]),
        'stok': pd.DataFrame([
            {"Kode": "EQ-001", "Nama Barang": "Hose Reel Assembly", "Kategori": "Fuelling Equipment", "Stok": 5, "Min": 2, "Lead_Time": 14},
            {"Kode": "TR-001", "Nama Barang": "Brake Pad Heavy Duty", "Kategori": "Trucktive", "Stok": 12, "Min": 4, "Lead_Time": 7},
            {"Kode": "LN-001", "Nama Barang": "Safety Gloves PPE", "Kategori": "Lainnya", "Stok": 20, "Min": 5, "Lead_Time": 3}
        ]),
        'in': pd.DataFrame(columns=["ID", "Tgl", "Barang", "Qty", "User"]),
        'req': pd.DataFrame(columns=["ID", "Tgl", "Pemohon", "Barang", "Qty", "Tujuan", "Status", "Approved_By", "Keterangan_Atasan", "Tgl_Timestamp"]),
        'opname': pd.DataFrame(columns=["Tgl", "Barang", "Fisik", "Sistem", "Selisih", "User"]),
        'notif': []
    }

db = get_global_db()

def tambah_notif(pesan, jenis="info"):
    waktu = datetime.now().strftime('%H:%M')
    icon = "🔵"
    if jenis == "in": icon = "📦"
    elif jenis == "req": icon = "🛒"
    elif jenis == "acc": icon = "✅"
    db['notif'].insert(0, f"{icon} **{waktu}** - {pesan}")
    if len(db['notif']) > 15: db['notif'].pop()

def generate_surat_jalan_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image("logo.jpeg", x=155, y=10, w=40)
    except: pass
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "SHIPS WAREHOUSE", ln=True)
    pdf.set_font("Arial", '', 10); pdf.cell(0, 5, "Material Release Note (Surat Jalan)", ln=True)
    pdf.line(10, 45, 200, 45); pdf.ln(15)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, f"No. Dokumen: {row['ID']}", ln=True)
    pdf.set_font("Arial", '', 11); pdf.cell(0, 8, f"Tanggal: {row['Tgl']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11); pdf.cell(95, 10, "INFORMASI PEMOHON", 1, 0, 'C'); pdf.cell(95, 10, "DETAIL MATERIAL", 1, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(40, 10, "Nama:", 1); pdf.cell(55, 10, f"{row['Pemohon']}", 1); pdf.cell(40, 10, "Barang:", 1); pdf.cell(55, 10, f"{row['Barang']}", 1, 1)
    pdf.cell(40, 10, "Tujuan:", 1); pdf.cell(55, 10, f"{row['Tujuan']}", 1); pdf.cell(40, 10, "Jumlah:", 1); pdf.cell(55, 10, f"{row['Qty']} Pcs", 1, 1)
    pdf.ln(10); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, f"STATUS: {row['Status'].upper()}", ln=True)
    pdf.set_font("Arial", '', 10); pdf.cell(0, 6, f"Disetujui Oleh: {row['Approved_By']}", ln=True)
    pdf.cell(0, 6, f"Catatan: {row['Keterangan_Atasan']}", ln=True)
    pdf.ln(20); pdf.cell(95, 10, "Tanda Tangan Pemohon,", 0, 0, 'C'); pdf.cell(95, 10, "Tanda Tangan Admin Stok,", 0, 1, 'C')
    pdf.ln(20); pdf.cell(95, 10, "( ................................ )", 0, 0, 'C'); pdf.cell(95, 10, "( ................................ )", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 4. SISTEM AUTHENTICATION
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div class='erp-card' style='text-align: center;'>", unsafe_allow_html=True)
        # Menampilkan Logo di Login
        if logo_base64: st.markdown(f'<img src="data:image/jpeg;base64,{logo_base64}" width="140" style="margin-bottom: 20px; border-radius: 8px;"/>', unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 5px; font-weight:800; color:#0052CC;'>SHIPS WMS</h2>", unsafe_allow_html=True)
        st.markdown("<p style='opacity: 0.7; margin-bottom: 30px;'>Enterprise Warehouse Management</p>", unsafe_allow_html=True)
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("SECURE LOGIN", use_container_width=True):
                match = db['users'][(db['users']['Username'] == user) & (db['users']['Password'] == pwd)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Akses Ditolak! Username/Password salah.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. MAIN APP (DASHBOARD & MENUS)
# ==========================================
else:
    user_role = st.session_state.user['Role']
    user_name = st.session_state.user['Nama']

    # --- TOP NAVBAR ---
    st.markdown("<div class='erp-card' style='padding: 12px 24px; display: flex; align-items:center;'>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns([1.5, 2, 1])
    with n1: st.markdown("<h3 style='margin:0; font-weight:800; color:#0052CC;'><i class='fas fa-boxes'></i> SHIPS WMS</h3>", unsafe_allow_html=True)
    with n2:
        with st.popover(f"🔔 Notifikasi ({len(db['req'][db['req']['Status'] == 'Pending'])})", use_container_width=True):
            if not db['notif']: st.info("Belum ada aktivitas")
            for n in db['notif']: st.markdown(n)
    with n3:
        with st.popover(f"👤 {user_name}", use_container_width=True):
            st.caption(f"Role: {user_role}")
            new_pass = st.text_input("Ganti Password", type="password")
            if st.button("Update Password"):
                db['users'].loc[db['users']['Username'] == st.session_state.user['Username'], 'Password'] = new_pass
                st.success("Sukses diupdate!")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # --- SIDEBAR MENU ---
    with st.sidebar:
        if logo_base64: st.markdown(f'<div style="text-align:center; padding: 10px 0 20px 0;"><img src="data:image/jpeg;base64,{logo_base64}" width="150" style="border-radius:8px;"/></div>', unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:12px; color:gray; padding-left:10px;'>MAIN NAVIGATION</h4>", unsafe_allow_html=True)
        m_list = ["📊 Dashboard", "📦 Master Inventory", "📥 Inbound & Kelola", "🛒 Request Material"]
        if user_role in ["Master Admin", "Supervisor"]: m_list += ["📤 Approval", "📝 Stock Opname", "📜 Histori Transaksi"]
        if user_role == "Staff (Admin Stok)": m_list += ["📝 Stock Opname", "📜 Histori Transaksi"]
        if user_role == "Master Admin": m_list += ["⚙️ Akun"]
        menu = st.radio("Menu", m_list, label_visibility="collapsed")

    # ==========================================
    # MODUL LOGIKA MASING-MASING MENU
    # ==========================================
    
    if menu == "📊 Dashboard":
        st.markdown("### 📈 Operasional Hari Ini")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='kpi-box'><div><div class='kpi-title'>Total SKU</div><div class='kpi-value'>{len(db['stok'])}</div></div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='kpi-box'><div><div class='kpi-title'>Pending Request</div><div class='kpi-value'>{len(db['req'][db['req']['Status'] == 'Pending'])}</div></div></div>", unsafe_allow_html=True)
        
        low_stok_df = db['stok'][db['stok']['Stok'] <= db['stok']['Min']]
        c3.markdown(f"<div class='kpi-box danger'><div><div class='kpi-title'>Stok Kritis</div><div class='kpi-value' style='color:#EF4444;'>{len(low_stok_df)}</div></div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='kpi-box warning'><div><div class='kpi-title'>Inbound Data</div><div class='kpi-value' style='color:#F59E0B;'>{len(db['in'])}</div></div></div>", unsafe_allow_html=True)

        g1, g2 = st.columns([2.5, 1.5])
        with g1:
            st.markdown("<div class='erp-card'><h5>📊 Analitik Kategori Barang</h5>", unsafe_allow_html=True)
            fig_cat = px.bar(db['stok'], x='Kategori', y='Stok', color='Kategori', barmode='group', template='plotly_white')
            st.plotly_chart(fig_cat, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with g2:
            st.markdown("<div class='erp-card' style='height:450px; overflow-y:auto;'><h5>⚠️ Pusat Peringatan Stok</h5>", unsafe_allow_html=True)
            if low_stok_df.empty: 
                st.success("Sistem Terkendali. Tidak ada stok kritis.")
            else:
                for _, r in low_stok_df.iterrows():
                    color = "#EF4444" if r['Stok'] == 0 else "#F59E0B"
                    msg = f"🔴 **KOSONG!** Lead Time {r['Lead_Time']} hari. Segera PO!" if r['Stok'] == 0 else f"🟠 **MENIPIS!** Sisa {r['Stok']}. Butuh {r['Lead_Time']} hari kirim."
                    st.markdown(f"<div style='border-left:4px solid {color}; padding:12px; margin-bottom:12px; background:var(--secondary-background-color); border-radius:6px;'><small style='color:gray;'>{r['Kode']}</small><br><b style='font-size:15px;'>{r['Nama Barang']}</b><br><span style='color:{color}; font-size:13px;'>{msg}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "📦 Master Inventory":
        st.markdown("<div class='erp-card'><h4>🗄️ Database Material</h4>", unsafe_allow_html=True)
        # FITUR SEARCH DIKEMBALIKAN
        pencarian = st.text_input("🔍 Cari Nama Barang atau Kode Aset...")
        df_show = db['stok'].copy()
        if pencarian: df_show = df_show[df_show['Nama Barang'].str.contains(pencarian, case=False) | df_show['Kode'].str.contains(pencarian, case=False)]
        
        def status_stok(row):
            if row['Stok'] == 0: return "🔴 Kosong"
            elif row['Stok'] <= row['Min']: return "🟠 Menipis"
            else: return "🟢 Aman"
        df_show['Status'] = df_show.apply(status_stok, axis=1)
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "📥 Inbound & Kelola":
        # TAB HAPUS RECORD DIKEMBALIKAN
        t1, t2, t3 = st.tabs(["📥 Tambah Stok", "➕ Registrasi Barang Baru", "🗑️ Hapus Aset"])
        with t1:
            with st.form("in"):
                brg = st.selectbox("Pilih Material", db['stok']['Nama Barang'])
                qty = st.number_input("Jumlah Masuk (Qty)", min_value=1)
                if st.form_submit_button("UPDATE STOK"):
                    db['stok'].loc[db['stok']['Nama Barang'] == brg, 'Stok'] += qty
                    db['in'] = pd.concat([db['in'], pd.DataFrame([{"ID": f"IN-{int(time.time())}", "Tgl": datetime.now().strftime("%Y-%m-%d"), "Barang": brg, "Qty": qty, "User": user_name}])], ignore_index=True)
                    tambah_notif(f"{user_name} menambah stok {brg}", "in")
                    st.session_state.toast_msg = "Stok Berhasil Ditambah!"
                    st.rerun()
        with t2:
            with st.form("new"):
                c1, c2 = st.columns(2)
                nk = c1.text_input("Kode Aset Baru")
                nn = c2.text_input("Nama Material Lengkap")
                nka = c1.selectbox("Kategori", ["Fuelling Equipment", "Trucktive", "Lainnya"])
                ns = c2.number_input("Stok Awal", min_value=0)
                nm = c1.number_input("Batas Peringatan (Min)", min_value=1)
                nlt = c2.number_input("Lead Time Pengiriman (Hari)", min_value=1)
                if st.form_submit_button("REGISTRASI ASET"):
                    db['stok'] = pd.concat([db['stok'], pd.DataFrame([{"Kode":nk, "Nama Barang":nn, "Kategori":nka, "Stok":ns, "Min":nm, "Lead_Time":nlt}])], ignore_index=True)
                    tambah_notif(f"Aset Baru Terdaftar: {nn}", "in")
                    st.session_state.toast_msg = "Aset Baru Sukses Diregistrasi!"
                    st.rerun()
        with t3:
            st.warning("⚠️ Peringatan: Menghapus material akan menghilangkannya dari database.")
            with st.form("del_brg"):
                del_target = st.selectbox("Pilih Material yang akan DIHAPUS", db['stok']['Nama Barang'])
                if st.form_submit_button("HAPUS MATERIAL PERMANEN"):
                    db['stok'] = db['stok'][db['stok']['Nama Barang'] != del_target]
                    st.session_state.toast_msg = f"{del_target} telah dihapus!"
                    st.rerun()

    elif menu == "🛒 Request Material":
        with st.form("req"):
            r1, r2 = st.columns([2,1])
            b_req = r1.selectbox("Pilih Material", db['stok']['Nama Barang'])
            q_req = r2.number_input("Jumlah Diminta", min_value=1)
            t_req = st.text_input("Tujuan / Keterangan Penggunaan")
            if st.form_submit_button("KIRIM PERMINTAAN"):
                new_req = pd.DataFrame([{"ID": f"RQ-{int(time.time())}", "Tgl": datetime.now().strftime("%Y-%m-%d %H:%M"), "Pemohon": user_name, "Barang": b_req, "Qty": q_req, "Tujuan": t_req, "Status": "Pending", "Approved_By": "-", "Keterangan_Atasan": "-", "Tgl_Timestamp": datetime.now()}])
                db['req'] = pd.concat([db['req'], new_req], ignore_index=True)
                tambah_notif(f"Request baru dari {user_name}", "req")
                st.session_state.toast_msg = "Request Terkirim!"
                st.rerun()
        st.markdown("#### Histori Dokumen Saya")
        my_req = db['req'][db['req']['Pemohon'] == user_name]
        for idx, row in my_req.sort_index(ascending=False).iterrows():
            with st.container():
                st.markdown(f"<div class='erp-card' style='padding:15px; margin-bottom:10px;'><b>{row['ID']}</b> | {row['Barang']} (Qty: {row['Qty']}) <br>Status: <b>{row['Status']}</b> | Catatan: <i>{row['Keterangan_Atasan']}</i></div>", unsafe_allow_html=True)
                if row['Status'] == 'Approved':
                    st.download_button("🖨️ Cetak Surat Jalan PDF", generate_surat_jalan_pdf(row), f"SuratJalan_{row['ID']}.pdf", key=f"pdf_{idx}")

    elif menu == "📤 Approval":
        st.markdown("### 📝 Panel Persetujuan Supervisor")
        pending = db['req'][db['req']['Status'] == 'Pending']
        
        # PERBAIKAN LOGIKA JIKA KOSONG
        if pending.empty:
            st.info("Bagus! Tidak ada permintaan material yang menunggu persetujuan saat ini.")
        else:
            for idx, row in pending.iterrows():
                st.markdown(f"<div style='background:var(--secondary-background-color); padding:15px; border-radius:10px; margin-bottom:10px;'>👷 <b>{row['Pemohon']}</b> meminta <b>{row['Qty']} Pcs {row['Barang']}</b><br><small>Tujuan: {row['Tujuan']}</small></div>", unsafe_allow_html=True)
                ket = st.text_input("Catatan Anda (Opsional):", key=f"k_{idx}")
                c1, c2 = st.columns(2)
                if c1.button("✅ APPROVE", use_container_width=True, key=f"a_{idx}"):
                    stok_now = db['stok'].loc[db['stok']['Nama Barang'] == row['Barang'], 'Stok'].values[0]
                    if stok_now >= row['Qty']:
                        db['stok'].loc[db['stok']['Nama Barang'] == row['Barang'], 'Stok'] -= row['Qty']
                        db['req'].loc[idx, 'Status'], db['req'].loc[idx, 'Approved_By'], db['req'].loc[idx, 'Keterangan_Atasan'] = "Approved", user_name, ket if ket else "Disetujui"
                        tambah_notif(f"Approved {row['ID']}", "acc")
                        st.session_state.toast_msg = "Disetujui!"
                        st.rerun()
                    else: st.error("Gagal! Stok di gudang tidak mencukupi.")
                if c2.button("❌ REJECT", use_container_width=True, key=f"r_{idx}"):
                    db['req'].loc[idx, 'Status'], db['req'].loc[idx, 'Approved_By'], db['req'].loc[idx, 'Keterangan_Atasan'] = "Rejected", user_name, ket if ket else "Ditolak"
                    st.rerun()

    elif menu == "📝 Stock Opname":
        st.markdown("<div class='erp-card'><h4>📝 Stock Opname (Audit Fisik)</h4>", unsafe_allow_html=True)
        with st.form("opname"):
            brg_op = st.selectbox("Pilih Barang yang Diaudit", db['stok']['Nama Barang'])
            fisik = st.number_input("Jumlah Fisik Riil di Rak", min_value=0)
            if st.form_submit_button("SUBMIT HASIL AUDIT"):
                sis = db['stok'].loc[db['stok']['Nama Barang'] == brg_op, 'Stok'].values[0]
                sel = fisik - sis
                new_op = pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Barang": brg_op, "Fisik": fisik, "Sistem": sis, "Selisih": sel, "User": user_name}])
                db['opname'] = pd.concat([db['opname'], new_op], ignore_index=True)
                db['stok'].loc[db['stok']['Nama Barang'] == brg_op, 'Stok'] = fisik
                st.success(f"Audit Selesai. Selisih: {sel}")
        st.dataframe(db['opname'], use_container_width=True)

    elif menu == "📜 Histori Transaksi":
        st.markdown("#### 🔍 Filter & Download Laporan")
        c1, c2, c3 = st.columns([1,1,1])
        tgl_awal = c1.date_input("Dari Tanggal", datetime.now() - timedelta(days=30))
        tgl_akhir = c2.date_input("Sampai Tanggal", datetime.now())
        
        hist_df = db['req'][db['req']['Status'] != 'Pending'].copy()
        hist_df['Tgl_DT'] = pd.to_datetime(hist_df['Tgl'], errors='coerce')
        mask = (hist_df['Tgl_DT'].dt.date >= tgl_awal) & (hist_df['Tgl_DT'].dt.date <= tgl_akhir)
        filtered_df = hist_df.loc[mask].drop(columns=['Tgl_DT'])
        
        st.dataframe(filtered_df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Outbound')
            db['in'].to_excel(writer, index=False, sheet_name='Inbound')
        
        st.download_button(label="📥 Download Laporan (Excel)", data=buffer, file_name=f"Laporan_Gudang_{tgl_awal}.xlsx", mime="application/vnd.ms-excel")

    # MODUL AKUN DIKEMBALIKAN (KHUSUS MASTER ADMIN)
    elif menu == "⚙️ Akun":
        st.markdown("### 👥 Manajemen Pengguna")
        st.dataframe(db['users'], use_container_width=True, hide_index=True)
        
        st.markdown("#### Tambah Pengguna Baru")
        with st.form("add_user"):
            c1, c2 = st.columns(2)
            nu = c1.text_input("Username Baru")
            np = c2.text_input("Password", type="password")
            nn = c1.text_input("Nama Lengkap Karyawan")
            nr = c2.selectbox("Role/Jabatan", ["Supervisor", "Staff (Admin Stok)", "Staff (Requestor)"])
            if st.form_submit_button("BUAT AKUN"):
                if nu in db['users']['Username'].values: st.error("Username sudah dipakai!")
                else:
                    new_user = pd.DataFrame([{"Username": nu, "Password": np, "Nama": nn, "Role": nr}])
                    db['users'] = pd.concat([db['users'], new_user], ignore_index=True)
                    st.session_state.toast_msg = "Akun Baru Dibuat!"
                    st.rerun()
                    
        st.markdown("#### Hapus Pengguna")
        with st.form("del_user"):
            del_user = st.selectbox("Pilih Username yang akan dihapus", db['users']['Username'])
            if st.form_submit_button("HAPUS AKUN"):
                if del_user == "admin": st.error("Master Admin tidak boleh dihapus!")
                else:
                    db['users'] = db['users'][db['users']['Username'] != del_user]
                    st.session_state.toast_msg = "Akun dihapus!"
                    st.rerun()
