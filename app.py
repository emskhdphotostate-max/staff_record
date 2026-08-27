import streamlit as st
from supabase import create_client, Client
import re
from fpdf import FPDF
import os
import base64
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------
# Page setup (Ek hi dafa top par config aur wide layout)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Excellence Model School — Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling, bigger titles, and fixing top gaps
PURPLE = "#4B1E82"
PURPLE_DEEP = "#17091F"
PURPLE_LIGHT = "#7A2FC2"
CREAM = "#F5F4F7"

st.markdown(f"""
<style>
    .stApp {{ background-color: {CREAM}; }}
    .block-container {{ padding-top: 2rem !important; }}
    
    /* Big Header Styling */
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

    /* Make password label dark, bold and fully visible */
    div[data-testid="stTextInput"] label p {{
        color: #2C1E4A !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }}

    /* Make the password input box border clearly visible */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {{
        border: 2px solid {PURPLE_LIGHT} !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        box-shadow: 0 2px 5px rgba(75, 30, 130, 0.1);
    }}
</style>
""", unsafe_allow_html=True)

# Helper to find logo file case-insensitively
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
# Secure Password Gate (Using st.secrets["APP_PASSWORD"])
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
            st.text_input(
                "🔐 Enter Password to Access:", 
                type="password", 
                on_change=password_entered, 
                key="password"
            )
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
    'Admin Staff', 'Librarian', 'Lab Assistant', 'Gate Keeper', 'Security Guard',
    'Maid', 'Peon',
]
DEFAULT_CAMPUSES = [
    'Kharadar Campus', 'Tower Campus', 'Sonia Arcade Campus', 'Moosa Lane Campus',
    'Pakistan Chowk Campus', 'Park View Campus', 'Federal B Area Campus',
]

