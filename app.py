import streamlit as st
from supabase import create_client, Client
import re
from fpdf import FPDF
import os
import base64
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Excellence Model School — Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Dashboard Theme
st.markdown('''
<style>
    .stApp { background-color: #F4F5F8; }
    .block-container { padding-top: 1.5rem !important; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2B1A63 0%, #1A103C 100%);
        color: white;
    }
    section[data-testid="stSidebar"] .stButton>button {
        width: 100%;
        background: rgba(255, 255, 255, 0.08);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 6px;
        text-align: left;
        font-weight: 500;
        margin-bottom: 4px;
        transition: all 0.3s ease;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background: #3F2B96;
        border-color: #ffffff;
    }

    /* Top Banner Header */
    .dashboard-header {
        background: linear-gradient(135deg, #3F2B96 0%, #1A103C 100%);
        padding: 22px 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(63, 43, 150, 0.2);
    }
    .dashboard-header h1 {
        margin: 0;
        font-size: 26px !important;
        font-weight: 800;
        letter-spacing: 0.5px;
    }

    /* Cards & Containers */
    div[data-testid="stForm"] {
        border: 1px solid #E0D8F0;
        border-radius: 10px;
        padding: 20px;
        background: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    
    .ems-badge {
        display: inline-block;
        background: #1A103C;
        color: #E7D6F7;
        border-radius: 15px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 700;
    }
</style>
''', unsafe_allow_html=True)

def get_logo_path():
    for filename in ["LOGO.png", "logo.png", "Logo.png"]:
        if os.path.exists(filename):
            return filename
    return None

def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def clean_student_name(name_str):
    if not name_str:
        return ""
    cleaned = re.sub(r'Class\s*\d+\s*\d*', '', name_str, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else name_str

def safe_text(txt):
    if not txt:
        return ""
    return str(txt).encode('latin-1', 'replace').decode('latin-1')

# ------------------------------------------------------------------
# Secure Password Gate
# ------------------------------------------------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            logo_path = get_logo_path()
            logo_base64 = get_image_base64(logo_path)
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="110" style="margin-bottom: 10px;" />' if logo_base64 else '<div style="font-size: 45px; margin-bottom: 10px;">🎓</div>'
            
            st.markdown(
                f'''
                <div style="background: linear-gradient(135deg, #3F2B96, #1A103C); padding: 35px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); text-align: center; color: white; margin-top: 30px;">
                    <div style="text-align: center;">{logo_html}</div>
                    <h1 style="margin: 15px 0 5px 0; font-size: 22px; font-weight: 800; color: #ffffff !important;">EXCELLENCE MODEL SCHOOL</h1>
                    <p style="margin: 0; font-size: 12px; color: #D4C5F9 !important;">Secure Enterprise Portal</p>
                </div>
                ''',
                unsafe_allow_html=True
            )
            st.write("")
            st.text_input("🔐 Enter System Password:", type="password", on_change=password_entered, key="password")
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("⚠️ Incorrect password, please try again!")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ------------------------------------------------------------------
# Supabase connection
# ------------------------------------------------------------------
@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])

sb = get_client()

DEFAULT_DESIGNATIONS = [
    'Principal', 'Vice Principal', 'Head Mistress', 'Coordinator', 'Incharge',
    'Class Teacher', 'Subject Teacher', 'Computer Operator', 'Accountant',
    'Admin Staff', 'Librarian', 'Lab Assistant', 'Gate Keeper', 'Security Guard', 'Maid', 'Peon',
]
DEFAULT_CAMPUSES = [
    'Kharadar Campus', 'Tower Campus', 'Sonia Arcade Campus', 'Moosa Lane Campus',
    'Pakistan Chowk Campus', 'Park View Campus', 'Federal B Area Campus',
]

DEFAULT_CLASSES = [
    "Montessori", "LKG", "UKG", "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", 
    "Class 6", "Class 7", "Class 8", "Class 9", "Matric"
]

# ------------------------------------------------------------------
# Data Helpers
# ------------------------------------------------------------------
def fetch_staff():
    res = sb.table("staff").select("*").order("id").execute()
    return res.data or []

def fetch_designations():
    res = sb.table("designations").select("label").order("label").execute()
    labels = [r["label"] for r in (res.data or [])]
    return labels or DEFAULT_DESIGNATIONS

def fetch_campuses():
    res = sb.table("campuses").select("label").order("label").execute()
    labels = [r["label"] for r in (res.data or [])]
    return labels or DEFAULT_CAMPUSES

def fetch_classes_list():
    try:
        res = sb.table("classes").select("label").order("id").execute()
        labels = [r["label"] for r in (res.data or [])]
        return labels if labels else DEFAULT_CLASSES
    except Exception:
        return DEFAULT_CLASSES

def next_staff_id(staff):
    nums = [int(re.search(r"(\d+)", s.get("id", "")).group(1)) for s in staff if re.search(r"(\d+)", s.get("id", ""))]
    n = (max(nums) + 1) if nums else 1
    return f"EMS-{n:03d}"

def next_student_id(students):
    nums = [int(re.search(r"(\d+)", s.get("id", "")).group(1)) for s in students if re.search(r"(\d+)", s.get("id", ""))]
    n = (max(nums) + 1) if nums else 1
    return f"STD-{n:03d}"

def fetch_students():
    res = sb.table("students").select("*").order("id").execute()
    data = res.data or []
    for s in data:
        if s.get("name"):
            s["name"] = clean_student_name(s["name"])
    return data

def add_student(record):
    if "status" not in record:
        record["status"] = "Active"
    sb.table("students").insert(record).execute()

def update_student(student_id, record):
    sb.table("students").update(record).eq("id", student_id).execute()

def fetch_fee_record(student_id, month_year):
    res = sb.table("fee_records").select("*").eq("student_id", student_id).eq("month_year", month_year).execute()
    return res.data[0] if res.data else None

def get_fee_statuses(student_id, month_year):
    rec = fetch_fee_record(student_id, month_year)
    if not rec or not rec.get("status"):
        return "Pending", "Pending"
    val = rec.get("status", "")
    m_stat = "Paid" if "Monthly:Paid" in val else "Pending"
    y_stat = "Paid" if "Yearly:Paid" in val else "Pending"
    if "Monthly:" not in val and "Yearly:" not in val:
        if val == "Paid":
            m_stat = "Paid"
            y_stat = "Paid"
        else:
            m_stat = "Pending"
            y_stat = "Pending"
    return m_stat, y_stat

