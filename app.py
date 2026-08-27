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
st.markdown("""
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
""", unsafe_allow_html=True)

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
                f"""
                <div style="background: linear-gradient(135deg, #3F2B96, #1A103C); padding: 35px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.15); text-align: center; color: white; margin-top: 30px;">
                    {logo_html}
                    <h1 style="margin: 15px 0 5px 0; font-size: 22px; font-weight: 800; color: #ffffff !important;">EXCELLENCE MODEL SCHOOL</h1>
                    <p style="margin: 0; font-size: 12px; color: #D4C5F9 !important;">Secure Enterprise Portal</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            st.text_input("🔐 Enter System Password:", type="password", on_change=password_entered, key="password")
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("😕 Incorrect password, please try again!")
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

def fetch_custom_fields():
    res = sb.table("custom_fields").select("*").order("label").execute()
    return res.data or []

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
    return res.data or []

def add_student(record):
    sb.table("students").insert(record).execute()

def update_student_fee(std_id, monthly_fee, yearly_fee):
    sb.table("students").update({"monthly_fee": monthly_fee, "yearly_fee": yearly_fee}).eq("id", std_id).execute()

def delete_student(std_id):
    sb.table("students").delete().eq("id", std_id).execute()

def fetch_fee_records_for_student(student_id):
    res = sb.table("fee_records").select("*").eq("student_id", student_id).execute()
    return res.data or []

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
        sb.table("fee_records").update({"status": status_str, "paid_date": today}).eq("id", existing["id"]).execute()
    else:
        sb.table("fee_records").insert({
            "student_id": student_id,
            "month_year": month_year,
            "status": status_str,
            "paid_date": today,
            "amount": amount
        }).execute()

# ------------------------------------------------------------------
# PDF Functions
# ------------------------------------------------------------------
def generate_staff_pdf(data_rows, custom_fields_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Excellence Model School - Staff Report", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Total Records: {len(data_rows)}", 0, 1, "C")
    pdf.ln(5)

    for s in data_rows:
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(230, 230, 250)
        pdf.cell(0, 8, f"ID: {s.get('id')} | Name: {s.get('name')}", 0, 1, "L", True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Designation: {s.get('designation')}  |  Campus: {s.get('campus', '—')}", 0, 1, "L")
        pdf.cell(0, 6, f"Father Name: {s.get('father_name', '—')}  |  Class Teacher: {s.get('class_teacher_of', '—')}", 0, 1, "L")
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin1')

def generate_student_pdf(data_rows):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Excellence Model School - Student Directory", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Total Students: {len(data_rows)}", 0, 1, "C")
    pdf.ln(5)

    for s in data_rows:
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(240, 230, 250)
        pdf.cell(0, 8, f"Roll No: {s.get('id')} | Name: {s.get('name')}", 0, 1, "L", True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Father Name: {s.get('father_name')}  |  Class: {s.get('class_name')}", 0, 1, "L")
        
        m_fee = int(s.get('monthly_fee') or 3500)
        y_fee = int(s.get('yearly_fee') or 5000)
        pdf.cell(0, 6, f"Monthly Fee: Rs. {m_fee:,}  |  Yearly Fee: Rs. {y_fee:,}", 0, 1, "L")
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin1')

def generate_comprehensive_fee_pdf(class_title, target_month, students_list):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 8, "Excellence Model School - Comprehensive Fee Ledger Report", 0, 1, "C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, f"Selection: {class_title}   |   Billing Month: {target_month}", 0, 1, "C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(230, 230, 250)
    
    # Column widths totaling 277mm (A4 landscape usable width)
    pdf.cell(20, 8, "Roll No", 1, 0, "C", True)
    pdf.cell(30, 8, "Class", 1, 0, "C", True)
    pdf.cell(42, 8, "Student Name", 1, 0, "C", True)
    pdf.cell(42, 8, "Father Name", 1, 0, "C", True)
    pdf.cell(24, 8, "Monthly Fee", 1, 0, "C", True)
    pdf.cell(24, 8, "Yearly Fee", 1, 0, "C", True)
    pdf.cell(25, 8, "Status", 1, 0, "C", True)
    pdf.cell(70, 8, "Remarks", 1, 0, "C", True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    total_monthly = 0
    total_yearly = 0

    for s in students_list:
        m_stat, y_stat = get_fee_statuses(s["id"], target_month)
        status_str = f"M:{m_stat[:1]} | Y:{y_stat[:1]}"
        remarks_str = f"Monthly: {m_stat}, Yearly: {y_stat}"

        m_fee = int(s.get('monthly_fee') or 3500)
        y_fee = int(s.get('yearly_fee') or 5000)

        total_monthly += m_fee
        total_yearly += y_fee

        pdf.cell(20, 7, s.get("id", ""), 1, 0, "C")
        pdf.cell(30, 7, s.get("class_name", ""), 1, 0, "C")
        pdf.cell(42, 7, s.get("name", ""), 1, 0, "L")
        pdf.cell(42, 7, s.get("father_name", ""), 1, 0, "L")
        
        # Monthly Fee Column (Red background + White text if Pending)
        if m_stat == "Pending":
            pdf.set_fill_color(220, 53, 69)  # Red background
            pdf.set_text_color(255, 255, 255) # White text
            fill_m = True
        else:
            fill_m = False
        pdf.cell(24, 7, f"Rs. {m_fee:,}", 1, 0, "R", fill=fill_m)
        
        # Reset colors for Yearly Fee column if needed
        pdf.set_text_color(0, 0, 0)
        
        # Yearly Fee Column (Red background + White text if Pending)
        if y_stat == "Pending":
            pdf.set_fill_color(220, 53, 69)  # Red background
            pdf.set_text_color(255, 255, 255) # White text
            fill_y = True
        else:
            fill_y = False
        pdf.cell(24, 7, f"Rs. {y_fee:,}", 1, 0, "R", fill=fill_y)
        
        # Reset text color and fill for Status, Remarks and next rows
        pdf.set_text_color(0, 0, 0)
        pdf.cell(25, 7, status_str, 1, 0, "C")
        pdf.cell(70, 7, remarks_str, 1, 0, "L")
        pdf.ln()

    # Total Summary Row at the bottom
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(134, 8, f"Total Students: {len(students_list)}", 1, 0, "L", True)
    pdf.cell(24, 8, f"Rs. {total_monthly:,}", 1, 0, "R", True)
    pdf.cell(24, 8, f"Rs. {total_yearly:,}", 1, 0, "R", True)
    pdf.cell(95, 8, "---", 1, 0, "C", True)
    pdf.ln()

    return pdf.output(dest='S').encode('latin1')

def generate_monthly_attendance_pdf(class_name, month_year_str, students_list):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, f"Excellence Model School - Monthly Attendance Sheet", 0, 1, "C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, f"Class: {class_name}   |   Month: {month_year_str}", 0, 1, "C")
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
        pdf.cell(22, 6, s.get("id", ""), 1, 0, "C")
        pdf.cell(48, 6, s.get("name", ""), 1, 0, "L")
        for d in range(1, 32):
            pdf.cell(6.5, 6, "", 1, 0, "C")
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

# ------------------------------------------------------------------
# Data Fetches
# ------------------------------------------------------------------
staff = fetch_staff()
students = fetch_students()
designations = fetch_designations()
campuses = fetch_campuses()
custom_fields = fetch_custom_fields()

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
    st.markdown("""
    <div class="dashboard-header">
        <h1>Dashboard & Quick Statistics</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Real-time summary of school operations and cloud metrics</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Enrolled Students", len(students))
    c2.metric("Total Staff Members", len(staff))
    c3.metric("Active Campuses", len(campuses))
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
        st.subheader("🎓 Students per Class Distribution")
        if students:
            df_std = pd.DataFrame(students)
            if "class_name" in df_std.columns:
                st.bar_chart(df_std["class_name"].fillna("Unassigned").value_counts())