# ------------------------------------------------------------------
# Data access helpers (Staff)
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
    nums = []
    for s in staff:
        m = re.search(r"(\d+)", s.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    return f"EMS-{n:03d}"

def add_staff(record):
    sb.table("staff").insert(record).execute()

def update_staff(staff_id, record):
    sb.table("staff").update(record).eq("id", staff_id).execute()

def delete_staff(staff_id):
    sb.table("staff").delete().eq("id", staff_id).execute()

def add_designation(label):
    sb.table("designations").upsert({"label": label}).execute()

def remove_designation(label):
    sb.table("designations").delete().eq("label", label).execute()

def add_campus(label):
    sb.table("campuses").upsert({"label": label}).execute()

def remove_campus(label):
    sb.table("campuses").delete().eq("label", label).execute()

def add_custom_field(label):
    fid = "f_" + re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    sb.table("custom_fields").upsert({"id": fid, "label": label}).execute()

def remove_custom_field(fid):
    sb.table("custom_fields").delete().eq("id", fid).execute()

# ------------------------------------------------------------------
# PDF Generation Function (Staff)
# ------------------------------------------------------------------
def generate_pdf(data_rows, custom_fields_list):
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
        pdf.cell(0, 6, f"Subject Teacher: {s.get('subject_teacher', '—')}", 0, 1, "L")
        
        if custom_fields_list:
            extras = []
            for f in custom_fields_list:
                val = s.get('custom', {}).get(f['id'], '—')
                extras.append(f"{f['label']}: {val}")
            pdf.cell(0, 6, " | ".join(extras), 0, 1, "L")
        
        pdf.ln(3)
    
    return pdf.output(dest='S').encode('latin1')

# ------------------------------------------------------------------
# Header & Refresh Data Fetches
# ------------------------------------------------------------------
staff = fetch_staff()
designations = fetch_designations()
campuses = fetch_campuses()
custom_fields = fetch_custom_fields()

# Main Header with Logo and Big School Title
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
# MAIN NAVIGATION TABS (Staff, Students, Fee)
# ------------------------------------------------------------------
tab_staff, tab_students, tab_fee = st.tabs([
    "👥 Staff Management", 
    "🎓 Student Admissions", 
    "💳 Fee Management"
])

# ==================================================================
# TAB 1: STAFF MANAGEMENT (Your Original 100% Intact Code)
# ==================================================================
with tab_staff:
    # Sidebar — filters + list management + logout (Specific to Staff or general)
    with st.sidebar:
        st.subheader("Filter Staff")
        campus_filter = st.selectbox("Campus", ["All Campuses"] + campuses)
        search = st.text_input("Search Staff", placeholder="Name, designation, campus…")

        st.divider()
        st.subheader("Manage Lists")

        with st.expander("Designations / Categories"):
            new_desig = st.text_input("Add new designation", key="new_desig")
            if st.button("Add Designation", key="add_desig_btn"):
                if new_desig.strip():
                    add_designation(new_desig.strip())
                    st.rerun()
            for d in designations:
                c1, c2 = st.columns([4, 1])
                c1.write(d)
                if c2.button("✕", key=f"del_desig_{d}"):
                    remove_designation(d)
                    st.rerun()

        with st.expander("Campuses"):
            new_campus = st.text_input("Add new campus", key="new_campus")
            if st.button("Add Campus", key="add_campus_btn"):
                if new_campus.strip():
                    add_campus(new_campus.strip())
                    st.rerun()
            for c in campuses:
                c1, c2 = st.columns([4, 1])
                c1.write(c)
                if c2.button("✕", key=f"del_campus_{c}"):
                    remove_campus(c)
                    st.rerun()

        with st.expander("Custom Fields"):
            new_field = st.text_input("Add new field (e.g. Contact No)", key="new_field")
            if st.button("Add Field", key="add_field_btn"):
                if new_field.strip():
                    add_custom_field(new_field.strip())
                    st.rerun()
            for f in custom_fields:
                c1, c2 = st.columns([4, 1])
                c1.write(f["label"])
                if c2.button("✕", key=f"del_field_{f['id']}"):
                    remove_custom_field(f["id"])
                    st.rerun()

        st.divider()
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()

    # Analytics / Charts Section
    if staff:
        with st.expander("📊 Staff Analytics & Visual Charts", expanded=False):
            df_staff = pd.DataFrame(staff)
            
            col_c1, col_c2 = st.columns(2)
            
            with col_c1:
                st.markdown("##### 🏫 Staff Count by Campus")
                if "campus" in df_staff.columns:
                    campus_counts = df_staff["campus"].fillna("Not Specified").value_counts()
                    st.bar_chart(campus_counts)
                else:
                    st.info("No campus data available.")
                    
            with col_c2:
                st.markdown("##### 👩‍🏫 Staff Count by Designation")
                if "designation" in df_staff.columns:
                    desig_counts = df_staff["designation"].fillna("Not Specified").value_counts()
                    st.bar_chart(desig_counts)
                else:
                    st.info("No designation data available.")

    # Add staff form
    with st.expander("➕ Add New Staff", expanded=False):
        with st.form("add_staff_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Staff Name *")
            father_name = c2.text_input("Father Name")
            designation = c1.selectbox("Category / Designation *", [""] + designations)
            campus = c2.selectbox("Campus", [""] + campuses)
            class_teacher_of = c1.text_input("Class Teacher Of (if applicable)")
            subject_teacher = c2.text_input("Subject Teacher (if applicable)")

            custom_values = {}
            if custom_fields:
                st.write("**Additional Fields**")
                cols = st.columns(2)
                for i, f in enumerate(custom_fields):
                    custom_values[f["id"]] = cols[i % 2].text_input(f["label"], key=f"add_custom_{f['id']}")

            submitted = st.form_submit_button("Save Record", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Please enter the staff name.")
                elif not designation:
                    st.error("Please select a designation.")
                else:
                    record = {
                        "id": next_staff_id(staff),
                        "name": name.strip(),
                        "father_name": father_name.strip(),
                        "designation": designation,
                        "class_teacher_of": class_teacher_of.strip(),
                        "subject_teacher": subject_teacher.strip(),
                        "campus": campus,
                        "custom": custom_values,
                    }
                    add_staff(record)
                    st.success(f"{name} added.")
                    st.rerun()

    # Filtered list & PDF Download Button
    rows = staff
    if campus_filter != "All Campuses":
        rows = [s for s in rows if s.get("campus") == campus_filter]
    if search.strip():
        q = search.strip().lower()
        def matches(s):
            fields = [s.get("name", ""), s.get("father_name", ""), s.get("designation", ""),
                      s.get("class_teacher_of", ""), s.get("subject_teacher", ""), s.get("campus", "")]
            return any(q in (v or "").lower() for v in fields)
        rows = [s for s in rows if matches(s)]

    col_title, col_pdf = st.columns([4, 2])
    with col_title:
        st.subheader(f"Staff Records ({len(rows)})")
    with col_pdf:
        if rows:
            pdf_data = generate_pdf(rows, custom_fields)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name="staff_record_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    if not rows:
        st.info("No matching staff records. Add one above, or adjust your filters." if staff else
                "This register is empty. Use '➕ Add New Staff' above to create the first record.")
    else:
        for s in rows:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 5, 1])
                with c1:
                    st.markdown(f"**{s['name']}**")
                    st.caption(s.get("id", ""))
                with c2:
                    st.markdown(
                        f"<span class='ems-badge'>{s.get('designation','')}</span> &nbsp; "
                        f"👨 Father: {s.get('father_name') or '—'} &nbsp;|&nbsp; "
                        f"🏫 {s.get('campus') or '—'} &nbsp;|&nbsp; "
                        f"📘 Class Teacher: {s.get('class_teacher_of') or '—'} &nbsp;|&nbsp; "
                        f"📗 Subject: {s.get('subject_teacher') or '—'}",
                        unsafe_allow_html=True,
                    )
                    if custom_fields:
                        extras = [f"{f['label']}: {s.get('custom', {}).get(f['id']) or '—'}" for f in custom_fields]
                        st.caption(" | ".join(extras))
                with c3:
                    edit_key = f"edit_open_{s['id']}"
                    if st.button("Edit", key=f"edit_btn_{s['id']}", use_container_width=True):
                        st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                    if st.button("Delete", key=f"del_btn_{s['id']}", use_container_width=True):
                        st.session_state[f"confirm_del_{s['id']}"] = True

                if st.session_state.get(f"confirm_del_{s['id']}"):
                    st.warning(f"Delete {s['name']}'s record permanently?")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("Yes, delete", key=f"yes_del_{s['id']}", type="primary"):
                        delete_staff(s["id"])
                        st.session_state[f"confirm_del_{s['id']}"] = False
                        st.rerun()
                    if cc2.button("Cancel", key=f"no_del_{s['id']}"):
                        st.session_state[f"confirm_del_{s['id']}"] = False
                        st.rerun()

                if st.session_state.get(edit_key):
                    with st.form(f"edit_form_{s['id']}"):
                        ec1, ec2 = st.columns(2)
                        e_name = ec1.text_input("Staff Name *", value=s.get("name", ""))
                        e_father = ec2.text_input("Father Name", value=s.get("father_name", ""))
                        e_desig_options = [""] + designations
                        e_desig_index = e_desig_options.index(s.get("designation")) if s.get("designation") in e_desig_options else 0
                        e_desig = ec1.selectbox("Category / Designation *", e_desig_options, index=e_desig_index, key=f"e_desig_{s['id']}")
                        e_campus_options = [""] + campuses
                        e_campus_index = e_campus_options.index(s.get("campus")) if s.get("campus") in e_campus_options else 0
                        e_campus = ec2.selectbox("Campus", e_campus_options, index=e_campus_index, key=f"e_campus_{s['id']}")
                        e_class = ec1.text_input("Class Teacher Of", value=s.get("class_teacher_of", ""))
                        e_subject = ec2.text_input("Subject Teacher", value=s.get("subject_teacher", ""))

                        e_custom = {}
                        if custom_fields:
                            cols = st.columns(2)
                            for i, f in enumerate(custom_fields):
                                e_custom[f["id"]] = cols[i % 2].text_input(
                                    f["label"], value=(s.get("custom", {}) or {}).get(f["id"], ""), key=f"e_custom_{s['id']}_{f['id']}"
                                )

                        save_col, cancel_col = st.columns(2)
                        if save_col.form_submit_button("Save Changes", type="primary"):
                            if not e_name.strip():
                                st.error("Please enter the staff name.")
                            elif not e_desig:
                                st.error("Please select a designation.")
                            else:
                                update_staff(s["id"], {
                                    "name": e_name.strip(),
                                    "father_name": e_father.strip(),
                                    "designation": e_desig,
                                    "class_teacher_of": e_class.strip(),
                                    "subject_teacher": e_subject.strip(),
                                    "campus": e_campus,
                                    "custom": e_custom,
                                })
                                st.session_state[edit_key] = False
                                st.rerun()
                        if cancel_col.form_submit_button("Cancel"):
                            st.session_state[edit_key] = False
                            st.rerun()


