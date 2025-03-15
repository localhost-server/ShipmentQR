import streamlit as st
import pandas as pd
from utils.data_handler import generate_download_link
from utils.qr_generator import generate_qr_code
import uuid
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Artist QR Code Generator",
    page_icon="🎨",
    layout="wide"
)

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

# Title and description
st.title("🎨 Artist QR Code Generator")

# Tabs for upload and history
tab1, tab2 = st.tabs(["Generate QR Codes", "History"])

with tab1:
    st.markdown("""
    Upload a spreadsheet containing artist information to generate QR codes.
    Required fields: Artist Name
    Optional fields: Phone, Address details
    """)

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

            st.success("File processed successfully!")

            # Process each row
            for index, row in df.iterrows():
                # Generate reference ID
                ref_id = str(uuid.uuid4())[:8]

                # Combine address fields
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

                # Create data dictionary
                data = {
                    'reference_id': ref_id,
                    'Artist Name': row['Artist Name'],
                    'Phone': row.get('Phone', ''),
                    'Address': combined_address
                }

                # Generate QR code
                qr_code = generate_qr_code(str(data))

                # Create a history entry
                history_entry = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'artist_name': row['Artist Name'],
                    'reference_id': ref_id,
                    'data': data,
                    'qr_code': qr_code
                }
                st.session_state.history.append(history_entry)

                st.markdown(f"### 🎨 {row['Artist Name']}")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**Artist Name:**", row['Artist Name'])
                    if pd.notna(row.get('Phone')):
                        st.write("**Phone:**", row['Phone'])
                    if combined_address:
                        st.write("**Address:**", combined_address)
                
                with col2:
                    # Display QR code
                    qr_html = f"""
                    <div style='text-align: center;'>
                        <img src='data:image/png;base64,{qr_code}' 
                             alt='QR Code'
                             style='width: 200px; margin-bottom: 10px;'/>
                    </div>
                    """
                    st.markdown(qr_html, unsafe_allow_html=True)
                    
                    # Download button
                    download_link = generate_download_link(
                        qr_code,
                        f"qr_code_{ref_id}.png"
                    )
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    # Print button
                    if st.button("🖨️ Print QR", key=f"print_{index}"):
                        st.markdown(
                            f'''
                            <script>
                                var printWindow = window.open('', '_blank');
                                printWindow.document.write(
                                    '<img src="data:image/png;base64,{qr_code}" ' +
                                    'style="width: 100%; max-width: 400px;" />'
                                );
                                printWindow.document.close();
                                printWindow.print();
                            </script>
                            ''',
                            unsafe_allow_html=True
                        )

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

with tab2:
    if not st.session_state.history:
        st.info("No QR codes have been generated yet. Upload a spreadsheet to get started.")
    else:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.history = []
                st.rerun()
        
        st.markdown("## Generated QR Codes")
        
        for entry in reversed(st.session_state.history):
            st.markdown(f"### 🎨 {entry['artist_name']}")
            st.markdown(f"*Generated on: {entry['timestamp']}*")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write("**Artist Name:**", entry['data']['Artist Name'])
                if entry['data']['Phone']:
                    st.write("**Phone:**", entry['data']['Phone'])
                if entry['data']['Address']:
                    st.write("**Address:**", entry['data']['Address'])
            
            with col2:
                qr_html = f"""
                <div style='text-align: center;'>
                    <img src='data:image/png;base64,{entry['qr_code']}' 
                         alt='QR Code'
                         style='width: 200px; margin-bottom: 10px;'/>
                </div>
                """
                st.markdown(qr_html, unsafe_allow_html=True)
                
                # Download button
                download_link = generate_download_link(
                    entry['qr_code'],
                    f"qr_code_{entry['reference_id']}.png"
                )
                st.markdown(download_link, unsafe_allow_html=True)
                
                # Print button
                if st.button("🖨️ Print QR", key=f"print_history_{entry['reference_id']}"):
                    st.markdown(
                        f'''
                        <script>
                            var printWindow = window.open('', '_blank');
                            printWindow.document.write(
                                '<img src="data:image/png;base64,{entry["qr_code"]}" ' +
                                'style="width: 100%; max-width: 400px;" />'
                            );
                            printWindow.document.close();
                            printWindow.print();
                        </script>
                        ''',
                        unsafe_allow_html=True
                    )
            
            st.markdown("---")
