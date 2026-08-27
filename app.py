import streamlit as st
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="School Management System (ERP)",
    page_icon="🏫",
    layout="wide"
)

# --- 2. SUPABASE CONNECTION SETUP ---
# Yeh keys aapke Streamlit Secrets se data uthayengi
try:
    SUPABASE_URL = st.secrets["supabase_url"]
    SUPABASE_KEY = st.secrets["supabase_key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("⚠️ Supabase connection failed! Please check your Streamlit Secrets.")
    st.stop()

# --- 3. MAIN NAVIGATION TABS ---
st.title("🏫 School Management System")
st.markdown("Manage Staff, Student Admissions, and Monthly Fees from one unified portal.")

tab_staff, tab_students, tab_fee = st.tabs([
    "👥 Staff Management", 
    "🎓 Student Admissions", 
    "💳 Fee Management"
])

# ==========================================
# TAB 1: STAFF MANAGEMENT (Purana Module)
# ==========================================
with tab_staff:
    st.header("👥 Staff Record Book")
    st.markdown("Manage your school staff details, designations, and records here.")
    
    # Yahan aap apna pehle wala staff management ka code ya form rakh sakte hain
    # Misal ke tor par ek simple input form:
    with st.form("staff_form"):
        st.subheader("Add New Staff Member")
        s_name = st.text_input("Staff Name")
        s_role = st.selectbox("Designation", ["Teacher", "Administrator", "Principal", "Support Staff"])
        s_phone = st.text_input("Phone Number")
        
        submitted_staff = st.form_submit_button("Save Staff Member")
        if submitted_staff:
            if s_name:
                # Supabase insert logic (Example)
                try:
                    data = {"name": s_name, "designation": s_role, "phone": s_phone}
                    # supabase.table("staff").insert(data).execute() # Table hone par uncomment karein
                    st.success(f"Staff member {s_name} added successfully!")
                except Exception as ex:
                    st.error(f"Error: {ex}")
            else:
                st.warning("Please enter staff name.")
                
    st.divider()
    st.subheader("Current Staff List")
    st.info("Staff records fetched from Supabase will appear here.")

# ==========================================
# TAB 2: STUDENT ADMISSIONS
# ==========================================
with tab_students:
    st.header("🎓 Student Admissions & Records")
    st.markdown("Register new students and manage class-wise enrollment.")
    
    with st.form("student_admission_form"):
        st.subheader("New Student Registration Form")
        col1, col2 = st.columns(2)
        
        with col1:
            std_name = st.text_input("Student Full Name")
            father_name = st.text_input("Father's Name")
            
        with col2:
            class_selected = st.selectbox("Assign Class", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5"])
            monthly_fee_amount = st.number_input("Monthly Fee Amount (Rs.)", min_value=0, value=3000, step=500)
            
        submit_student = st.form_submit_button("Register Student")
        
        if submit_student:
            if std_name and father_name:
                try:
                    # Supabase mein students table mein data save karne ka code
                    student_data = {
                        "name": std_name,
                        "father_name": father_name,
                        "class_name": class_selected,
                        "monthly_fee": monthly_fee_amount
                    }
                    # supabase.table("students").insert(student_data).execute()
                    st.success(f"Student {std_name} successfully enrolled in {class_selected}!")
                except Exception as e:
                    st.error(f"Error saving student: {e}")
            else:
                st.warning("Please fill in all mandatory fields.")

    st.divider()
    st.subheader("🔍 Class-wise Student Directory")
    filter_class = st.selectbox("Select Class to View Students", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5"], key="filter_cls")
    
    # Sample view table (Jab Supabase se data aayega toh yeh dynamic ho jayega)
    st.write(f"Showing enrolled students for: **{filter_class}**")
    sample_df = pd.DataFrame([
        {"Roll No": "ST-001", "Student Name": "Ali Khan", "Father Name": "Ahmed Khan", "Monthly Fee": 3000},
        {"Roll No": "ST-002", "Student Name": "Sara Ahmed", "Father Name": "Tariq Ahmed", "Monthly Fee": 3000},
    ])
    st.dataframe(sample_df, use_container_width=True)

# ==========================================
# TAB 3: FEE MANAGEMENT & TRACKER
# ==========================================
with tab_fee:
    st.header("💳 Monthly Fee Management & Pending Dues")
    current_month = datetime.now().strftime("%B %Y")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        fee_class_filter = st.selectbox("Select Class for Fee Status", ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5"], key="fee_cls")
    with f_col2:
        fee_month = st.text_input("Billing Month & Year", value=current_month)
        
    st.divider()
    
    # Mock / Live data simulation for fee status
    fee_students = [
        {"id": "ST-001", "name": "Ali Khan", "monthly_fee": 3000, "status": "Pending"},
        {"id": "ST-002", "name": "Sara Ahmed", "monthly_fee": 3000, "status": "Paid"},
    ]
    
    # Top Metrics Dashboard
    t_total = len(fee_students)
    t_paid = sum(1 for s in fee_students if s['status'] == 'Paid')
    t_pending = sum(1 for s in fee_students if s['status'] == 'Pending')
    t_pending_amt = sum(s['monthly_fee'] for s in fee_students if s['status'] == 'Pending')
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Students", t_total)
    m2.metric("Paid Count", t_paid)
    m3.metric("Pending Count", t_pending)
    m4.metric("Pending Dues", f"Rs. {t_pending_amt:,}")
    
    st.subheader(f"📋 Fee Record List — {fee_class_filter} ({fee_month})")
    
    for std in fee_students:
        with st.container(border=True):
            col_info, col_status, col_action = st.columns([4, 2, 2])
            
            with col_info:
                st.markdown(f"**{std['name']}** (`{std['id']}`)")
                st.caption(f"Due Amount: Rs. {std['monthly_fee']:,}")
                
            with col_status:
                if std["status"] == "Paid":
                    st.markdown("🟢 **<span style='color:green;'>PAID / CLEAR</span>**", unsafe_allow_html=True)
                else:
                    st.markdown("🔴 **<span style='color:red;'>PENDING</span>**", unsafe_allow_html=True)
                    
            with col_action:
                if std["status"] == "Pending":
                    if st.button("✅ Collect Fee", key=f"pay_{std['id']}", type="primary"):
                        # Yahan Supabase mein status 'Paid' update karne ki query aayegi
                        st.success(f"Fee collected successfully for {std['name']}!")
                        st.rerun()
                else:
                    st.button("🖨️ Print Receipt", key=f"print_{std['id']}")
