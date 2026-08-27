import streamlit as st
from supabase import create_client, Client
import re
from fpdf import FPDF
import os
import base64
import pandas as pd
from datetime import datetime
import calendar

# ------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Excellence Model School — Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
PURPLE = "#4B1E82"
PURPLE_DEEP = "#17091F"
PURPLE_LIGHT = "#7A2FC2"
CREAM = "#F5F4F7"

st.markdown(f"""
<style>
    .stApp {{ background-color: {CREAM}; }}
    .block-container {{ padding-top: 2rem !important; }}
    
    .ems-header {{
        background: linear-gradient(115deg, {PURPLE} 0%, {PURPLE_DEEP} 100%);
        padding: 30px 35px; border-radius: 12px; margin-bottom: 20px; color: white;
        box-shadow: 0 6px 20px rgba(75, 30, 130, 0.2);
    }}
    .ems-header .eyebrow {{ font-size: 13px; letter-spacing: 2px; text-transform: uppercase;
        color: #E7D6F7; margin: 0 0 6px 0; font-weight: 700; }}
    .ems-header h1 {{ margin: 0; font-size: 34px !important; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px; }}
    
    .ems-badge {{
        display: inline-block; background: {PURPLE_DEEP}; color: #E7D6F7;
        border: 1px solid {PURPLE_LIGHT}; border-radius: 20px; padding: 2px 10px;
        font-size: 12px; font-weight: 700;
    }}
    div[data-testid="stForm"] {{ border: 1px solid #DED4EC; border-radius: 10px; padding: 18px; background: white; }}
    .stButton>button {{ border-radius: 7px; font-weight: 600; }}
    .stButton>button[kind="primary"] {{ background-color: {PURPLE}; border-color: {PURPLE}; }}

    div[data-testid="stTextInput"] label p {{
        color: #2C1E4A !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }}

    div[data-testid="stTextInput"] div[data-baseweb="input"] {{
        border: 2px solid {PURPLE_LIGHT} !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 5px rgba(75, 30, 130, 0.1);
    }}
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
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="120" style="margin-bottom: 10px;" />' if logo_base64 else '<div style="font-size: 45px; margin-bottom: 10px;">🎓</div>'
            
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #4B1E82, #17091F); padding: 35px; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.2); text-align: center; color: white; margin-top: 30px;">
                    {logo_html}
                    <h1 style="margin: 15px 0 5px 0; font-size: 24px; font-weight: 800; color: #ffffff !important; letter-spacing: 1px;">EXCELLENCE MODEL SCHOOL</h1>
                    <p style="margin: 0; font-size: 13px; font-weight: 400; color: #E7D6F7 !important; letter-spacing: 0.5px;">School Management System — Secure Login</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            st.text_input("🔐 Enter Password to Access:", type="password", on_change=password_entered, key="password")
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

def delete_student(std_id):
    sb.table("students").delete().eq("id", std_id).execute()

def fetch_fee_record(student_id, month_year):
    res = sb.table("fee_records").select("*").eq("student_id", student_id).eq("month_year", month_year).execute()
    return res.data[0] if res.data else None

def mark_fee_paid(student_id, month_year, amount):
    existing = fetch_fee_record(student_id, month_year)
    today = datetime.now().strftime("%Y-%m-%d")
    if existing:
        sb.table("fee_records").update({"status": "Paid", "paid_date": today}).eq("id", existing["id"]).execute()
    else:
        sb.table("fee_records").insert({
            "student_id": student_id,
            "month_year": month_year,
            "status": "Paid",
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
        pdf.cell(0, 6, f"Monthly Fee: Rs. {s.get('monthly_fee', 0):,}", 0, 1, "L")
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin1')

def generate_monthly_attendance_pdf(class_name, month_year_str, students_list):
    # Landscape orientation for wide attendance grid
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    
    # Title
    pdf.cell(0, 8, f"Excellence Model School - Monthly Attendance Sheet", 0, 1, "C")
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, f"Class: {class_name}   |   Month: {month_year_str}", 0, 1, "C")
    pdf.ln(4)

    # Table Header setup
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 250)
    
    # Widths: Roll No (22), Student Name (45), Days 1-31 (approx 6.2 each for total 275mm width landscape)
    pdf.cell(22, 7, "Roll No", 1, 0, "C", True)
    pdf.cell(48, 7, "Student Name", 1, 0, "C", True)
    
    # Days 1 to 31 headers
    for d in range(1, 32):
        pdf.cell(6.5, 7, str(d), 1, 0, "C", True)
    pdf.ln()

    # Students Rows
    pdf.set_font("Arial", "", 8)
    for s in students_list:
        pdf.cell(22, 6, s.get("id", ""), 1, 0, "C")
        pdf.cell(48, 6, s.get("name", ""), 1, 0, "L")
        
        # Empty cells for manual pen marking
        for d in range(1, 32):
            pdf.cell(6.5, 6, "", 1, 0, "C")
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

# ------------------------------------------------------------------
# Data Fetches & Header
# ------------------------------------------------------------------
staff = fetch_staff()
students = fetch_students()
designations = fetch_designations()
campuses = fetch_campuses()
custom_fields = fetch_custom_fields()

col_logo, col_head, col_refresh = st.columns([1, 6, 1])

with col_logo:
    logo_path = get_logo_path()
    if logo_path:
        st.image(logo_path, width=95)
    else:
        st.markdown("<div style='font-size: 50px; text-align: center;'>🎓</div>", unsafe_allow_html=True)

with col_head:
    st.markdown(f"""
    <div class="ems-header">
        <p class="eyebrow">Excellence Model School</p>
        <h1>School Management ERP</h1>
        <p style="margin:6px 0 0 0; color:#E7D6F7; font-size:14px; font-weight: 500;">Live multi-tab portal connected with Supabase</p>
    </div>
    """, unsafe_allow_html=True)

with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh App", use_container_width=True):
        st.rerun()

# ------------------------------------------------------------------
# TABS SETUP
# ------------------------------------------------------------------
tab_staff, tab_students, tab_fee, tab_attendance = st.tabs([
    "👥 Staff Management", 
    "🎓 Student Admissions", 
    "💳 Fee Management",
    "📅 Attendance"
])

# ==================================================================
# TAB 1: STAFF MANAGEMENT
# ==================================================================
with tab_staff:
    with st.sidebar:
        st.subheader("Filter Staff")
        campus_filter = st.selectbox("Campus", ["All Campuses"] + campuses)
        search = st.text_input("Search Staff", placeholder="Name, designation, campus…")
        st.divider()
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()

    if staff:
        with st.expander("📊 Staff Analytics & Visual Charts", expanded=False):
            df_staff = pd.DataFrame(staff)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("##### 🏫 Staff Count by Campus")
                if "campus" in df_staff.columns:
                    st.bar_chart(df_staff["campus"].fillna("Not Specified").value_counts())
            with col_c2:
                st.markdown("##### 👩‍🏫 Staff Count by Designation")
                if "designation" in df_staff.columns:
                    st.bar_chart(df_staff["designation"].fillna("Not Specified").value_counts())

    with st.expander("➕ Add New Staff", expanded=False):
        with st.form("add_staff_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Staff Name *")
            father_name = c2.text_input("Father Name")
            designation = c1.selectbox("Category / Designation *", [""] + designations)
            campus = c2.selectbox("Campus", [""] + campuses)
            class_teacher_of = c1.text_input("Class Teacher Of (if applicable)")
            subject_teacher = c2.text_input("Subject Teacher (if applicable)")

            submitted = st.form_submit_button("Save Record", type="primary")
            if submitted:
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

    rows = staff
    if campus_filter != "All Campuses":
        rows = [s for s in rows if s.get("campus"] == campus_filter]
    if search.strip():
        q = search.strip().lower()
        rows = [s for s in rows if any(q in (v or "").lower() for v in [s.get("name"), s.get("designation"), s.get("campus")])]

    col_title, col_pdf = st.columns([4, 2])
    with col_title:
        st.subheader(f"Staff Records ({len(rows)})")
    with col_pdf:
        if rows:
            st.download_button("📄 Download PDF Report", generate_staff_pdf(rows, custom_fields), "staff_report.pdf", "application/pdf", use_container_width=True)

    for s in rows:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5, 1])
            c1.markdown(f"**{s['name']}** \n`{s.get('id')}`")
            c2.markdown(f"<span class='ems-badge'>{s.get('designation','')}</span> | Father: {s.get('father_name','—')} | Campus: {s.get('campus','—')}", unsafe_allow_html=True)
            if c3.button("Delete", key=f"del_staff_{s['id']}"):
                sb.table("staff").delete().eq("id", s["id"]).execute()
                st.rerun()


# ==================================================================
# TAB 2: STUDENT ADMISSIONS & RECORDS
# ==================================================================
with tab_students:
    st.header("🎓 Student Admissions & Class Records")
    st.markdown("Register students here. Data syncs instantly with Supabase database and Class lists.")
    
    with st.form("student_admission_form", clear_on_submit=True):
        st.subheader("New Student Registration")
        sc1, sc2 = st.columns(2)
        
        with sc1:
            std_name = st.text_input("Student Full Name *")
            std_father = st.text_input("Father's Name *")
            
        with sc2:
            std_class = st.selectbox("Assign Class", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"])
            std_fee = st.number_input("Monthly Fee Amount (Rs.)", min_value=0, value=3500, step=500)
            
        submit_std = st.form_submit_button("Register Student", type="primary")
        
        if submit_std:
            if std_name.strip() and std_father.strip():
                try:
                    new_s_id = next_student_id(students)
                    student_data = {
                        "id": new_s_id,
                        "name": std_name.strip(),
                        "father_name": std_father.strip(),
                        "class_name": std_class,
                        "monthly_fee": std_fee
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
        view_class = st.selectbox("Select Class to View Directory", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="dir_class")
    
    class_students = [s for s in students if s.get("class_name") == view_class]

    with c_filt2:
        st.write("")
        st.write("")
        if class_students:
            st.download_button(
                "📄 Download Class PDF", 
                generate_student_pdf(class_students), 
                f"students_{view_class}.pdf", 
                "application/pdf", 
                use_container_width=True
            )

    st.subheader(f"📋 Enrolled Students in {view_class} ({len(class_students)})")
    
    if not class_students:
        st.info(f"No students found in {view_class}. Use the form above to add students.")
    else:
        for st_item in class_students:
            with st.container(border=True):
                col_i, col_d, col_btn = st.columns([4, 4, 2])
                col_i.markdown(f"**{st_item['name']}** (`{st_item['id']}`)")
                col_i.caption(f"Father: {st_item['father_name']}")
                
                col_d.markdown(f"Monthly Fee: **Rs. {st_item.get('monthly_fee', 0):,}**")
                
                if col_btn.button("🗑️ Delete", key=f"del_std_{st_item['id']}"):
                    delete_student(st_item['id'])
                    st.success("Student removed.")
                    st.rerun()


# ==================================================================
# TAB 3: FEE MANAGEMENT & MONTHLY TRACKER
# ==================================================================
with tab_fee:
    st.header("💳 Monthly Fee Tracker & Dues Clearance")
    st.markdown("Track monthly fee status. Clicking 'Collect Fee' updates Supabase instantly.")
    
    current_month_str = datetime.now().strftime("%B %Y")
    
    fc1, fc2 = st.columns(2)
    with fc1:
        fee_class_sel = st.selectbox("Select Class for Fee Status", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="fee_cls_sel")
    with fc2:
        fee_month_input = st.text_input("Billing Month & Year", value=current_month_str)
        
    st.divider()
    
    fee_target_students = [s for s in students if s.get("class_name") == fee_class_sel]
    
    processed_fee_list = []
    for s_obj in fee_target_students:
        rec = fetch_fee_record(s_obj["id"], fee_month_input)
        status = rec["status"] if rec else "Pending"
        processed_fee_list.append({
            "id": s_obj["id"],
            "name": s_obj["name"],
            "monthly_fee": s_obj.get("monthly_fee", 0),
            "status": status
        })
    
    tot_s = len(processed_fee_list)
    paid_s = sum(1 for s in processed_fee_list if s['status'] == 'Paid')
    pend_s = sum(1 for s in processed_fee_list if s['status'] == 'Pending')
    pend_amt = sum(s['monthly_fee'] for s in processed_fee_list if s['status'] == 'Pending')
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", tot_s)
    m2.metric("Paid Clear", paid_s)
    m3.metric("Pending Dues", pend_s)
    m4.metric("Pending Amount", f"Rs. {pend_amt:,}")
    
    st.subheader(f"📋 Fee Status Ledger — {fee_class_sel} ({fee_month_input})")
    
    if not processed_fee_list:
        st.info(f"No students enrolled in {fee_class_sel} yet to generate fee ledger.")
    else:
        for s_item in processed_fee_list:
            with st.container(border=True):
                col_info, col_status, col_action = st.columns([4, 2, 2])
                
                with col_info:
                    st.markdown(f"**{s_item['name']}** (`{s_item['id']}`)")
                    st.caption(f"Monthly Fee Due: Rs. {s_item['monthly_fee']:,}")
                    
                with col_status:
                    if s_item["status"] == "Paid":
                        st.markdown("🟢 **<span style='color:green;'>PAID / CLEAR</span>**", unsafe_allow_html=True)
                    else:
                        st.markdown("🔴 **<span style='color:red;'>PENDING</span>**", unsafe_allow_html=True)
                        
                with col_action:
                    if s_item["status"] == "Pending":
                        if st.button("✅ Collect Fee", key=f"pay_btn_{s_item['id']}", type="primary"):
                            mark_fee_paid(s_item["id"], fee_month_input, s_item["monthly_fee"])
                            st.success(f"Fee collected successfully for {s_item['name']}!")
                            st.rerun()
                    else:
                        if st.button("↩️ Undo / Make Pending", key=f"undo_btn_{s_item['id']}"):
                            rec = fetch_fee_record(s_item["id"], fee_month_input)
                            if rec:
                                sb.table("fee_records").update({"status": "Pending"}).eq("id", rec["id"]).execute()
                                st.warning(f"Status changed back to Pending for {s_item['name']}.")
                                st.rerun()


# ==================================================================
# TAB 4: MONTHLY ATTENDANCE PRINTABLE SHEET
# ==================================================================
with tab_attendance:
    st.header("📅 Monthly Printable Attendance Sheets")
    st.markdown("Generate and print blank monthly attendance sheets for teachers to fill manually.")

    at_c1, at_c2 = st.columns(2)
    with at_c1:
        att_class_sel = st.selectbox("Select Class for Attendance Sheet", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="att_cls_sheet")
    with at_c2:
        att_month_sel = st.selectbox("Select Month & Year", ["August 2026", "September 2026", "October 2026", "November 2026", "December 2026", "January 2027", "February 2027", "March 2027", "April 2027", "May 2027", "June 2027", "July 2027"], key="att_mnth_sheet")

    st.divider()

    class_att_students = [s for s in students if s.get("class_name") == att_class_sel]

    col_info, col_btn = st.columns([4, 3])
    with col_info:
        st.subheader(f"📋 {att_class_sel} Student List ({len(class_att_students)} Students)")
        st.write(f"Clicking the button will generate a landscape PDF containing all students with dates 1 to 31 for **{att_month_sel}**.")
    
    with col_btn:
        st.write("")
        st.write("")
        if class_att_students:
            pdf_bytes = generate_monthly_attendance_pdf(att_class_sel, att_month_sel, class_att_students)
            st.download_button(
                "📄 Download Monthly Attendance PDF", 
                pdf_bytes, 
                f"Attendance_{att_class_sel}_{att_month_sel}.pdf", 
                "application/pdf", 
                use_container_width=True
            )
        else:
            st.warning("No students found in this class to generate sheet.")

    st.divider()
    
    if class_att_students:
        for st_item in class_att_students:
            with st.container(border=True):
                st.markdown(f"**{st_item['name']}** (`{st_item['id']}`) — Father: {st_item['father_name']}")
    else:
        st.info(f"No students enrolled in {att_class_sel} yet.")
