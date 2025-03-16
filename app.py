import streamlit as st
import pandas as pd
from utils.data_handler import generate_download_link
from utils.qr_generator import generate_qr_code
from utils.db_handler import DatabaseHandler
import uuid
from datetime import datetime
import json
from pyzbar.pyzbar import decode
import numpy as np
from PIL import Image
import io

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
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("## 🎨 Artist QR Code Generator", help=None)

from utils.qr_scanner import QRScanner
from utils.ui_components import ScannerUI, SettingsUI, QRDisplayUI

# Initialize session state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = None
    st.session_state.scan_result = None
    st.session_state.camera_active = False
    st.session_state.last_scan_time = None
    st.session_state.formatted_result = None

# Settings management
def load_settings():
    # First check if settings exist in session state
    if 'settings' in st.session_state:
        return st.session_state.settings
    
    # Try to load from file
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            st.session_state.settings = settings
            return settings
    except:
        # Return default settings
        default_settings = {
            "sender": {
                "name": "Default Name",
                "address": "Default Address",
                "city": "Default City",
                "state": "Default State",
                "zip": "00000"
            }
        }
        st.session_state.settings = default_settings
        return default_settings

def save_settings(settings):
    # Update session state
    st.session_state.settings = settings
    # Try to save to file (may not work in cloud)
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
    except:
        pass  # Ignore file write errors in cloud environment

# Tabs for generate, scan, settings, and history
tab1, tab2, tab3, tab4 = st.tabs(["Gen QR", "Scan QR", "View QR", "Settings"])

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
                        st.markdown("#### 🎨 Artist Information", help=None)
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
    
    # Initialize session state variables if they don't exist
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False
    if 'scan_result' not in st.session_state:
        st.session_state.scan_result = None
    
    # Create placeholders for video and result
    result_placeholder = st.empty()
    
    # Camera component with Streamlit
    camera_image = st.camera_input("Scan QR Code")
    
    if camera_image is not None:
        # Convert the image to PIL Image
        img = Image.open(camera_image)
        
        # Convert to numpy array for pyzbar
        img_array = np.array(img)
        
        # Detect QR codes
        decoded_objects = decode(img_array)
        
        if decoded_objects:
            for obj in decoded_objects:
                # Get QR code data
                qr_data = obj.data.decode('utf-8')
                
                # Store in session state
                st.session_state.scan_result = qr_data
                
                # Parse and format QR data
                lines = qr_data.split('\n')
                formatted_data = []
                
                # Format sender info
                formatted_data.append("Sender:")
                for line in lines:
                    if line.startswith("SR:"):
                        continue
                    elif line.startswith("NM:"):
                        formatted_data.append(f"Name: {line[3:].strip()}")
                    elif line.startswith("ADD:"):
                        formatted_data.append(f"Address: {line[4:].strip()}")
                    elif line.startswith("CT:"):
                        formatted_data.append(f"City: {line[3:].strip()}")
                    elif line.startswith("STT:"):
                        formatted_data.append(f"State: {line[4:].strip()}")
                    elif line.startswith("CD:"):
                        formatted_data.append(f"ZipCode: {line[3:].strip()}")
                    elif line.startswith("AT:"):
                        formatted_data.append("\nArtist:")
                    elif line.startswith("PH:"):
                        formatted_data.append(f"Phone: {line[3:].strip()}")
                    # Handle artist name and address
                    elif line.startswith("NM:") and formatted_data[-1] == "\nArtist:":
                        formatted_data.append(f"Name: {line[3:].strip()}")
                    elif line.startswith("ADD:") and "\nArtist:" in formatted_data:
                        formatted_data.append(f"Address: {line[4:].strip()}")
                
                formatted_result = "\n".join(formatted_data)
                
                # Show result
                result_placeholder.subheader("QR Code Content:")
                result_placeholder.code(formatted_result)
                break
        else:
            st.info("No QR code detected. Please try again.")

# View QR tab
with tab3:
    # Update tab state
    st.session_state.active_tab = 'history'
    st.session_state.scan_result = None
    
    st.markdown("## QR Code History")
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
        
        # Display each QR code entry
        for entry in entries:
            QRDisplayUI.show_qr_entry(entry, generate_download_link)

# Settings tab
with tab4:
    # Update tab state
    st.session_state.active_tab = 'settings'
    st.session_state.scan_result = None
    
    # Show settings interface
    settings = load_settings()
    SettingsUI.show_settings_interface(settings, save_settings)
