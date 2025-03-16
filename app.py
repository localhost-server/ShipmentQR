import streamlit as st
import pandas as pd
from utils.data_handler import generate_download_link
from utils.qr_generator import generate_qr_code
from utils.db_handler import DatabaseHandler
import uuid
from datetime import datetime
import json
import os

# Page config
st.set_page_config(
    page_title="Artist QR Code Generator",
    page_icon="🎨",
    initial_sidebar_state="collapsed"
)

# Initialize database
db = DatabaseHandler()

# Custom CSS
st.markdown("""
<style>
    .block-container {
        padding: 0.25rem;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding: 0;
    }
    div[data-testid="stMarkdown"] > div {
        line-height: 0.5;
        margin: 0;
        padding: 0;
    }
    div[data-testid="stMarkdown"] p {
        margin: 0;
        padding: 0;
    }
    .element-container {
        margin: 0;
        padding: 0;
    }
    /* Reduce space between write elements */
    div[data-testid="stText"] {
        line-height: 0.8;
        margin: 0;
        padding: 0;
    }
    button[data-baseweb="tab"] {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }
    .stMarkdown {
        margin: 0;
    }
    .qr-code-container {
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .qr-code-section, .history-section {
        margin-bottom: 0.25rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #f0f0f0;
    }
    .download-link {
        display: block;
        text-align: center;
        margin-top: 0.25rem;
    }
    /* Scanning animation styles */
    @keyframes scan {
        0% {
            transform: translateY(-100%);
            opacity: 0.5;
        }
        50% {
            opacity: 1;
        }
        100% {
            transform: translateY(100%);
            opacity: 0.5;
        }
    }
    .camera-container {
        position: relative;
        overflow: hidden;
        border-radius: 4px;
    }
    .scan-line {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: #00ff00;
        animation: scan 2s linear infinite;
        box-shadow: 0 0 8px #00ff00;
    }
    .scan-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border: 2px solid #00ff00;
        border-radius: 4px;
        box-shadow: 0 0 0 1px rgba(0,255,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("## 🎨 Artist QR Code Generator", help=None)

# Function to load settings
def load_settings():
    if os.path.exists('settings.json'):
        with open('settings.json', 'r') as f:
            return json.load(f)
    return {"sender": {"name": "", "address": "", "city": "", "state": "", "zip": ""}}

# Function to save settings
def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

from utils.qr_scanner import QRScanner

# Initialize session state for tab tracking
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = None
    st.session_state.scan_result = None

# Tabs for generate, scan, settings, and history
tab1, tab2, tab3, tab4 = st.tabs(["Gen QR", "Scan QR", "View QR","Settings"])

with tab1:
    # Update tab state
    st.session_state.active_tab = 'generate'
    st.session_state.scan_result = None
    st.markdown("## Generate QR Codes")

    # Load sender settings
    sender_settings = load_settings()["sender"]

    # Check if sender settings are configured
    if not all(sender_settings.values()):
        st.error("Please configure sender information in the Settings tab first.")
        st.stop()

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file (CSV or Excel)",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Unsupported file format. Please upload CSV or Excel file.")
                st.stop()

            # Check for required Artist Name column
            if 'Artist Name' not in df.columns:
                st.error("Missing required column: Artist Name")
                st.stop()

            # Process entries
            with st.spinner(f"Processing {len(df)} entries..."):
                qr_container = st.container()
                
                for index, row in df.iterrows():
                    # Generate reference ID
                    ref_id = str(uuid.uuid4())[:8]
                    
                    # Combine address fields
                    address_parts = []
                    address_fields = ['Address: Address Line 1', 'Address: Address Line 2', 'Address: City',
                                    'Address: State', 'Address: Zip/Postal Code', 'Address: Country']
                    
                    for field in address_fields:
                        if field in row and pd.notna(row[field]) and str(row[field]).strip():
                            address_parts.append(str(row[field]).strip())
                    
                    combined_address = ', '.join(address_parts)

                    # Generate and save entry
                    qr_content = (
                        f"SR:\nNM: {sender_settings['name']}\nADD: {sender_settings['address']}\n"
                        f"CT: {sender_settings['city']}\nSTT: {sender_settings['state']}\n"
                        f"CD: {sender_settings['zip']}\n\nAT:\nNM: {row['Artist Name']}\n"
                        f"PH: {row.get('Phone', '')}\nADD: {combined_address}"
                    )
                    
                    qr_code = generate_qr_code(qr_content)
                    
                    entry = {
                        'reference_id': ref_id,
                        'data': {
                            'sender': sender_settings,
                            'Artist Name': row['Artist Name'],
                            'Phone': row.get('Phone', ''),
                            'Address': combined_address
                        },
                        'qr_code': qr_code,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    db.save_entry(entry)

                # Display generated QR codes
                st.success(f"Successfully processed {len(df)} entries!")
                st.markdown("## Generated QR Codes")
                
                for entry in db.get_all_entries():
                    st.markdown("<div class='qr-code-section'>", unsafe_allow_html=True)
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("#### 🎨 Artist Details", help=None)
                        st.write("**Name:**", entry['data']['Artist Name'])
                        if entry['data']['Phone']:
                            st.write("**Phone:**", entry['data']['Phone'])
                        if entry['data']['Address']:
                            st.write("**Address:**", entry['data']['Address'])
                    
                    with col2:
                        qr_html = f"""
                        <div class='qr-code-container'>
                            <img src='data:image/png;base64,{entry['qr_code']}' 
                                 alt='QR Code'
                                 style='width: 200px;'/>
                            <div class='download-link'>
                                {generate_download_link(entry['qr_code'], f"qr_code_{entry['reference_id']}.png")}
                            </div>
                        </div>
                        """
                        st.markdown(qr_html, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# Scan QR tab
with tab2:
    # Update tab state
    st.session_state.active_tab = 'scan'
    st.session_state.scan_result = None
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    
    st.markdown("## Scan QR")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.session_state.scan_result:
            st.success("QR Code detected!")
            formatted_result = QRScanner.format_scan_result(st.session_state.scan_result)
            st.text_area("QR Code Content", value=formatted_result, height=250, disabled=True)
            if st.button("Start New Scan"):
                st.session_state.scan_result = None
                st.session_state.camera_active = True
                st.experimental_rerun()
        else:
            if not st.session_state.camera_active:
                st.info("📸 Click the button below to start scanning")
                st.markdown("""
                    <style>
                        .guide-text {
                            text-align: center;
                            padding: 1rem;
                            background: #f0f2f6;
                            border-radius: 4px;
                            margin-bottom: 1rem;
                        }
                    </style>
                    <div class="guide-text">
                        <p>🎯 Hold the QR code steady and centered in the camera view</p>
                        <p>📱 Keep your device about 6-8 inches away from the code</p>
                        <p>💡 Ensure good lighting and minimal glare</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Start Camera", use_container_width=True):
                    st.session_state.camera_active = True
                    st.experimental_rerun()
            else:
                # Camera container with scanning animation
                camera_container = st.container()
                with camera_container:
                    st.markdown("""
                        <style>
                            [data-testid="stCamera"] > div {
                                min-height: 400px !important;
                            }
                            [data-testid="stCamera"] video {
                                min-height: 400px !important;
                                object-fit: cover;
                            }
                        </style>
                        <div class="camera-container">
                            <div class="scan-line"></div>
                            <div class="scan-overlay"></div>
                    """, unsafe_allow_html=True)
                    
                    scanning_spinner = st.empty()
                    with scanning_spinner:
                        st.info("🔍 Scanning for QR code...")
                    
                    results, error = QRScanner.scan_from_camera()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if results:
                        scanning_spinner.success("✅ QR Code detected!")
                        st.session_state.scan_result = results[0]
                        st.session_state.camera_active = False
                        st.experimental_rerun()
                    elif error:
                        if error != "No QR code found in camera frame":
                            scanning_spinner.error(error)
                    
                    col1, col2 = st.columns([4, 1])
                    with col2:
                        if st.button("Stop Camera", type="secondary"):
                            st.session_state.camera_active = False
                            st.experimental_rerun()

# View QR tab
with tab3:
    # Update tab state
    st.session_state.active_tab = 'history'
    st.session_state.scan_result = None
    st.markdown("## History")
    entries = db.get_all_entries()
    if not entries:
        st.info("No QR codes have been generated yet. Upload a spreadsheet to get started.")
    else:
        if st.button("🗑️ Clear All Data", type="secondary"):
            if db.clear_all():
                st.success("All data has been cleared!")
                st.rerun()
            else:
                st.error("Error clearing data. Please try again.")
        
        st.markdown("## Generated QR Codes", help=None)
        
        for entry in entries:
            with st.container():
                st.markdown("<div class='history-section'>", unsafe_allow_html=True)
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"#### 🎨 Artist Details • *{entry['timestamp']}*", help=None)
                    st.write("**Name:**", entry['data']['Artist Name'])
                    if entry['data']['Phone']:
                        st.write("**Phone:**", entry['data']['Phone'])
                    if entry['data']['Address']:
                        st.write("**Address:**", entry['data']['Address'])
                    
                with col2:
                    qr_html = f"""
                    <div class='qr-code-container'>
                        <img src='data:image/png;base64,{entry['qr_code']}' 
                             alt='QR Code'
                             style='width: 200px;'/>
                        <div class='download-link'>
                            {generate_download_link(entry['qr_code'], f"qr_code_{entry['reference_id']}.png")}
                        </div>
                    </div>
                    """
                    st.markdown(qr_html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# Settings tab
with tab4:
    # Update tab state
    st.session_state.active_tab = 'settings'
    st.session_state.scan_result = None
    st.markdown("## Sender Settings")
    st.markdown("Configure the sender information to be included in QR codes.")
    
    # Load current settings
    settings = load_settings()
    
    # Create form for settings
    with st.form("sender_settings"):
        sender_name = st.text_input("Name", value=settings["sender"]["name"])
        sender_address = st.text_input("Address Line 1", value=settings["sender"]["address"])
        sender_city = st.text_input("City", value=settings["sender"]["city"])
        sender_state = st.text_input("State", value=settings["sender"]["state"])
        sender_zip = st.text_input("Zip Code", value=settings["sender"]["zip"])
        
        submit = st.form_submit_button("Save Settings")
        
        if submit:
            # Validate all fields are filled
            if all([sender_name, sender_address, sender_city, sender_state, sender_zip]):
                new_settings = {
                    "sender": {
                        "name": sender_name,
                        "address": sender_address,
                        "city": sender_city,
                        "state": sender_state,
                        "zip": sender_zip
                    }
                }
                save_settings(new_settings)
                st.success("Settings saved successfully!")
            else:
                st.error("All fields are required. Please fill in all the information.")