# ==================================================================
# 2. STAFF MANAGEMENT
# ==================================================================
elif menu_choice == "👥 Staff Management":
    st.markdown("""
    <div class="dashboard-header">
        <h1>Staff Management & Directory</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Manage faculty, designations, campuses and employee records</p>
    </div>
    """, unsafe_allow_html=True)

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
                    st.success(f"{name} added successfully.")
                    st.rerun()

    f_col1, f_col2 = st.columns([4, 2])
    with f_col1:
        search_staff = st.text_input("🔍 Search Staff", placeholder="Filter by name, designation or campus...")
    with f_col2:
        st.write("")
        st.write("")
        if staff:
            st.download_button("📄 Download Staff PDF", generate_staff_pdf(staff, custom_fields), "staff_report.pdf", "application/pdf", use_container_width=True)

    filtered_staff = staff
    if search_staff.strip():
        q = search_staff.strip().lower()
        filtered_staff = [s for s in staff if any(q in (v or "").lower() for v in [s.get("name"), s.get("designation"), s.get("campus")])]

    st.subheader(f"📋 Staff Directory Records ({len(filtered_staff)})")
    for s in filtered_staff:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5, 1])
            c1.markdown(f"**{s['name']}** \n`{s.get('id')}`")
            c2.markdown(f"<span class='ems-badge'>{s.get('designation','')}</span> | Father: {s.get('father_name','—')} | Campus: {s.get('campus','—')}", unsafe_allow_html=True)
            if c3.button("Delete", key=f"del_staff_{s['id']}"):
                sb.table("staff").delete().eq("id", s["id"]).execute()
                st.rerun()

