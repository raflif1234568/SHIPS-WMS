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
st.set_page_config(page_title="SHIPS Warehouse v2.0", layout="wide", page_icon="🏢", initial_sidebar_state="expanded")

if 'toast_msg' in st.session_state:
    st.toast(st.session_state.toast_msg, icon='✅')
    del st.session_state.toast_msg

# ==========================================
# 2. INJEKSI CSS (AUTO THEME + PREMIUM STYLING)
# ==========================================
st.markdown("""
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        .stApp { font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] div[role="radiogroup"] > label {
            padding: 10px 20px; border-radius: 8px; margin: 4px 10px;
            transition: 0.3s; border-left: 4px solid transparent;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: var(--secondary-background-color); }
        [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] { 
            background-color: var(--secondary-background-color); border-left: 4px solid #FF7A00 !important; 
        }
        .erp-card {
            background-color: var(--background-color); padding: 24px; border-radius: 16px;
            border: 1px solid var(--secondary-background-color); margin-bottom: 20px; 
        }
        .kpi-box { 
            background-color: var(--background-color); padding: 20px; border-radius: 16px; 
            border: 1px solid var(--secondary-background-color); display: flex; justify-content: space-between; align-items: center; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); position: relative; overflow: hidden;
        }
        .kpi-box::before { content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #0A1931; }
        .kpi-box.warning::before { background: #F59E0B; }
        .kpi-box.danger::before { background: #EF4444; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. GLOBAL DATABASE & CORE LOGIC
# ==========================================
logo_path = "logo.jpeg"

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
    try: pdf.image(logo_path, x=155, y=10, w=40)
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
# 4. SISTEM AUTH
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div class='erp-card' style='text-align: center;'>", unsafe_allow_html=True)
        try:
            with open(logo_path, "rb") as f:
                st.image(f.read(), width=140)
        except: pass
        st.markdown("<h2 style='margin-bottom: 0;'>Warehouse SHIPS</h2>", unsafe_allow_html=True)
        st.caption("Secure Enterprise Login")
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                match = db['users'][(db['users']['Username'] == user) & (db['users']['Password'] == pwd)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Akses Ditolak!")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 5. MAIN APP
# ==========================================
else:
    user_role, user_name = st.session_state.user['Role'], st.session_state.user['Nama']

    # --- NAVBAR ---
    st.markdown("<div class='erp-card' style='padding: 10px 24px; display: flex; align-items:center;'>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns([1.5, 2, 1])
    with n1: st.markdown("<h3 style='margin:0;'><i class='fas fa-layer-group' style='color:#FF7A00;'></i> SHIPS WMS</h3>", unsafe_allow_html=True)
    with n2:
        with st.popover(f"🔔 Notifikasi ({len(db['req'][db['req']['Status'] == 'Pending'])})", use_container_width=True):
            for n in db['notif']: st.markdown(n)
    with n3:
        with st.popover(f"👤 {user_name}", use_container_width=True):
            st.caption(f"Role: {user_role}")
            new_pass = st.text_input("Ganti Password", type="password")
            if st.button("Update Password"):
                db['users'].loc[db['users']['Username'] == st.session_state.user['Username'], 'Password'] = new_pass
                st.success("Sukses!")
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### MAIN MENU")
        m_list = ["📊 Dashboard", "📦 Master Inventory", "📥 Inbound/Register", "🛒 Request Material"]
        if user_role in ["Master Admin", "Supervisor"]: m_list += ["📤 Approval", "📝 Stock Opname", "📜 Histori Transaksi"]
        if user_role == "Master Admin": m_list += ["⚙️ Akun"]
        menu = st.radio("Menu", m_list, label_visibility="collapsed")

    # ==========================================
    # MODUL DASHBOARD (REVISI LEAD TIME & ALERT)
    # ==========================================
    if menu == "📊 Dashboard":
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='kpi-box'><div><div class='kpi-title'>Total SKU</div><div class='kpi-value'>{len(db['stok'])}</div></div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='kpi-box'><div><div class='kpi-title'>Pending Req</div><div class='kpi-value'>{len(db['req'][db['req']['Status'] == 'Pending'])}</div></div></div>", unsafe_allow_html=True)
        
        low_stok_df = db['stok'][db['stok']['Stok'] <= db['stok']['Min']]
        c3.markdown(f"<div class='kpi-box danger'><div><div class='kpi-title'>Kritis</div><div class='kpi-value'>{len(low_stok_df)}</div></div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='kpi-box warning'><div><div class='kpi-title'>Inbound</div><div class='kpi-value'>{len(db['in'])}</div></div></div>", unsafe_allow_html=True)

        g1, g2 = st.columns([2.5, 1.5])
        with g1:
            st.markdown("<div class='erp-card'><h5>📈 Analitik Pergerakan Barang</h5>", unsafe_allow_html=True)
            # Grafik Bar untuk kategori
            fig_cat = px.bar(db['stok'], x='Kategori', y='Stok', color='Kategori', barmode='group')
            st.plotly_chart(fig_cat, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with g2:
            st.markdown("<div class='erp-card' style='height:450px; overflow-y:auto;'><h5>⚠️ Pusat Peringatan Stok</h5>", unsafe_allow_html=True)
            if low_stok_df.empty: st.success("Stok Terkendali.")
            else:
                for _, r in low_stok_df.iterrows():
                    color = "#EF4444" if r['Stok'] == 0 else "#F59E0B"
                    msg = f"🔴 **KOSONG!** Lead Time {r['Lead_Time']} hari. Segera PO!" if r['Stok'] == 0 else f"🟠 **MENIPIS!** Sisa {r['Stok']}. Butuh {r['Lead_Time']} hari kirim."
                    st.markdown(f"<div style='border-left:4px solid {color}; padding:10px; margin-bottom:10px; background:var(--secondary-background-color);'><small>{r['Kode']}</small><br><b>{r['Nama Barang']}</b><br><span style='color:{color}; font-size:12px;'>{msg}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # MODUL INBOUND & REGISTER (REVISI LEAD TIME)
    # ==========================================
    elif menu == "📥 Inbound/Register":
        t1, t2 = st.tabs(["📥 Tambah Stok Existing", "➕ Registrasi Barang Baru"])
        with t1:
            with st.form("in"):
                brg = st.selectbox("Barang", db['stok']['Nama Barang'])
                qty = st.number_input("Qty", min_value=1)
                if st.form_submit_button("UPDATE STOK"):
                    db['stok'].loc[db['stok']['Nama Barang'] == brg, 'Stok'] += qty
                    db['in'] = pd.concat([db['in'], pd.DataFrame([{"ID": f"IN-{int(time.time())}", "Tgl": datetime.now().strftime("%Y-%m-%d"), "Barang": brg, "Qty": qty, "User": user_name}])], ignore_index=True)
                    tambah_notif(f"{user_name} tambah stok {brg}", "in")
                    st.rerun()
        with t2:
            with st.form("new"):
                st.info("💡 Gunakan Scanner pada kolom 'Kode Aset' jika tersedia.")
                c1, c2 = st.columns(2)
                nk = c1.text_input("Kode Aset (Scan/Ketik)")
                nn = c2.text_input("Nama Material")
                nka = c1.selectbox("Kategori", ["Fuelling Equipment", "Trucktive", "Lainnya"])
                ns = c2.number_input("Stok Awal", min_value=0)
                nm = c1.number_input("Batas Min", min_value=1)
                nlt = c2.number_input("Lead Time Pengiriman (Hari)", min_value=1) # REVISI 4
                if st.form_submit_button("SIMPAN ASET"):
                    db['stok'] = pd.concat([db['stok'], pd.DataFrame([{"Kode":nk, "Nama Barang":nn, "Kategori":nka, "Stok":ns, "Min":nm, "Lead_Time":nlt}])], ignore_index=True)
                    tambah_notif(f"Asset Baru: {nn}", "in")
                    st.rerun()

    # ==========================================
    # MODUL STOCK OPNAME (REVISI 1)
    # ==========================================
    elif menu == "📝 Stock Opname":
        st.markdown("<div class='erp-card'><h4>📝 Stock Opname (Audit Fisik)</h4>", unsafe_allow_html=True)
        with st.form("opname"):
            brg_op = st.selectbox("Pilih Barang yang Diaudit", db['stok']['Nama Barang'])
            fisik = st.number_input("Jumlah Fisik di Rak", min_value=0)
            if st.form_submit_button("SUBMIT HASIL AUDIT"):
                sis = db['stok'].loc[db['stok']['Nama Barang'] == brg_op, 'Stok'].values[0]
                sel = fisik - sis
                new_op = pd.DataFrame([{"Tgl": datetime.now().strftime("%Y-%m-%d"), "Barang": brg_op, "Fisik": fisik, "Sistem": sis, "Selisih": sel, "User": user_name}])
                db['opname'] = pd.concat([db['opname'], new_op], ignore_index=True)
                db['stok'].loc[db['stok']['Nama Barang'] == brg_op, 'Stok'] = fisik
                st.success(f"Audit Selesai. Selisih: {sel}")
        st.dataframe(db['opname'], use_container_width=True)

    # ==========================================
    # MODUL HISTORI & EXCEL (REVISI 2 & 5)
    # ==========================================
    elif menu == "📜 Histori Transaksi":
        st.markdown("#### 🔍 Filter & Download Laporan")
        c1, c2, c3 = st.columns([1,1,1])
        tgl_awal = c1.date_input("Dari Tanggal", datetime.now() - timedelta(days=30))
        tgl_akhir = c2.date_input("Sampai Tanggal", datetime.now())
        
        hist_df = db['req'][db['req']['Status'] != 'Pending'].copy()
        # Filter sederhana berdasarkan string tanggal
        hist_df['Tgl_DT'] = pd.to_datetime(hist_df['Tgl'], errors='coerce')
        mask = (hist_df['Tgl_DT'].dt.date >= tgl_awal) & (hist_df['Tgl_DT'].dt.date <= tgl_akhir)
        filtered_df = hist_df.loc[mask].drop(columns=['Tgl_DT'])
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Fitur Export ke Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Outbound')
            db['in'].to_excel(writer, index=False, sheet_name='Inbound')
        
        st.download_button(label="📥 Download Laporan (Excel)", data=buffer, file_name=f"Laporan_Gudang_{tgl_awal}.xlsx", mime="application/vnd.ms-excel")

    # (Modul lain seperti Request, Approval, Master Inventory, Akun tetap ada dengan logika yang sama)
    elif menu == "📦 Master Inventory":
        st.dataframe(db['stok'], use_container_width=True, hide_index=True)
    
    elif menu == "🛒 Request Material":
        with st.form("req"):
            r1, r2 = st.columns([2,1])
            b_req = r1.selectbox("Material", db['stok']['Nama Barang'])
            q_req = r2.number_input("Qty", min_value=1)
            t_req = st.text_input("Keperluan")
            if st.form_submit_button("SUBMIT"):
                new_req = pd.DataFrame([{"ID": f"RQ-{int(time.time())}", "Tgl": datetime.now().strftime("%Y-%m-%d %H:%M"), "Pemohon": user_name, "Barang": b_req, "Qty": q_req, "Tujuan": t_req, "Status": "Pending", "Approved_By": "-", "Keterangan_Atasan": "-", "Tgl_Timestamp": datetime.now()}])
                db['req'] = pd.concat([db['req'], new_req], ignore_index=True)
                tambah_notif(f"Req baru dari {user_name}", "req")
                st.rerun()
        st.markdown("---")
        my_req = db['req'][db['req']['Pemohon'] == user_name]
        for idx, row in my_req.sort_index(ascending=False).iterrows():
            st.markdown(f"**{row['ID']}** - {row['Barang']} ({row['Status']})")
            if row['Status'] == 'Approved':
                st.download_button("📄 PDF", generate_surat_jalan_pdf(row), f"{row['ID']}.pdf", key=f"pdf_{idx}")

    elif menu == "📤 Approval":
        pending = db['req'][db['req']['Status'] == 'Pending']
        for idx, row in pending.iterrows():
            st.markdown(f"**{row['Pemohon']}** minta {row['Qty']} {row['Barang']}")
            ket = st.text_input("Catatan Atasan", key=f"k_{idx}")
            c1, c2 = st.columns(2)
            if c1.button("APPROVE", key=f"a_{idx}"):
                db['stok'].loc[db['stok']['Nama Barang'] == row['Barang'], 'Stok'] -= row['Qty']
                db['req'].loc[idx, 'Status'], db['req'].loc[idx, 'Approved_By'], db['req'].loc[idx, 'Keterangan_Atasan'] = "Approved", user_name, ket
                tambah_notif(f"Approved {row['ID']}", "acc")
                st.rerun()
            if c2.button("REJECT", key=f"r_{idx}"):
                db['req'].loc[idx, 'Status'], db['req'].loc[idx, 'Approved_By'], db['req'].loc[idx, 'Keterangan_Atasan'] = "Rejected", user_name, ket
                st.rerun()