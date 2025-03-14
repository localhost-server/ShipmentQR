import streamlit as st
import pandas as pd
from utils.data_handler import process_spreadsheet, generate_download_link
from utils.qr_generator import generate_qr_code

# Page config
st.set_page_config(
    page_title="QR Code Generator for Shipping",
    page_icon="📦",
    layout="wide"
)

# Title and description
st.title("📦 QR Code Generator")
st.markdown("""
Upload a spreadsheet to generate QR codes for each row.
Each QR code will contain all the data from that row.
""")

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
        st.success("File processed successfully!")
        
        # Generate QR codes for each row's JSON data
        if 'QR Code' not in df.columns:
            df['QR Code'] = df['JSON_Data'].apply(generate_qr_code)
        
        # Display the data with QR codes
        for index, row in df.iterrows():
            # Get all columns except internal ones
            display_columns = [col for col in df.columns if col not in ['QR Code', 'JSON_Data']]
            
            with st.expander(f"📝 Row {index + 1}"):
                col1, col2 = st.columns([3, 1])
                
                # Display all data fields
                with col1:
                    for col in display_columns:
                        if pd.notna(row[col]):
                            st.write(f"**{col}:**", row[col])
                
                # Display QR code and actions
                with col2:
                    qr_html = f"""
                    <div style='text-align: center;'>
                        <img src='data:image/png;base64,{row["QR Code"]}' 
                             alt='QR Code'
                             style='width: 200px; margin-bottom: 10px;'/>
                    </div>
                    """
                    st.markdown(qr_html, unsafe_allow_html=True)
                    
                    # Download button
                    download_link = generate_download_link(
                        row["QR Code"],
                        f"qr_code_{row['Reference ID']}.png"
                    )
                    st.markdown(download_link, unsafe_allow_html=True)
                    
                    # Print button
                    if st.button("🖨️ Print QR", key=f"print_{index}"):
                        st.markdown(
                            f'''
                            <script>
                                var printWindow = window.open('', '_blank');
                                printWindow.document.write(
                                    '<img src="data:image/png;base64,{row["QR Code"]}" ' +
                                    'style="width: 100%; max-width: 400px;" />'
                                );
                                printWindow.document.close();
                                printWindow.print();
                            </script>
                            ''',
                            unsafe_allow_html=True
                        )
