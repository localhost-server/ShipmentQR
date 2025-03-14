import streamlit as st
import pandas as pd
from utils.data_handler import process_spreadsheet, generate_download_link
from utils.qr_generator import generate_qr_code
from utils.db_handler import DatabaseHandler

# Page config
st.set_page_config(
    page_title="QR Code Generator for Shipping",
    page_icon="📦",
    layout="wide"
)

# Initialize database
db = DatabaseHandler()

# Title and description
st.title("📦 QR Code Generator")
st.markdown("""
Upload a spreadsheet to generate QR codes for each row.
Each QR code will contain all the data from that row.
Data will be stored with unique reference IDs to avoid duplicates.
""")

# Tabs for upload and view
tab1, tab2 = st.tabs(["Upload New Data", "View Existing Data"])

with tab1:
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file (CSV or Excel)",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:
        # Process the uploaded file
        df, error = process_spreadsheet(uploaded_file)
        
        if error:
            st.error(error)
        else:
            st.success("File processed successfully! Data stored in database.")
            
            # Generate QR codes for each row's JSON data
            if 'QR Code' not in df.columns:
                df['QR Code'] = df['JSON_Data'].apply(generate_qr_code)
            
            # Display the data with QR codes
            for index, row in df.iterrows():
                # Get all columns except internal ones
                display_columns = [col for col in df.columns if col not in ['QR Code', 'JSON_Data']]
                
                with st.expander(f"📝 Reference ID: {row['Reference ID']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    # Display all data fields
                    with col1:
                        for col in display_columns:
                            if pd.notna(row[col]):
                                st.write(f"**{col}:**", row[col])

with tab2:
    # Get all reference IDs
    ref_ids = db.get_all_reference_ids()
    
    # Initialize session state for confirmation
    if 'show_confirm' not in st.session_state:
        st.session_state.show_confirm = False

    # Add Clear Data button with confirmation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if not st.session_state.show_confirm:
            if st.button("🗑️ Clear All Data", type="secondary"):
                st.session_state.show_confirm = True
                st.rerun()
        else:
            st.warning("⚠️ Are you sure you want to clear all data? This cannot be undone.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Clear Data", type="primary"):
                    if db.clear_data():
                        st.session_state.show_confirm = False
                        st.success("All data has been cleared!")
                        st.rerun()
                    else:
                        st.error("Error clearing data. Please try again.")
            with col2:
                if st.button("No, Cancel", type="secondary"):
                    st.session_state.show_confirm = False
                    st.rerun()
    
    if not ref_ids:
        st.info("No data available. Upload a spreadsheet to get started.")
    else:
        st.write("### Stored Data")
        st.caption("Note: Clear data to remove any private information before sharing with others.")
        for ref_id in ref_ids:
            data = db.get_data(ref_id)
            if data:
                with st.expander(f"📝 Reference ID: {ref_id}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        for key, value in data.items():
                            if pd.notna(value):
                                st.write(f"**{key}:**", value)
                
                    # Generate and display QR code
                    qr_json = str({'reference_id': ref_id, **data})
                    qr_code = generate_qr_code(qr_json)
                    
                    with col2:
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
                        if st.button("🖨️ Print QR", key=f"print_{ref_id}"):
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
