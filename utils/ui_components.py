import streamlit as st
import time
import cv2
from pyzbar.pyzbar import decode
import numpy as np

class ScannerUI:
    @staticmethod
    def show_scan_interface(video_placeholder, result_placeholder):
        """Show the scanner interface with video and result placeholders"""
        col1, col2, col3 = st.columns([1,2,1])
        
        with col2:
            if not st.session_state.camera_active:
                with video_placeholder.container():
                    st.info("📸 Ready to scan a QR code? Click the button below to start.")
                    if st.button("📷 Start Camera", type="primary", use_container_width=True):
                        st.session_state.camera_active = True
                        st.rerun()
                    
                    # Show scanning tips
                    with st.expander("📝 Scanning Tips"):
                        st.markdown("""
                        - Ensure good lighting for better scanning
                        - Hold the QR code steady
                        - Keep the QR code within the camera frame
                        - Make sure the QR code is not damaged or obscured
                        - Try different angles if scanning fails
                        """)
                return False
            
            return True

class SettingsUI:
    @staticmethod
    def show_settings_interface(current_settings, save_callback):
        """Display the settings interface"""
        st.markdown("## Sender Settings")
        st.markdown("Configure the sender information to be included in QR codes.")
        
        with st.form("sender_settings"):
            sender_name = st.text_input("Name", value=current_settings["sender"]["name"])
            sender_address = st.text_input("Address Line 1", value=current_settings["sender"]["address"])
            sender_city = st.text_input("City", value=current_settings["sender"]["city"])
            sender_state = st.text_input("State", value=current_settings["sender"]["state"])
            sender_zip = st.text_input("Zip Code", value=current_settings["sender"]["zip"])
            
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
                    save_callback(new_settings)
                    st.success("Settings saved successfully!")
                else:
                    st.error("All fields are required. Please fill in all the information.")

class QRDisplayUI:
    @staticmethod
    def show_qr_entry(entry, download_link_generator):
        """Display a single QR code entry"""
        st.markdown("<div class='qr-code-section'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Sender Information
            st.markdown("#### 📤 Sender Information", help=None)
            if 'sender' in entry['data']:
                sender = entry['data']['sender']
                st.write("**Name:**", sender['name'])
                st.write("**Address:**", sender['address'])
                st.write("**Location:**", f"{sender['city']}, {sender['state']} {sender['zip']}")
            
            # Artist Information
            timestamp_text = f" • *{entry['timestamp']}*" if 'timestamp' in entry else ""
            st.markdown(f"#### 🎨 Artist Information{timestamp_text}", help=None)
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
                    {download_link_generator(entry['qr_code'], f"qr_code_{entry['reference_id']}.png")}
                </div>
            </div>
            """
            st.markdown(qr_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