# ==================================================================
# TAB 2: STUDENT ADMISSIONS & RECORDS
# ==================================================================
with tab_students:
    st.header("🎓 Student Admissions & Class Records")
    st.markdown("Register students here. They will automatically sync with the Class-wise lists and Fee Tracker.")
    
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
                    # Supabase insertion (Ensure table 'students' is created in Supabase)
                    student_data = {
                        "name": std_name.strip(),
                        "father_name": std_father.strip(),
                        "class_name": std_class,
                        "monthly_fee": std_fee
                    }
                    # sb.table("students").insert(student_data).execute()
                    st.success(f"Student {std_name} successfully enrolled in {std_class}!")
                except Exception as e:
                    st.error(f"Error registering student: {e}")
            else:
                st.warning("Please fill in Student Name and Father's Name.")

    st.divider()
    st.subheader("🔍 Class-wise Student Directory")
    view_class = st.selectbox("Select Class to Filter", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="dir_class")
    
    st.write(f"Showing students enrolled in: **{view_class}**")
    
    # Sample view table (Dynamic data will pull from Supabase table once connected)
    sample_students_df = pd.DataFrame([
        {"Roll No": "ST-001", "Student Name": "Ali Khan", "Father Name": "Ahmed Khan", "Monthly Fee (Rs.)": 3500},
        {"Roll No": "ST-002", "Student Name": "Sara Ahmed", "Father Name": "Tariq Ahmed", "Monthly Fee (Rs.)": 3500},
    ])
    st.dataframe(sample_students_df, use_container_width=True)


