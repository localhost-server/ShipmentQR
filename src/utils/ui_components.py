import streamlit as st

# Custom CSS
custom_css = """
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
    /* Hide the "Take Photo" button on camera component */
    button[data-testid="stCameraInputButton"] {
        display: none !important;
    }
</style>
"""

def init_ui():
    """Initialize UI components and styling"""
    st.set_page_config(
        page_title="Artist QR Code Generator",
        page_icon="🎨",
        initial_sidebar_state="collapsed"
    )
    st.markdown(custom_css, unsafe_allow_html=True)
    st.markdown("## 🎨 Artist QR Code Generator", help=None)

def show_qr_entry(entry, download_link_generator):
    """Display a single QR code entry"""
    st.markdown("<div class='qr-code-section'>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
