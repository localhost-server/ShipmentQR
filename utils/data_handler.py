import pandas as pd
import uuid
from typing import Tuple, Optional

def process_spreadsheet(file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Process uploaded spreadsheet and convert each row to JSON for QR code.
    Returns tuple of (DataFrame, error_message)
    """
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, "Unsupported file format. Please upload CSV or Excel file."

        # Add reference ID column
        df['Reference ID'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
            
        # Convert each row to JSON string
        df['JSON_Data'] = df.apply(lambda row: row.to_json(), axis=1)
        
        return df, None
        
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def generate_download_link(img_base64: str, filename: str) -> str:
    """Generate HTML download link for QR code image."""
    return f'<a href="data:image/png;base64,{img_base64}" download="{filename}">Download QR</a>'
