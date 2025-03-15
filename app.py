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
    layout="wide",
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

# Tabs for generate, settings, and history
tab1, tab2, tab3 = st.tabs(["Generate QR Codes", "Settings", "View QR Codes"])

# Settings tab
with tab2:
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

with tab1:
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

            # Success message with auto-hide
            placeholder = st.empty()
            placeholder.success(f"Processing {len(df)} entries...")
            import time
            time.sleep(2)
            placeholder.empty()

            # Create container for all QR codes
            qr_container = st.container()
            
            # Process each row
            for index, row in df.iterrows():
                # Generate reference ID
                ref_id = str(uuid.uuid4())[:8]
                
                # Combine address fields if present
                address_parts = []
                address_fields = [
                    'Address: Address Line 1',
                    'Address: Address Line 2',
                    'Address: City',
                    'Address: State',
                    'Address: Zip/Postal Code',
                    'Address: Country'
                ]
                
                for field in address_fields:
                    if field in row and pd.notna(row[field]) and str(row[field]).strip():
                        address_parts.append(str(row[field]).strip())
                
                combined_address = ', '.join(address_parts)

                # Format QR code content
                qr_content = (
                    f"SR:\n"
                    f"NM: {sender_settings['name']}\n"
                    f"ADD: {sender_settings['address']}\n"
                    f"CT: {sender_settings['city']}\n"
                    f"STT: {sender_settings['state']}\n"
                    f"CD: {sender_settings['zip']}\n\n"
                    f"AT:\n"
                    f"NM: {row['Artist Name']}\n"
                    f"PH: {row.get('Phone', '')}\n"
                    f"ADD: {combined_address}"
                )

                # Create data dictionary with both sender and artist info
                data = {
                    'reference_id': ref_id,
                    'sender': sender_settings,
                    'Artist Name': row['Artist Name'],
                    'Phone': row.get('Phone', ''),
                    'Address': combined_address
                }

                # Generate QR code with formatted content
                qr_code = generate_qr_code(qr_content)

                # Create entry
                entry = {
                    'reference_id': ref_id,
                    'data': data,
                    'qr_code': qr_code,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                # Save to database
                db.save_entry(entry)

                # Display the entry in the container
                with qr_container:
                    st.markdown("<div class='qr-code-section'>", unsafe_allow_html=True)
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("#### 📤 Sender Information", help=None)
                        st.write("**Name:**", sender_settings['name'])
                        st.write("**Address:**", sender_settings['address'])
                        st.write("**Location:**", f"{sender_settings['city']}, {sender_settings['state']} {sender_settings['zip']}")
                            
                        st.markdown("#### 🎨 Artist Information", help=None)
                        st.write("**Name:**", row['Artist Name'])
                        if pd.notna(row.get('Phone')):
                            st.write("**Phone:**", row['Phone'])
                        if combined_address:
                            st.write("**Address:**", combined_address)
                        
                    with col2:
                        qr_html = f"""
                        <div class='qr-code-container'>
                            <img src='data:image/png;base64,{qr_code}' 
                                 alt='QR Code'
                                 style='width: 200px;'/>
                            <div class='download-link'>
                                {generate_download_link(qr_code, f"qr_code_{ref_id}.png")}
                            </div>
                        </div>
                        """
                        st.markdown(qr_html, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

with tab3:
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
                    st.markdown("#### 📤 Sender Information", help=None)
                    if 'sender' in entry['data']:  # Check for backward compatibility
                        sender = entry['data']['sender']
                        st.write("**Name:**", sender['name'])
                        st.write("**Address:**", sender['address'])
                        st.write("**Location:**", f"{sender['city']}, {sender['state']} {sender['zip']}")
                    
                    st.markdown(f"#### 🎨 Artist Information • *{entry['timestamp']}*", help=None)
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
