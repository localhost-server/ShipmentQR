import streamlit as st
import pandas as pd
from utils.data_handler import generate_download_link
from utils.qr_generator import generate_qr_code
from utils.db_handler import DatabaseHandler
import uuid
from datetime import datetime
import json
import os
import cv2
from pyzbar.pyzbar import decode
import numpy as np

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
st.markdown("# 🎨 Artist QR Code Generator", help=None)

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
    if 'app_state' not in st.session_state:
        st.session_state.app_state = 'idle'  # Possible states: 'idle', 'scanning', 'result_ready'
    if 'camera_key' not in st.session_state:
        st.session_state.camera_key = 0  # Initialize camera key counter
    
    # Create placeholders for video and result
    video_placeholder = st.empty()
    result_placeholder = st.empty()
    
    # Function to process QR code data
    def process_qr_data(qr_data):
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
        
        return "\n".join(formatted_data)
    
    # Function to reset the app state completely
    def reset_app():
        st.session_state.app_state = 'idle'
        st.session_state.camera_active = False
        st.session_state.scan_result = None
        # Increment camera key to force a new camera instance
        st.session_state.camera_key += 1
    
    # Scan control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Camera Scan", type="primary", use_container_width=True):
            st.session_state.app_state = 'scanning'
            st.session_state.camera_active = True
            # Increment camera key to force a new camera instance
            st.session_state.camera_key += 1
    
    with col2:
        if st.button("Reset", use_container_width=True):
            reset_app()
            video_placeholder.empty()
            result_placeholder.empty()
    
    # Display based on app state
    if st.session_state.app_state == 'idle':
        # Show options when idle
        with video_placeholder.container():
            
            if uploaded_file is not None:
                try:
                    # Process uploaded image
                    image_bytes = uploaded_file.getvalue()
                    image_array = np.frombuffer(image_bytes, np.uint8)
                    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    
                    # Convert to RGB for display
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Detect QR codes
                    decoded_objects = decode(rgb_frame)
                    
                    if decoded_objects:
                        obj = decoded_objects[0]  # Get the first QR code
                        
                        # Get QR code data
                        qr_data = obj.data.decode('utf-8')
                        
                        # Draw boundary
                        points = obj.polygon
                        if len(points) > 4:
                            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                            points = hull
                        
                        n = len(points)
                        for j in range(n):
                            cv2.line(rgb_frame, tuple(points[j]), tuple(points[(j+1)%n]), (0,255,0), 3)
                        
                        # Show image with boundary
                        st.image(rgb_frame, channels="RGB", use_column_width=True)
                        
                        # Store in session state
                        st.session_state.scan_result = qr_data
                        st.session_state.app_state = 'result_ready'
                        
                        try:
                            # Format and display result
                            formatted_result = process_qr_data(qr_data)
                            result_placeholder.subheader("QR Code Content:")
                            result_placeholder.code(formatted_result)
                        except Exception as e:
                            st.error(f"Failed to process QR code data: {str(e)}")
                    else:
                        st.error("No QR code detected in the uploaded image. Please try a different image.")
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
    
    # In the scanning section
    elif st.session_state.app_state == 'scanning' and st.session_state.camera_active:
        # Handle camera scanning
        with video_placeholder.container():
            try:
                # Create a temporary container for the camera that can be replaced
                camera_container = st.container()
                
                with camera_container:
                    # Use a dynamic key for the camera input to force a new instance
                    camera_key = f"qr_scanner_{st.session_state.camera_key}"
                    camera_input = st.camera_input(label="Scan QR Code", key=camera_key)
                    
                    if camera_input:
                        # Process the image
                        image_bytes = camera_input.getvalue()
                        image_array = np.frombuffer(image_bytes, np.uint8)
                        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Detect QR codes
                        decoded_objects = decode(rgb_frame)
                        
                        if decoded_objects:
                            obj = decoded_objects[0]  # Get the first QR code
                            qr_data = obj.data.decode('utf-8')
                            
                            # Draw boundary
                            points = obj.polygon
                            if len(points) > 4:
                                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                                points = hull
                            
                            n = len(points)
                            for j in range(n):
                                cv2.line(rgb_frame, tuple(points[j]), tuple(points[(j+1)%n]), (0,255,0), 3)
                            
                            # Clear the camera input and show only the captured image
                            camera_container.empty()  # Clear the camera input
                            video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                            
                            # Rest of the code for processing the QR data
                            st.session_state.scan_result = qr_data
                            st.session_state.camera_active = False
                            st.session_state.app_state = 'result_ready'
                            
                            # Format and display result
                            try:
                                formatted_result = process_qr_data(qr_data)
                                result_placeholder.subheader("QR Code Content:")
                                result_placeholder.code(formatted_result)
                            except Exception as e:
                                st.error(f"Failed to process QR code data: {str(e)}")
                        else:
                            st.info("Position QR code in view. No QR code detected yet.")
                
            except Exception as e:
                st.error(f"Camera error: {str(e)}")
                st.session_state.camera_active = False
                st.session_state.app_state = 'idle'
                st.info("Camera access failed. Please try uploading an image instead.")
                    
    elif st.session_state.app_state == 'result_ready':
        # Display the previous scan result
        if st.session_state.scan_result:
            try:
                # Format and display
                formatted_result = process_qr_data(st.session_state.scan_result)
                result_placeholder.subheader("QR Code Content:")
                result_placeholder.code(formatted_result)
                
                # Option to scan again
                if st.button("Scan Another", use_container_width=True):
                    reset_app()  # Use the reset function to ensure consistent state reset
            except Exception as e:
                st.error(f"Error displaying results: {str(e)}")

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
