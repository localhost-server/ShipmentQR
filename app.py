import streamlit as st
import pandas as pd

from src.utils.ui_components import init_ui, show_qr_entry, show_settings_interface
from src.core.db_handler import DatabaseHandler
from src.core.qr_handler import generate_download_link, process_upload_data
from src.utils.settings_handler import load_settings, save_settings, validate_sender_settings

# Initialize UI
init_ui()

# Initialize database
try:
    db = DatabaseHandler()
except Exception as e:
    st.error(f"Error initializing database: {e}")
    db = None

# Initialize session state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'generate'

# Radio button for navigation
tab_options = ["Gen QR", "View QR", "Settings"]
selected_tab = st.radio("Select Function:", tab_options, horizontal=True, 
                       index=tab_options.index(st.session_state.active_tab) if st.session_state.active_tab in tab_options else 0)

# Handle tab switching
if selected_tab == "Gen QR":
    st.session_state.active_tab = 'generate'
elif selected_tab == "View QR":
    st.session_state.active_tab = 'history'
elif selected_tab == "Settings":
    st.session_state.active_tab = 'settings'

# Display content based on selected tab
if st.session_state.active_tab == 'generate':
    st.markdown("## Generate QR Codes")
    
    # Load sender settings
    sender_settings = load_settings()["sender"]
    
    # Check if sender settings are configured
    if not validate_sender_settings({"sender": sender_settings}):
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
            else:
                df = pd.read_excel(uploaded_file)
            
            # Check for required Artist Name column
            if 'Artist Name' not in df.columns:
                st.error("Missing required column: Artist Name")
                st.stop()
            
            # Process entries
            with st.spinner(f"Processing {len(df)} entries..."):
                entries = process_upload_data(df, sender_settings)
                
                # Save entries to database
                for entry in entries:
                    db.save_entry(entry)
                
                # Display success message and newly generated QR codes
                st.success(f"Successfully processed {len(df)} entries!")
                st.markdown("## Generated QR Codes")
                
                # Display only the newly generated QR codes
                for entry in entries:
                    show_qr_entry(entry, generate_download_link)
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

elif st.session_state.active_tab == 'history':
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
            show_qr_entry(entry, generate_download_link)

elif st.session_state.active_tab == 'settings':
    # Show settings interface
    settings = load_settings()
    show_settings_interface(settings, save_settings)