def set_fee_status(student_id, month_year, m_stat, y_stat, amount=0):
    existing = fetch_fee_record(student_id, month_year)
    today = datetime.now().strftime("%Y-%m-%d")
    status_str = f"Monthly:{m_stat} | Yearly:{y_stat}"
    if existing:
        sb.table("fee_records").update({
            "status": status_str, 
            "paid_date": today,
            "amount": amount
        }).eq("id", existing["id"]).execute()
    else:
        sb.table("fee_records").insert({
            "student_id": student_id,
            "month_year": month_year,
            "status": status_str,
            "paid_date": today,
            "amount": amount
        }).execute()

def mark_challan_generated(student_id, month_year, include_yearly):
    existing = fetch_fee_record(student_id, month_year)
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if existing:
        sb.table("fee_records").update({
            "challan_generated": True,
            "challan_date": current_timestamp,
            "include_yearly_in_challan": include_yearly
        }).eq("id", existing["id"]).execute()
    else:
        sb.table("fee_records").insert({
            "student_id": student_id,
            "month_year": month_year,
            "status": "Monthly:Pending | Yearly:Pending",
            "challan_generated": True,
            "challan_date": current_timestamp,
            "include_yearly_in_challan": include_yearly
        }).execute()

def fetch_generated_challans(month_year):
    try:
        res = sb.table("fee_records").select("*").eq("month_year", month_year).eq("challan_generated", True).execute()
        return res.data or []
    except Exception:
        return []

# ------------------------------------------------------------------
# PDF Functions (Safe Encoding)
# ------------------------------------------------------------------
def generate_staff_pdf(data_rows, custom_fields_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, safe_text("Excellence Model School - Staff Report"), 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, safe_text(f"Total Records: {len(data_rows)}"), 0, 1, "C")
    pdf.ln(5)

    for s in data_rows:
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(230, 230, 250)
        pdf.cell(0, 8, safe_text(f"ID: {s.get('id')} | Name: {s.get('name')}"), 0, 1, "L", True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, safe_text(f"Designation: {s.get('designation')}  |  Campus: {s.get('campus', '—')}"), 0, 1, "L")
        pdf.cell(0, 6, safe_text(f"Father Name: {s.get('father_name', '—')}  |  Class Teacher: {s.get('class_teacher_of', '—')}"), 0, 1, "L")
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin1')