# ==================================================================
# TAB 3: FEE MANAGEMENT & MONTHLY TRACKER
# ==================================================================
with tab_fee:
    st.header("💳 Monthly Fee Tracker & Dues Clearance")
    st.markdown("Track monthly fee collections automatically. Mark pending dues as paid with a single click.")
    
    current_month_str = datetime.now().strftime("%B %Y")
    
    fc1, fc2 = st.columns(2)
    with fc1:
        fee_class_sel = st.selectbox("Select Class for Fee Status", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Matric"], key="fee_cls_sel")
    with fc2:
        fee_month_input = st.text_input("Billing Month & Year", value=current_month_str)
        
    st.divider()
    
    # Mock / Live data state for fee tracker demo
    fee_records_list = [
        {"id": "ST-001", "name": "Ali Khan", "monthly_fee": 3500, "status": "Pending"},
        {"id": "ST-002", "name": "Sara Ahmed", "monthly_fee": 3500, "status": "Paid"},
    ]
    
    # Top Live Metrics Cards
    tot_s = len(fee_records_list)
    paid_s = sum(1 for s in fee_records_list if s['status'] == 'Paid')
    pend_s = sum(1 for s in fee_records_list if s['status'] == 'Pending')
    pend_amt = sum(s['monthly_fee'] for s in fee_records_list if s['status'] == 'Pending')
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", tot_s)
    m2.metric("Paid Clear", paid_s)
    m3.metric("Pending Dues", pend_s)
    m4.metric("Pending Amount", f"Rs. {pend_amt:,}")
    
    st.subheader(f"📋 Fee Status Ledger — {fee_class_sel} ({fee_month_input})")
    
    for s_item in fee_records_list:
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
                        # Supabase fee status update trigger goes here
                        st.success(f"Fee collected successfully for {s_item['name']}!")
                        st.rerun()
                else:
                    st.button("🖨️ Print Receipt", key=f"print_btn_{s_item['id']}")