# ==================================================================
# 3. STUDENT ADMISSIONS
# ==================================================================
elif menu_choice == "🎓 Student Admissions":
    st.markdown("""
    <div class="dashboard-header">
        <h1>Student Admissions & Class Records</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Register students with monthly/yearly fee setup and view class directories</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("student_admission_form", clear_on_submit=True):
        st.subheader("New Student Registration Form")
        sc1, sc2 = st.columns(2)
        
        with sc1:
            std_name = st.text_input("Student Full Name *")
            std_father = st.text_input("Father's Name *")
            std_class = st.selectbox("Assign Class", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"])
            
        with sc2:
            std_fee = st.number_input("Monthly Fee Amount (Rs.)", min_value=0, value=3500, step=500)
            std_yearly_fee = st.number_input("Yearly Fee / Salana Fee (Rs.)", min_value=0, value=5000, step=500)
            
        if st.form_submit_button("Register Student", type="primary"):
            if std_name.strip() and std_father.strip():
                try:
                    new_s_id = next_student_id(students)
                    student_data = {
                        "id": new_s_id,
                        "name": std_name.strip(),
                        "father_name": std_father.strip(),
                        "class_name": std_class,
                        "monthly_fee": std_fee,
                        "yearly_fee": std_yearly_fee
                    }
                    add_student(student_data)
                    st.success(f"Student {std_name} ({new_s_id}) successfully enrolled in {std_class}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving student: {e}")
            else:
                st.warning("Please fill in Student Name and Father's Name.")

    st.divider()
    
    c_filt1, c_filt2 = st.columns([4, 2])
    with c_filt1:
        view_class = st.selectbox("Select Class to View Directory", ["All Classes", "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="dir_class")
    
    if view_class == "All Classes":
        class_students = students
    else:
        class_students = [s for s in students if s.get("class_name") == view_class]

    with c_filt2:
        st.write("")
        st.write("")
        if class_students:
            st.download_button(
                "📄 Download Class PDF", 
                generate_student_pdf(class_students), 
                f"students_{view_class.replace(' ', '_')}.pdf", 
                "application/pdf", 
                use_container_width=True
            )

    st.subheader(f"📋 Enrolled Students in {view_class} ({len(class_students)})")
    
    if not class_students:
        st.info(f"No students found in {view_class}.")
    else:
        for st_item in class_students:
            with st.container(border=True):
                col_i, col_d, col_btn = st.columns([4, 4, 2])
                col_i.markdown(f"**{st_item['name']}** (`{st_item['id']}`) — *{st_item.get('class_name', '—')}*")
                col_i.caption(f"Father: {st_item['father_name']}")
                
                m_f = int(st_item.get('monthly_fee') or 3500)
                y_f = int(st_item.get('yearly_fee') or 5000)
                col_d.markdown(f"Monthly: **Rs. {m_f:,}** | Yearly: **Rs. {y_f:,}**")
                
                with st.expander("✏️ Update Fees"):
                    with st.form(key=f"edit_fee_form_{st_item['id']}"):
                        new_m = st.number_input("Monthly Fee", value=m_f, key=f"nm_{st_item['id']}")
                        new_y = st.number_input("Yearly Fee", value=y_f, key=f"ny_{st_item['id']}")
                        if st.form_submit_button("Update Fee"):
                            update_student_fee(st_item['id'], new_m, new_y)
                            st.success("Fee updated successfully!")
                            st.rerun()

                if col_btn.button("🗑️ Delete", key=f"del_std_{st_item['id']}"):
                    delete_student(st_item['id'])
                    st.success("Student removed.")
                    st.rerun()

# ==================================================================
# 4. FEE MANAGEMENT
# ==================================================================
elif menu_choice == "💳 Fee Management":
    st.markdown("""
    <div class="dashboard-header">
        <h1>Monthly Fee Tracker & Ledger</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Manage independent Monthly and Yearly payment statuses and ledgers</p>
    </div>
    """, unsafe_allow_html=True)
    
    current_month_str = datetime.now().strftime("%B %Y")
    
    fc1, fc2, fc3 = st.columns([2, 2, 3])
    with fc1:
        fee_class_sel = st.selectbox("Select Class", ["All Classes", "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="fee_cls_sel")
    with fc2:
        fee_month_input = st.text_input("Billing Month & Year", value=current_month_str)
    with fc3:
        st.write("")
        st.write("")
        if fee_class_sel == "All Classes":
            fee_target_students_pdf = students
        else:
            fee_target_students_pdf = [s for s in students if s.get("class_name") == fee_class_sel]
            
        if fee_target_students_pdf:
            comprehensive_pdf_bytes = generate_comprehensive_fee_pdf(fee_class_sel, fee_month_input, fee_target_students_pdf)
            st.download_button(
                "📄 Download Fee Ledger PDF", 
                comprehensive_pdf_bytes, 
                f"Fee_Ledger_{fee_class_sel.replace(' ', '_')}_{fee_month_input}.pdf", 
                "application/pdf", 
                use_container_width=True
            )
        
    fee_search_query = st.text_input("🔍 Search Student (by ID or Name)", placeholder="Type student name or ID (e.g. STD-001, Shehzad)...")

    st.divider()
    
    if fee_class_sel == "All Classes":
        fee_target_students = students
    else:
        fee_target_students = [s for s in students if s.get("class_name") == fee_class_sel]
    
    if fee_search_query.strip():
        q_fee = fee_search_query.strip().lower()
        fee_target_students = [s for s in fee_target_students if q_fee in s.get("id", "").lower() or q_fee in s.get("name", "").lower()]

    processed_fee_list = []
    for s_obj in fee_target_students:
        m_stat, y_stat = get_fee_statuses(s_obj["id"], fee_month_input)
        processed_fee_list.append({
            "id": s_obj["id"],
            "name": s_obj["name"],
            "class_name": s_obj.get("class_name", "—"),
            "monthly_fee": int(s_obj.get("monthly_fee") or 3500),
            "yearly_fee": int(s_obj.get("yearly_fee") or 5000),
            "monthly_status": m_stat,
            "yearly_status": y_stat
        })
    
    tot_s = len(processed_fee_list)
    paid_monthly = sum(1 for s in processed_fee_list if s['monthly_status'] == 'Paid')
    pend_monthly = sum(1 for s in processed_fee_list if s['monthly_status'] == 'Pending')
    pend_amt = sum(s['monthly_fee'] for s in processed_fee_list if s['monthly_status'] == 'Pending')
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", tot_s)
    m2.metric("Monthly Paid", paid_monthly)
    m3.metric("Monthly Pending", pend_monthly)
    m4.metric("Pending Monthly Dues", f"Rs. {pend_amt:,}")
    
    st.subheader(f"📋 Fee Status Ledger — {fee_class_sel} ({fee_month_input})")
    
    if not processed_fee_list:
        st.info("No students found matching your search.")
    else:
        for s_item in processed_fee_list:
            with st.container(border=True):
                col_info, col_m, col_y = st.columns([3, 3, 3])
                
                with col_info:
                    st.markdown(f"**{s_item['name']}** (`{s_item['id']}`) — *{s_item['class_name']}*")
                    st.caption(f"Monthly: Rs. {s_item['monthly_fee']:,} | Yearly: Rs. {s_item['yearly_fee']:,}")
                    
                with col_m:
                    st.write("📅 **Monthly Fee**")
                    if s_item["monthly_status"] == "Paid":
                        st.markdown("🟢 **Paid**")
                        if st.button("↩️ Undo Monthly", key=f"undo_m_{s_item['id']}"):
                            set_fee_status(s_item["id"], fee_month_input, "Pending", s_item["yearly_status"])
                            st.warning(f"Monthly status set to Pending for {s_item['name']}.")
                            st.rerun()
                    else:
                        st.markdown("🔴 **Pending**")
                        if st.button("✅ Pay Monthly", key=f"pay_m_{s_item['id']}", type="primary"):
                            set_fee_status(s_item["id"], fee_month_input, "Paid", s_item["yearly_status"], s_item["monthly_fee"])
                            st.success(f"Monthly fee collected for {s_item['name']}!")
                            st.rerun()
                            
                with col_y:
                    st.write("⭐ **Yearly Fee**")
                    if s_item["yearly_status"] == "Paid":
                        st.markdown("🟢 **Paid**")
                        if st.button("↩️ Undo Yearly", key=f"undo_y_{s_item['id']}"):
                            set_fee_status(s_item["id"], fee_month_input, s_item["monthly_status"], "Pending")
                            st.warning(f"Yearly status set to Pending for {s_item['name']}.")
                            st.rerun()
                    else:
                        st.markdown("🔴 **Not Paid**")
                        if st.button("✅ Pay Yearly", key=f"pay_y_{s_item['id']}", type="primary"):
                            set_fee_status(s_item["id"], fee_month_input, s_item["monthly_status"], "Paid", s_item["yearly_fee"])
                            st.success(f"Yearly fee collected for {s_item['name']}!")
                            st.rerun()

# ==================================================================
# 5. ATTENDANCE SHEETS
# ==================================================================
elif menu_choice == "📅 Attendance Sheets":
    st.markdown("""
    <div class="dashboard-header">
        <h1>Monthly Attendance Sheets</h1>
        <p style="margin:4px 0 0 0; color:#D4C5F9; font-size:13px;">Generate landscape printable attendance sheets with day grids (1 to 31)</p>
    </div>
    """, unsafe_allow_html=True)

    at_c1, at_c2 = st.columns(2)
    with at_c1:
        att_class_sel = st.selectbox("Select Class", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="att_cls_sheet")
    with at_c2:
        att_month_sel = st.selectbox("Select Month & Year", ["August 2026", "September 2026", "October 2026", "November 2026", "December 2026", "January 2027", "February 2027", "March 2027", "April 2027", "May 2027", "June 2027", "July 2027"], key="att_mnth_sheet")

    st.divider()

    class_att_students = [s for s in students if s.get("class_name") == att_class_sel]

    col_info, col_btn = st.columns([4, 3])
    with col_info:
        st.subheader(f"📋 {att_class_sel} Roster ({len(class_att_students)} Students)")
        st.write(f"Generate blank printable attendance grid for **{att_month_sel}**.")
    
    with col_btn:
        st.write("")
        st.write("")
        if class_att_students:
            pdf_bytes = generate_monthly_attendance_pdf(att_class_sel, att_month_sel, class_att_students)
            st.download_button(
                "📄 Download Attendance PDF", 
                pdf_bytes, 
                f"Attendance_{att_class_sel}_{att_month_sel}.pdf", 
                "application/pdf", 
                use_container_width=True
            )
        else:
            st.warning("No students found in this class.")

    st.divider()
    if class_att_students:
        for st_item in class_att_students:
            with st.container(border=True):
                st.markdown(f"**{st_item['name']}** (`{st_item['id']}`) — Father: {st_item['father_name']}")