def generate_monthly_attendance_pdf(class_name, month_year_str, students_list):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, safe_text("Excellence Model School - Monthly Attendance Sheet"), 0, 1, "C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, safe_text(f"Class: {class_name}    |    Month: {month_year_str}"), 0, 1, "C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 250)
    pdf.cell(22, 7, "Roll No", 1, 0, "C", True)
    pdf.cell(48, 7, "Student Name", 1, 0, "C", True)
    for d in range(1, 32):
        pdf.cell(6.5, 7, str(d), 1, 0, "C", True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    for s in students_list:
        pdf.cell(22, 6, safe_text(s.get("id", "")), 1, 0, "C")
        pdf.cell(48, 6, safe_text(s.get("name", "")), 1, 0, "L")
        for d in range(1, 32):
            pdf.cell(6.5, 6, "", 1, 0, "C")
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

def generate_fee_challan_pdf(student, month_year, include_yearly=False):
    pdf = FPDF(orientation='P', unit='mm', format='A5')
    pdf.add_page()
    
    pdf.set_draw_color(63, 43, 150)
    pdf.set_line_width(0.8)
    pdf.rect(5, 5, 138, 200)
    
    pdf.set_font("Arial", "B", 13)
    pdf.set_xy(10, 10)
    pdf.cell(128, 6, safe_text("EXCELLENCE MODEL SCHOOL"), 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(128, 5, safe_text("Fee Payment Challan / Voucher"), 0, 1, "C")
    
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(10, 24, 133, 24)
    
    pdf.set_xy(10, 27)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(30, 6, "Student ID:", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(40, 6, safe_text(str(student.get("id", ""))), 0, 0)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 6, "Billing Month:", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(33, 6, safe_text(str(month_year)), 0, 1)
    
    pdf.set_xy(10, 34)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(30, 6, "Student Name:", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(40, 6, safe_text(str(student.get("name", ""))), 0, 0)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 6, "Class:", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(33, 6, safe_text(str(student.get("class_name", ""))), 0, 1)
    
    pdf.set_xy(10, 41)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(30, 6, "Father's Name:", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(98, 6, safe_text(str(student.get("father_name", ""))), 0, 1)
    
    pdf.ln(4)
    pdf.set_fill_color(63, 43, 150)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(90, 7, safe_text("  Fee Particulars"), 1, 0, "L", True)
    pdf.cell(33, 7, safe_text("Amount (Rs.)  "), 1, 1, "R", True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    
    monthly_fee = int(student.get("monthly_fee", 3500) or 3500)
    yearly_fee = int(student.get("yearly_fee", 5000) or 5000)
    
    pdf.cell(90, 7, safe_text(f"   Monthly Tuition Fee ({month_year})"), 1, 0, "L")
    pdf.cell(33, 7, safe_text(f"Rs. {monthly_fee:,}   "), 1, 1, "R")
    
    total_due = monthly_fee
    if include_yearly:
        pdf.cell(90, 7, safe_text("   Yearly Fee / Annual Charges"), 1, 0, "L")
        pdf.cell(33, 7, safe_text(f"Rs. {yearly_fee:,}   "), 1, 1, "R")
        total_due += yearly_fee
        
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(230, 230, 250)
    pdf.cell(90, 8, safe_text("   Total Payable Amount"), 1, 0, "L", True)
    pdf.cell(33, 8, safe_text(f"Rs. {total_due:,}   "), 1, 1, "R", True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(123, 5, safe_text("Instructions:"), 0, 1, "L")
    pdf.set_font("Arial", "", 8)
    pdf.cell(123, 4, safe_text("1. Please deposit fee before the 10th of every month."), 0, 1, "L")
    pdf.cell(123, 4, safe_text("2. Fee once paid is non-refundable."), 0, 1, "L")
    
    pdf.ln(25)
    pdf.cell(60, 5, safe_text("_________________________"), 0, 0, "C")
    pdf.cell(63, 5, safe_text("_________________________"), 0, 1, "C")
    pdf.set_font("Arial", "B", 8)
    pdf.cell(60, 5, safe_text("Cashier / Accountant Sign"), 0, 0, "C")
    pdf.cell(63, 5, safe_text("Principal Signature"), 0, 1, "C")
    
    return pdf.output(dest='S').encode('latin1')

def generate_id_cards_pdf(students_list):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    logo_path = get_logo_path()
    
    for i, s in enumerate(students_list):
        if i % 2 == 0:
            pdf.add_page()
            y_start = 15
        else:
            y_start = 110
            
        x_start = 30
        
        # Outer Card Border
        pdf.set_draw_color(63, 43, 150)
        pdf.set_line_width(0.8)
        pdf.rect(x_start, y_start, 150, 88)
        
        # Header Banner Background
        pdf.set_fill_color(63, 43, 150)
        pdf.rect(x_start, y_start, 150, 20, 'F')
        
        # Insert Logo if available on ID Card Header
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=x_start + 8, y=y_start + 2.5, w=15)
            except Exception:
                pass
        
        # Header Centered Text
        pdf.set_xy(x_start, y_start + 3)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(150, 6, safe_text("EXCELLENCE MODEL SCHOOL"), 0, 1, "C")
        pdf.set_font("Arial", "", 8)
        pdf.set_xy(x_start, y_start + 10)
        pdf.cell(150, 4, safe_text("STUDENT IDENTITY CARD"), 0, 1, "C")
        
        pdf.set_text_color(0, 0, 0)
        
        # Student Photo Box
        pdf.set_draw_color(150, 150, 150)
        pdf.set_line_width(0.4)
        pdf.rect(x_start + 10, y_start + 24, 28, 35)
        
        p_url = s.get("photo_url", "")
        if not p_url:
            pdf.set_xy(x_start + 10, y_start + 38)
            pdf.set_font("Arial", "", 8)
            pdf.cell(28, 5, safe_text("NO PHOTO"), 0, 0, "C")
            
        # Student Details Layout
        pdf.set_xy(x_start + 42, y_start + 24)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(25, 6, safe_text("GR No:"), 0, 0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(75, 6, safe_text(str(s.get("gr_number", "—"))), 0, 1)
        
        pdf.set_xy(x_start + 42, y_start + 31)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(25, 6, safe_text("Student ID:"), 0, 0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(75, 6, safe_text(str(s.get("id", ""))), 0, 1)
        
        pdf.set_xy(x_start + 42, y_start + 38)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(25, 6, safe_text("Name:"), 0, 0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(75, 6, safe_text(str(s.get("name", ""))), 0, 1)
        
        pdf.set_xy(x_start + 42, y_start + 45)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(25, 6, safe_text("Father Name:"), 0, 0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(75, 6, safe_text(str(s.get("father_name", ""))), 0, 1)
        
        pdf.set_xy(x_start + 42, y_start + 52)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(25, 6, safe_text("Class:"), 0, 0)
        pdf.set_font("Arial", "", 9)
        pdf.cell(75, 6, safe_text(str(s.get("class_name", ""))), 0, 1)
        
        # Emergency & Blood Group Row
        pdf.set_xy(x_start + 10, y_start + 63)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(25, 5, safe_text("Emergency No:"), 0, 0)
        pdf.set_font("Arial", "", 8)
        pdf.cell(48, 5, safe_text(str(s.get("contact_1", "—"))), 0, 0)
        
        pdf.set_font("Arial", "B", 8)
        pdf.cell(22, 5, safe_text("Blood Grp:"), 0, 0)
        pdf.set_font("Arial", "", 8)
        pdf.cell(25, 5, safe_text(str(s.get("blood_group", "—"))), 0, 1)
        
        # Perfectly Balanced & Centered Signature Section
        line_y = y_start + 78
        pdf.line(x_start + 15, line_y, x_start + 65, line_y)
        pdf.line(x_start + 85, line_y, x_start + 135, line_y)
        
        pdf.set_xy(x_start + 15, line_y + 1)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(50, 4, safe_text("Issued By Authority"), 0, 0, "C")
        
        pdf.set_xy(x_start + 85, line_y + 1)
        pdf.cell(50, 4, safe_text("Principal Signature"), 0, 1, "C")
        
    return pdf.output(dest='S').encode('latin1')

# ------------------------------------------------------------------
# Data Fetches
# ------------------------------------------------------------------
staff = fetch_staff()
students = fetch_students()
designations = fetch_designations()
campuses = fetch_campuses()
class_sequence = fetch_classes_list()

# ------------------------------------------------------------------
# SIDEBAR NAVIGATION MENU
# ------------------------------------------------------------------
with st.sidebar:
    logo_path = get_logo_path()
    logo_base64 = get_image_base64(logo_path)
    if logo_base64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" width="85" style="margin: 0 auto; display: block;" /></div>', unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 38px; text-align: center;'>🎓</div>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center; color: white; margin-top: 5px; font-size: 16px;'>EXCELLENCE MODEL SCHOOL</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #D4C5F9; font-size: 11px; margin-bottom: 20px;'>Enterprise Management ERP</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<p style='color: #D4C5F9; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;'>Main Navigation</p>", unsafe_allow_html=True)
    
    if "selected_menu" not in st.session_state:
        st.session_state["selected_menu"] = "📊 Dashboard Overview"

    if st.button("📊 Dashboard Overview", use_container_width=True):
        st.session_state["selected_menu"] = "📊 Dashboard Overview"
    if st.button("👥 Staff Management", use_container_width=True):
        st.session_state["selected_menu"] = "👥 Staff Management"
    if st.button("🎓 Student Admissions", use_container_width=True):
        st.session_state["selected_menu"] = "🎓 Student Admissions"
    if st.button("💳 Fee Management", use_container_width=True):
        st.session_state["selected_menu"] = "💳 Fee Management"
    if st.button("📅 Attendance Sheets", use_container_width=True):
        st.session_state["selected_menu"] = "📅 Attendance Sheets"

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    if st.button("🔒 Secure Logout", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()

menu_choice = st.session_state.get("selected_menu", "📊 Dashboard Overview")

# ==================================================================
# 1. DASHBOARD OVERVIEW
# ==================================================================
if menu_choice == "📊 Dashboard Overview":
    st.markdown('''
    <div class="dashboard-header">
        <h1>Dashboard & Quick Statistics</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Real-time summary of school operations and cloud metrics</p>
    </div>
    ''', unsafe_allow_html=True)

    active_students = [s for s in students if s.get("status", "Active") == "Active"]
    alumni_students = [s for s in students if s.get("status") == "Graduated"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Students", len(active_students))
    c2.metric("Graduated / Alumni", len(alumni_students))
    c3.metric("Total Staff Members", len(staff))
    c4.metric("System Status", "🟢 Live Sync")

    st.write("")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("🏫 Staff Members per Campus")
        if staff:
            df_staff = pd.DataFrame(staff)
            if "campus" in df_staff.columns:
                st.bar_chart(df_staff["campus"].fillna("Unassigned").value_counts())
    with col_chart2:
        st.subheader("🎓 Active Students per Class Distribution")
        if active_students:
            df_std = pd.DataFrame(active_students)
            if "class_name" in df_std.columns:
                st.bar_chart(df_std["class_name"].fillna("Unassigned").value_counts())

# ==================================================================
# 2. STAFF MANAGEMENT
# ==================================================================
elif menu_choice == "👥 Staff Management":
    st.markdown('''
    <div class="dashboard-header">
        <h1>Staff Management & Directory</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Manage faculty, designations, campuses and employee records</p>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("➕ Add New Staff Member", expanded=False):
        with st.form("add_staff_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Staff Full Name *")
            father_name = c2.text_input("Father's Name")
            designation = c1.selectbox("Category / Designation *", [""] + designations)
            campus = c2.selectbox("Campus Location", [""] + campuses)
            class_teacher_of = c1.text_input("Class Teacher Of (if applicable)")
            subject_teacher = c2.text_input("Subject Teacher (if applicable)")

            if st.form_submit_button("Save Staff Record", type="primary"):
                if not name.strip() or not designation:
                    st.error("Please enter Name and Designation.")
                else:
                    sb.table("staff").insert({
                        "id": next_staff_id(staff),
                        "name": name.strip(),
                        "father_name": father_name.strip(),
                        "designation": designation,
                        "class_teacher_of": class_teacher_of.strip(),
                        "subject_teacher": subject_teacher.strip(),
                        "campus": campus,
                    }).execute()
                    st.success(f"Staff member {name} added successfully.")
                    st.rerun()

    f_col1, f_col2 = st.columns([4, 2])
    with f_col1:
        search_staff = st.text_input("🔍 Search Staff", placeholder="Filter by name, designation or campus...")
    with f_col2:
        st.write("")
        st.write("")
        if staff:
            st.download_button("📄 Download Staff PDF", generate_staff_pdf(staff, []), "staff_report.pdf", "application/pdf", use_container_width=True)

    filtered_staff = staff
    if search_staff.strip():
        q = search_staff.strip().lower()
        filtered_staff = [s for s in staff if any(q in (v or "").lower() for v in [s.get("name"), s.get("designation"), s.get("campus")])]

    st.subheader(f"📋 Staff Directory Records ({len(filtered_staff)})")
    for s in filtered_staff:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5, 1])
            c1.markdown(f"**{s['name']}**<br>`{s.get('id')}`", unsafe_allow_html=True)
            c2.markdown(f"<span class='ems-badge'>{s.get('designation','')}</span> | Father: {s.get('father_name','—')} | Campus: {s.get('campus','—')}", unsafe_allow_html=True)
            if c3.button("Delete", key=f"del_staff_{s['id']}"):
                sb.table("staff").delete().eq("id", s["id"]).execute()
                st.rerun()

# ==================================================================
# 3. STUDENT ADMISSIONS
# ==================================================================
elif menu_choice == "🎓 Student Admissions":
    st.markdown('''
    <div class="dashboard-header">
        <h1>Student Admissions & Class Records</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Register students, manage fees, CSV import/export, and annual class promotions</p>
    </div>
    ''', unsafe_allow_html=True)
    
    tab_single, tab_edit, tab_idcard, tab_bulk, tab_promo, tab_classes = st.tabs([
        "➕ Single Admission", 
        "✏️ Edit & Search Student", 
        "🪪 ID Cards Generator", 
        "📥 CSV / Excel Import & Export", 
        "🚀 Annual Class Promotion", 
        "🏫 Manage Classes"
    ])
    
    with tab_single:
        with st.form("student_admission_form", clear_on_submit=True):
            st.subheader("New Student Registration Form")
            
            sc1, sc2 = st.columns(2)
            with sc1:
                std_name = st.text_input("Student Full Name *")
                std_father = st.text_input("Father's Name *")
                std_gr = st.text_input("GR Number (General Register No) *")
                std_class = st.selectbox("Assign Class", class_sequence)
                std_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                std_dob = st.text_input("Date of Birth (e.g. 15-Aug-2020)")
                std_bform = st.text_input("B-Form / CNIC Number")
                
            with sc2:
                std_fee = st.number_input("Monthly Fee Amount (Rs.)", min_value=0, value=3500, step=500)
                std_yearly_fee = st.number_input("Yearly Fee / Annual Charges (Rs.)", min_value=0, value=5000, step=500)
                contact_1 = st.text_input("Primary Contact (Contact 1) *")
                contact_2 = st.text_input("Secondary Contact (Contact 2)")
                whatsapp_no = st.text_input("WhatsApp Number *")
                blood_group = st.selectbox("Blood Group", ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            
            address = st.text_area("Residential Address *")
            prev_school = st.text_input("Previous School / Last Attended Class (if any)")
            
            std_photo = st.file_uploader("Upload Student Photograph (JPG/PNG)", type=["jpg", "jpeg", "png"])
                
            if st.form_submit_button("Register Student", type="primary"):
                if std_name.strip() and std_father.strip() and std_gr.strip() and contact_1.strip() and whatsapp_no.strip() and address.strip():
                    try:
                        new_s_id = next_student_id(students)
                        
                        photo_url_val = ""
                        if std_photo is not None:
                            bytes_data = std_photo.getvalue()
                            encoded_img = base64.b64encode(bytes_data).decode('utf-8')
                            photo_url_val = f"data:image/{std_photo.type.split('/')[-1]};base64,{encoded_img}"

                        student_data = {
                            "id": new_s_id,
                            "gr_number": std_gr.strip(),
                            "name": std_name.strip(),
                            "father_name": std_father.strip(),
                            "class_name": std_class,
                            "monthly_fee": std_fee,
                            "yearly_fee": std_yearly_fee,
                            "status": "Active",
                            "contact_1": contact_1.strip(),
                            "contact_2": contact_2.strip(),
                            "whatsapp": whatsapp_no.strip(),
                            "address": address.strip(),
                            "dob": std_dob.strip(),
                            "gender": std_gender,
                            "b_form": std_bform.strip(),
                            "blood_group": blood_group,
                            "previous_school": prev_school.strip(),
                            "photo_url": photo_url_val
                        }
                        add_student(student_data)
                        st.success(f"Student {std_name} ({new_s_id} | GR: {std_gr}) successfully enrolled in {std_class}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving student: {e}")
                else:
                    st.warning("Please fill in all mandatory fields (*): Student Name, Father's Name, GR Number, Contact 1, WhatsApp Number, and Address.")

    with tab_edit:
        st.subheader("🔍 Search & Edit Student Record (Update GR, Picture & Details)")
        search_query = st.text_input("Search Student by Name, ID, GR Number, or Phone Number", placeholder="e.g. Ali, STD-001, GR-102...")
        
        filtered_search_list = []
        if search_query.strip():
            q = search_query.strip().lower()
            filtered_search_list = [s for s in students if any(q in (str(v) or "").lower() for v in [s.get("id"), s.get("gr_number"), s.get("name"), s.get("contact_1"), s.get("whatsapp")])]
        
        if search_query.strip() and not filtered_search_list:
            st.info("No matching students found.")
        elif filtered_search_list:
            student_choice_options = {f"{s['name']} (GR: {s.get('gr_number','—')} | ID: {s['id']} | Class: {s.get('class_name','—')})": s for s in filtered_search_list}
            selected_edit_label = st.selectbox("Select Student to Edit", list(student_choice_options.keys()))
            sel_s = student_choice_options[selected_edit_label]
            
            st.divider()
            
            col_img, col_det = st.columns([1, 3])
            with col_img:
                st.write("### Current Photo")
                p_url = sel_s.get("photo_url")
                if p_url and p_url.startswith("data:image"):
                    st.markdown(f'<img src="{p_url}" width="120" style="border-radius: 8px; border: 2px solid #3F2B96;" />', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-size: 60px;">👤</div>', unsafe_allow_html=True)
                    st.write("No photo uploaded")
            
            with col_det:
                st.markdown(f"**Student ID:** `{sel_s.get('id')}`")
                st.markdown(f"**GR Number:** `{sel_s.get('gr_number', '—')}`")
                st.markdown(f"**Current Class:** {sel_s.get('class_name')}")
                st.markdown(f"**Status:** {sel_s.get('status', 'Active')}")
            
            st.write("### Update Student Details & Photograph")
            with st.form(f"edit_student_form_{sel_s['id']}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_name = st.text_input("Student Full Name *", value=sel_s.get("name", ""))
                    e_father = st.text_input("Father's Name *", value=sel_s.get("father_name", ""))
                    e_gr = st.text_input("GR Number *", value=sel_s.get("gr_number", ""))
                    
                    curr_cls = sel_s.get("class_name", class_sequence[0] if class_sequence else "")
                    cls_idx = class_sequence.index(curr_cls) if curr_cls in class_sequence else 0
                    e_class = st.selectbox("Assign Class", class_sequence, index=cls_idx)
                    
                    genders = ["Male", "Female", "Other"]
                    g_idx = genders.index(sel_s.get("gender", "Male")) if sel_s.get("gender", "Male") in genders else 0
                    e_gender = st.selectbox("Gender", genders, index=g_idx)
                    
                    e_dob = st.text_input("Date of Birth", value=sel_s.get("dob", ""))
                    e_bform = st.text_input("B-Form / CNIC Number", value=sel_s.get("b_form", ""))
                    
                with ec2:
                    e_fee = st.number_input("Monthly Fee Amount (Rs.)", min_value=0, value=int(sel_s.get("monthly_fee", 3500) or 3500), step=500)
                    e_yearly_fee = st.number_input("Yearly Fee / Annual Charges (Rs.)", min_value=0, value=int(sel_s.get("yearly_fee", 5000) or 5000), step=500)
                    e_contact1 = st.text_input("Primary Contact (Contact 1) *", value=sel_s.get("contact_1", ""))
                    e_contact2 = st.text_input("Secondary Contact (Contact 2)", value=sel_s.get("contact_2", ""))
                    e_whatsapp = st.text_input("WhatsApp Number *", value=sel_s.get("whatsapp", ""))
                    
                    blood_groups = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                    bg_idx = blood_groups.index(sel_s.get("blood_group", "Unknown")) if sel_s.get("blood_group", "Unknown") in blood_groups else 0
                    e_blood = st.selectbox("Blood Group", blood_groups, index=bg_idx)
                
                e_address = st.text_area("Residential Address *", value=sel_s.get("address", ""))
                e_prev_school = st.text_input("Previous School / Last Attended Class", value=sel_s.get("previous_school", ""))
                
                new_uploaded_photo = st.file_uploader("Upload New Student Photograph (JPG/PNG) - Leave empty to keep existing", type=["jpg", "jpeg", "png"])
                
                if st.form_submit_button("Update Student Record", type="primary"):
                    try:
                        final_photo_url = sel_s.get("photo_url", "")
                        if new_uploaded_photo is not None:
                            b_data = new_uploaded_photo.getvalue()
                            enc_img = base64.b64encode(b_data).decode('utf-8')
                            final_photo_url = f"data:image/{new_uploaded_photo.type.split('/')[-1]};base64,{enc_img}"
                        
                        updated_payload = {
                            "name": str(e_name).strip() if e_name else "",
                            "father_name": str(e_father).strip() if e_father else "",
                            "gr_number": str(e_gr).strip() if e_gr else "",
                            "class_name": e_class,
                            "monthly_fee": e_fee,
                            "yearly_fee": e_yearly_fee,
                            "contact_1": str(e_contact1).strip() if e_contact1 else "",
                            "contact_2": str(e_contact2).strip() if e_contact2 else "",
                            "whatsapp": str(e_whatsapp).strip() if e_whatsapp else "",
                            "address": str(e_address).strip() if e_address else "",
                            "dob": str(e_dob).strip() if e_dob else "",
                            "gender": e_gender,
                            "b_form": str(e_bform).strip() if e_bform else "",
                            "blood_group": e_blood,
                            "previous_school": str(e_prev_school).strip() if e_prev_school else "",
                            "photo_url": final_photo_url
                        }
                        update_student(sel_s["id"], updated_payload)
                        st.success(f"Student {e_name} ({sel_s['id']}) updated successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error updating student: {ex}")

    with tab_idcard:
        st.subheader("🪪 Automatic Student ID Card Generator (Class-wise & Individual)")
        st.write("Generate professional printable ID cards featuring School Theme Colors, Student Photograph, GR Number, Name, Father Name, Class, and Emergency Contact.")
        
        id_mode = st.radio("Choose Generation Mode", ["Class-wise ID Cards (All Students in a Class)", "Individual Student ID Card"], horizontal=True)
        
        active_students_list = [s for s in students if s.get("status", "Active") == "Active"]
        
        if id_mode == "Class-wise ID Cards (All Students in a Class)":
            idc_class = st.selectbox("Select Class for ID Cards", class_sequence, key="idc_class_sel")
            cls_students = [s for s in active_students_list if s.get("class_name") == idc_class]
            
            st.write(f"Total active students in **{idc_class}**: **{len(cls_students)}**")
            
            if not cls_students:
                st.info(f"No active students found in {idc_class}.")
            else:
                id_pdf_bytes = generate_id_cards_pdf(cls_students)
                st.download_button(
                    label=f"📥 Download Class {idc_class} ID Cards (.PDF)",
                    data=id_pdf_bytes,
                    file_name=f"ID_Cards_{idc_class.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
        else:
            if not active_students_list:
                st.info("No active students found.")
            else:
                ind_options = {f"{s['name']} (GR: {s.get('gr_number','—')} | Class: {s.get('class_name','—')})": s for s in active_students_list}
                selected_ind_label = st.selectbox("Select Individual Student", list(ind_options.keys()), key="ind_std_sel")
                selected_ind_obj = ind_options[selected_ind_label]
                
                ind_pdf_bytes = generate_id_cards_pdf([selected_ind_obj])
                st.download_button(
                    label=f"📥 Download ID Card for {selected_ind_obj['name']} (.PDF)",
                    data=ind_pdf_bytes,
                    file_name=f"ID_Card_{selected_ind_obj['id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

    with tab_bulk:
        st.subheader("📁 Bulk Import / Export Students (CSV)")
        st.write("You can download the existing student list or template as a CSV file (including GR Number column), fill it, and upload it back here.")
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            if students:
                df_export = pd.DataFrame(students)
                expected_cols = ["id", "gr_number", "name", "father_name", "class_name", "monthly_fee", "yearly_fee", "status", "contact_1", "contact_2", "whatsapp", "address", "dob", "gender", "b_form", "blood_group", "previous_school"]
                existing_cols = [c for c in expected_cols if c in df_export.columns]
                csv_data = df_export[existing_cols].to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Existing Students (CSV)",
                    data=csv_data,
                    file_name="students_list.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No students available to export.")
                
        with col_ex2:
            template_df = pd.DataFrame([{
                "gr_number": "GR-1001",
                "name": "Ali Khan",
                "father_name": "Muhammad Khan",
                "class_name": class_sequence[0] if class_sequence else "Class 1",
                "monthly_fee": 3500,
                "yearly_fee": 5000,
                "status": "Active",
                "contact_1": "03001234567",
                "contact_2": "03219876543",
                "whatsapp": "03001234567",
                "address": "House 123, Street 4, Karachi",
                "dob": "12-Jan-2018",
                "gender": "Male",
                "b_form": "42101-1234567-1",
                "blood_group": "B+",
                "previous_school": "None"
            }])
            template_csv = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📋 Download CSV Template",
                data=template_csv,
                file_name="student_import_template.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        st.divider()
        st.write("### Upload Filled CSV File")
        uploaded_csv = st.file_uploader("Upload CSV file containing students data", type=["csv"])
        
        if uploaded_csv is not None:
            try:
                import_df = pd.read_csv(uploaded_csv)
                st.write("Preview of uploaded data:", import_df.head())
                
                if st.button("🚀 Confirm & Import Students", type="primary"):
                    current_students = fetch_students()
                    success_count = 0
                    for _, row in import_df.iterrows():
                        name_val = str(row.get("name", "")).strip()
                        father_val = str(row.get("father_name", "")).strip()
                        if not name_val or name_val.lower() == "nan":
                            continue
                        
                        gr_val = str(row.get("gr_number", "")).strip()
                        class_val = str(row.get("class_name", class_sequence[0] if class_sequence else "Class 1")).strip()
                        m_fee_val = int(row.get("monthly_fee", 3500) or 3500)
                        y_fee_val = int(row.get("yearly_fee", 5000) or 5000)
                        status_val = str(row.get("status", "Active")).strip()
                        
                        new_id = next_student_id(current_students)
                        current_students.append({"id": new_id})
                        
                        sb.table("students").insert({
                            "id": new_id,
                            "gr_number": gr_val if gr_val and gr_val.lower() != "nan" else "",
                            "name": name_val,
                            "father_name": father_val,
                            "class_name": class_val,
                            "monthly_fee": m_fee_val,
                            "yearly_fee": y_fee_val,
                            "status": status_val if status_val in ["Active", "Graduated"] else "Active",
                            "contact_1": str(row.get("contact_1", "")).strip(),
                            "contact_2": str(row.get("contact_2", "")).strip(),
                            "whatsapp": str(row.get("whatsapp", "")).strip(),
                            "address": str(row.get("address", "")).strip(),
                            "dob": str(row.get("dob", "")).strip(),
                            "gender": str(row.get("gender", "Male")).strip(),
                            "b_form": str(row.get("b_form", "")).strip(),
                            "blood_group": str(row.get("blood_group", "Unknown")).strip(),
                            "previous_school": str(row.get("previous_school", "")).strip(),
                            "photo_url": ""
                        }).execute()
                        success_count += 1
                        
                    st.success(f"Successfully imported {success_count} students!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing CSV file: {e}")

    with tab_promo:
        st.subheader("🚀 Annual Class Promotion & Session Upgrade")
        sequence_str = " ➔ ".join(class_sequence)
        st.info(f"Here you can run the annual promotion following this sequence: **{sequence_str}**. The last class in this sequence will automatically be marked as 'Graduated / Alumni'.")

        active_count = len([s for s in students if s.get("status", "Active") == "Active"])
        st.write(f"Total Active Students ready for promotion check: **{active_count}**")

        if st.button("✨ Run Global Annual Promotion", type="primary"):
            try:
                all_stds = fetch_students()
                promoted_count = 0
                graduated_count = 0
                last_class = class_sequence[-1] if class_sequence else "Matric"

                for s in all_stds:
                    if s.get("status", "Active") != "Active":
                        continue
                    
                    curr_cls = s.get("class_name")
                    s_id = s.get("id")

                    if curr_cls == last_class:
                        sb.table("students").update({"status": "Graduated"}).eq("id", s_id).execute()
                        graduated_count += 1
                    elif curr_cls in class_sequence:
                        idx = class_sequence.index(curr_cls)
                        if idx + 1 < len(class_sequence):
                            next_cls = class_sequence[idx + 1]
                            sb.table("students").update({"class_name": next_cls}).eq("id", s_id).execute()
                            promoted_count += 1

                st.success(f"Promotion completed successfully! {promoted_count} students promoted to next classes, and {graduated_count} {last_class} students moved to Alumni/Graduated records.")
                st.rerun()
            except Exception as e:
                st.error(f"Error during promotion: {e}")

    with tab_classes:
        st.subheader("🏫 Manage Classes (Add & Remove)")
        st.write("Here you can add new classes or remove unwanted classes from the system.")

        col_add_cls, col_list_cls = st.columns([1, 1])

        with col_add_cls:
            with st.form("add_new_class_form", clear_on_submit=True):
                new_cls_name = st.text_input("New Class Name (e.g. Nursery)")
                if st.form_submit_button("Add Class", type="primary"):
                    if new_cls_name.strip():
                        c_name = new_cls_name.strip()
                        if c_name in class_sequence:
                            st.warning("This class already exists.")
                        else:
                            try:
                                sb.table("classes").insert({"label": c_name}).execute()
                                st.success(f"Class '{c_name}' added successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error adding class: {e}")
                    else:
                        st.warning("Please enter a class name.")

        with col_list_cls:
            st.write("### Current Active Classes")
            for c in class_sequence:
                rc1, rc2 = st.columns([3, 1])
                rc1.write(f"• **{c}**")
                if rc2.button("Remove", key=f"del_cls_{c}"):
                    try:
                        sb.table("classes").delete().eq("label", c).execute()
                        st.success(f"Class '{c}' removed.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==================================================================
# 4. FEE MANAGEMENT
# ==================================================================
elif menu_choice == "💳 Fee Management":
    st.markdown('''
    <div class="dashboard-header">
        <h1>Fee Management & Ledgers</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Manage student dues, fee payments, and financial collection reports</p>
    </div>
    ''', unsafe_allow_html=True)

    tab_rec, tab_challan, tab_rep = st.tabs(["💵 Fee Collection & Records", "🖨️ Fee Challan Generator", "📊 Collection Reports & Ledger"])
    
    with tab_rec:
        f_c1, f_c2 = st.columns(2)
        selected_class_fee = f_c1.selectbox("Select Class / All Classes", ["All Active Classes"] + class_sequence, key="fee_class_select")
        
        current_month_default = datetime.now().strftime("%B %Y")
        target_month_fee = f_c2.text_input("Billing Month & Year", value=current_month_default, key="fee_month_input")
        
        if selected_class_fee == "All Active Classes":
            class_students = [s for s in students if s.get("status", "Active") == "Active"]
        else:
            class_students = [s for s in students if s.get("class_name") == selected_class_fee and s.get("status", "Active") == "Active"]
        
        st.subheader(f"Students in {selected_class_fee} ({len(class_students)})")
        
        if not class_students:
            st.info(f"No active students found.")
        else:
            for s in class_students:
                s_id = s["id"]
                s_name = s["name"]
                s_cls = s.get("class_name", "")
                m_fee = int(s.get("monthly_fee") or 3500)
                y_fee = int(s.get("yearly_fee") or 5000)
                
                m_stat, y_stat = get_fee_statuses(s_id, target_month_fee)
                
                with st.container(border=True):
                    cols = st.columns([3, 2, 2, 2])
                    display_title = f"**{s_name}** (`{s_id}` | GR: `{s.get('gr_number','—')}`)" + (f" — *Class: {s_cls}*" if selected_class_fee == "All Active Classes" else "")
                    cols[0].markdown(display_title + f"<br>Father: {s.get('father_name','—')} | Cont: {s.get('contact_1','—')}", unsafe_allow_html=True)
                    cols[1].markdown(f"Monthly: **Rs. {m_fee:,}**")
                    cols[2].markdown(f"Yearly: **Rs. {y_fee:,}**")
                    
                    status_label = f"M:{m_stat} | Y:{y_stat}"
                    cols[3].markdown(f"Status: `{status_label}`")
                    
                    btn_cols = st.columns(3)
                    if btn_cols[0].button(f"{'✅ Monthly Paid' if m_stat=='Paid' else '⏳ Mark Monthly Paid'}", key=f"m_paid_{s_id}_{target_month_fee}"):
                        new_m = "Pending" if m_stat=="Paid" else "Paid"
                        total_amt = (m_fee if new_m=="Paid" else 0) + (y_fee if y_stat=="Paid" else 0)
                        set_fee_status(s_id, target_month_fee, new_m, y_stat, total_amt)
                        st.rerun()
                        
                    if btn_cols[1].button(f"{'✅ Yearly Paid' if y_stat=='Paid' else '⏳ Mark Yearly Paid'}", key=f"y_paid_{s_id}_{target_month_fee}"):
                        new_y = "Pending" if y_stat=="Paid" else "Paid"
                        total_amt = (m_fee if m_stat=="Paid" else 0) + (y_fee if new_y=="Paid" else 0)
                        set_fee_status(s_id, target_month_fee, m_stat, new_y, total_amt)
                        st.rerun()

    with tab_challan:
        st.subheader("🖨️ Generate & Download Fee Challan (PDF)")
        st.write("Challans can only be generated for students whose monthly fee is marked as **'Paid'**.")
        
        ch_c1, ch_c2, ch_c3 = st.columns([2, 2, 1])
        ch_class = ch_c1.selectbox("Filter Class for Challan", class_sequence, key="ch_class_sel")
        ch_month = ch_c3.text_input("Month / Year", value=datetime.now().strftime("%B %Y"), key="ch_month_input")
        
        class_filtered_students = []
        for s in students:
            if s.get("class_name") == ch_class and s.get("status", "Active") == "Active":
                m_stat, _ = get_fee_statuses(s["id"], ch_month)
                if m_stat == "Paid":
                    class_filtered_students.append(s)
        
        if not class_filtered_students:
            st.warning(f"No students with **Paid** monthly fee found in {ch_class} for {ch_month}. Please mark the fee as Paid from the 'Fee Collection & Records' tab first.")
        else:
            student_options = {f"{s['name']} (GR: {s.get('gr_number','—')} | ID: {s['id']})": s for s in class_filtered_students}
            selected_ch_student_label = ch_c2.selectbox("Select Student (Paid Only)", list(student_options.keys()), key="ch_std_sel")
            selected_student_obj = student_options[selected_ch_student_label]
            
            include_yearly_in_challan = st.checkbox("Include Yearly Fee in this Challan Voucher", value=False)
            
            st.write("")
            if selected_student_obj:
                challan_pdf_bytes = generate_fee_challan_pdf(selected_student_obj, ch_month, include_yearly=include_yearly_in_challan)
                
                if st.download_button(
                    label=f"📄 Download Fee Challan for {selected_student_obj['name']} (.PDF)",
                    data=challan_pdf_bytes,
                    file_name=f"Fee_Challan_{selected_student_obj['id']}_{ch_month.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                ):
                    mark_challan_generated(selected_student_obj['id'], ch_month, include_yearly_in_challan)

        st.divider()
        st.subheader(f"📋 Challans Generated for: {ch_month}")
        generated_list = fetch_generated_challans(ch_month)
        
        if not generated_list:
            st.info(f"No challans generated yet for {ch_month}.")
        else:
            gen_df_data = []
            student_map = {s["id"]: s for s in students}
            for g in generated_list:
                sid = g.get("student_id")
                st_info = student_map.get(sid, {})
                gen_df_data.append({
                    "Student ID": sid,
                    "GR Number": st_info.get("gr_number", "—"),
                    "Student Name": st_info.get("name", "Unknown"),
                    "Class": st_info.get("class_name", "—"),
                    "Yearly Fee Included": "Yes" if g.get("include_yearly_in_challan") else "No",
                    "Generated Date & Time": g.get("challan_date", "—")
                })
            st.dataframe(pd.DataFrame(gen_df_data), use_container_width=True)

    with tab_rep:
        st.subheader("📊 Financial Collection Reports & Ledger Export")
        rep_col1, rep_col2, rep_col3 = st.columns(3)
        report_month = rep_col1.text_input("Report Month & Year", value=datetime.now().strftime("%B %Y"), key="rep_month")
        report_class = rep_col2.selectbox("Select Class / All Classes", ["All Active Classes"] + class_sequence, key="rep_class")
        
        filter_by_date = rep_col3.checkbox("Filter by Specific Paid Date?", value=False)
        target_date_str = None
        if filter_by_date:
            target_date = rep_col3.date_input("Select Date", datetime.now())
            target_date_str = target_date.strftime("%Y-%m-%d")
            
        target_students = students if report_class == "All Active Classes" else [s for s in students if s.get("class_name") == report_class and s.get("status", "Active") == "Active"]
        
        if not target_students:
            st.info("No students found for this selection.")
        else:
            ledger_data = []
            total_expected = 0
            total_collected = 0
            total_collected_on_date = 0
            total_remaining = 0
            
            for s in target_students:
                s_id = s["id"]
                m_fee = int(s.get("monthly_fee") or 3500)
                y_fee = int(s.get("yearly_fee") or 5000)
                
                m_stat, y_stat = get_fee_statuses(s_id, report_month)
                rec = fetch_fee_record(s_id, report_month)
                
                paid_amt = rec.get("amount", 0) if rec else 0
                paid_date = rec.get("paid_date", "") if rec else ""
                is_challan_gen = "Yes" if (rec and rec.get("challan_generated")) else "No"
                
                if m_stat == "Pending":
                    total_remaining += m_fee
                if y_stat == "Pending":
                    total_remaining += y_fee
                    
                total_collected += paid_amt
                
                if target_date_str and paid_date == target_date_str:
                    total_collected_on_date += paid_amt
                    
                ledger_data.append({
                    "Student ID": s_id,
                    "GR Number": s.get("gr_number", "—"),
                    "Student Name": s.get("name"),
                    "Father's Name": s.get("father_name", "—"),
                    "Contact 1": s.get("contact_1", "—"),
                    "WhatsApp": s.get("whatsapp", "—"),
                    "Class": s.get("class_name"),
                    "Monthly Fee Status": m_stat,
                    "Yearly Fee Status": y_stat,
                    "Challan Generated": is_challan_gen,
                    "Total Paid (Rs.)": paid_amt,
                    "Paid Date": paid_date
                })
            
            total_expected = total_collected + total_remaining
            
            st.markdown("### 💰 Collection Overview")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Expected", f"Rs. {total_expected:,}")
            m2.metric(f"Total Collected ({report_month})", f"Rs. {total_collected:,}")
            m3.metric("Total Remaining", f"Rs. {total_remaining:,}")
            
            if target_date_str:
                m4.metric(f"Collected on {target_date_str}", f"Rs. {total_collected_on_date:,}")
            else:
                m4.metric("Today's Collection Filter", "Not Active")
            
            st.divider()
            
            if target_date_str:
                display_data = [d for d in ledger_data if d["Paid Date"] == target_date_str]
                st.write(f"Showing filtered ledger for **{report_class}** on **{target_date_str}** ({len(display_data)} records):")
            else:
                display_data = ledger_data
                st.write(f"Showing complete ledger preview for **{report_class}** ({len(display_data)} students):")
            
            df_ledger = pd.DataFrame(display_data)
            st.dataframe(df_ledger, use_container_width=True)
            
            csv_ledger = df_ledger.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Financial Ledger as CSV",
                data=csv_ledger,
                file_name=f"Financial_Ledger_{report_class.replace(' ', '_')}_{report_month.replace(' ', '_')}.csv",
                mime="text/csv",
                type="primary"
            )

# ==================================================================
# 5. ATTENDANCE SHEETS
# ==================================================================
elif menu_choice == "📅 Attendance Sheets":
    st.markdown('''
    <div class="dashboard-header">
        <h1>Monthly Attendance Sheets</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Generate and print monthly attendance registers for any class</p>
    </div>
    ''', unsafe_allow_html=True)

    att_c1, att_c2 = st.columns(2)
    selected_att_class = att_c1.selectbox("Select Class / All Classes", ["All Active Classes"] + class_sequence, key="att_class_select")
    att_month = att_c2.text_input("Attendance Month & Year", value=datetime.now().strftime("%B %Y"), key="att_month_input")

    att_students = students if selected_att_class == "All Active Classes" else [s for s in students if s.get("class_name") == selected_att_class and s.get("status", "Active") == "Active"]

    st.write(f"### Attendance Sheet Preview: {selected_att_class} ({att_month})")
    
    if not att_students:
        st.info("No students found for attendance sheet generation.")
    else:
        att_pdf_bytes = generate_monthly_attendance_pdf(selected_att_class, att_month, att_students)
        st.download_button(
            "📥 Click Here to Download PDF Attendance Sheet",
            data=att_pdf_bytes,
            file_name=f"attendance_{selected_att_class.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary"
        )
            
        table_html = f'''
        <div style="background: white; padding: 20px; border-radius: 10px; border: 1px solid #E0D8F0; overflow-x: auto;">
            <h3 style="text-align: center; margin-bottom: 5px;">Excellence Model School - Monthly Attendance Sheet</h3>
            <p style="text-align: center; color: #666; margin-top: 0;">Class: <b>{selected_att_class}</b> | Month: <b>{att_month}</b></p>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <thead>
                    <tr style="background-color: #3F2B96; color: white;">
                        <th style="border: 1px solid #ccc; padding: 6px; width: 80px;">GR No</th>
                        <th style="border: 1px solid #ccc; padding: 6px; text-align: left;">Student Name</th>
        '''
        for d in range(1, 32):
            table_html += f'<th style="border: 1px solid #ccc; padding: 4px; width: 22px; text-align: center;">{d}</th>'
        table_html += "</tr></thead><tbody>"

        for s in att_students:
            s_name = clean_student_name(s.get("name", ""))
            table_html += f'''
                <tr>
                    <td style="border: 1px solid #ccc; padding: 5px; text-align: center; font-weight: bold;">{s.get("gr_number", "—")}</td>
                    <td style="border: 1px solid #ccc; padding: 5px;">{s_name}</td>
            '''
            for d in range(1, 32):
                table_html += '<td style="border: 1px solid #ccc; padding: 5px;"></td>'
            table_html += "</tr>"

        table_html += "</tbody></table></div>"
        st.markdown(table_html, unsafe_allow_html=True)
