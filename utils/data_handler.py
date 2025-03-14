import pandas as pd
import uuid
from typing import Tuple, Optional, Dict
from .db_handler import DatabaseHandler

def generate_reference_id() -> str:
    """Generate a unique 8-character reference ID."""
    return str(uuid.uuid4())[:8]

def combine_address(row: pd.Series) -> str:
    """Combine all address fields into a single string."""
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
    
    return ', '.join(address_parts)

def row_to_dict(row: pd.Series) -> Dict:
    """Convert a row to a dictionary with required fields."""
    required_fields = {
        'Artist Name': row.get('Artist Name', ''),
        'Phone': row.get('Phone', ''),
        'Address': combine_address(row)
    }
    
    # Remove empty values
    return {k: v for k, v in required_fields.items() if pd.notna(v) and str(v).strip()}

def process_spreadsheet(file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Process uploaded spreadsheet and store data in database.
    Returns tuple of (DataFrame, error_message)
    """
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, "Unsupported file format. Please upload CSV or Excel file."

        # Check for required field: Artist Name
        if 'Artist Name' not in df.columns:
            return None, "Missing required column: Artist Name"

        # Initialize database handler
        db = DatabaseHandler()
        
        # Process each row and store in database
        reference_ids = []
        for _, row in df.iterrows():
            # Convert row to dictionary
            row_data = row_to_dict(row)
            
            # Generate reference ID
            ref_id = generate_reference_id()
            while db.reference_id_exists(ref_id):
                ref_id = generate_reference_id()
            
            # Save to database
            if db.save_data(ref_id, row_data):
                reference_ids.append(ref_id)
            else:
                return None, "Error saving data to database"
        
        # Add reference IDs to DataFrame
        df['Reference ID'] = reference_ids
        
        # Convert each row to JSON string for QR code
        df['JSON_Data'] = df.apply(lambda row: str({
            'reference_id': row['Reference ID'],
            **row_to_dict(row)
        }), axis=1)
        
        return df, None
        
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def generate_download_link(img_base64: str, filename: str) -> str:
    """Generate HTML download link for QR code image."""
    return f'<a href="data:image/png;base64,{img_base64}" download="{filename}">Download QR</a>'
