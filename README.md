# QR Code Generator

A Streamlit web application that generates QR codes for artist shipping information.

## Features

- Upload CSV or Excel files
- Generate QR codes for each artist
- Download or print QR codes
- SQLite database for data persistence
- Unique reference IDs to avoid duplicates
- View all previously generated QR codes
- Clear data functionality for privacy protection

## Required Spreadsheet Fields

- Artist Name (required)
- Phone (optional)
- Address Fields (optional):
  - Address Line 1
  - Address Line 2
  - City
  - State
  - Zip/Postal Code
  - Country
  
All address fields will be combined into a single address string in the QR code.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/QRGen.git
cd QRGen
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Open your browser and go to `http://localhost:8501`

3. Upload your spreadsheet (CSV or Excel) with artist information

4. View, download, or print QR codes for each artist

## Project Structure

```
QRGen/
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
├── qr_data.db         # SQLite database
└── utils/
    ├── __init__.py
    ├── data_handler.py # Spreadsheet processing
    ├── qr_generator.py # QR code generation
    └── db_handler.py   # Database operations
```

## Database

The application uses SQLite for data persistence:
- Each artist gets a unique reference ID
- Data includes artist name, phone, and combined address
- Prevents duplicate entries
- Access historical data anytime
- Clear data option for privacy protection

## Privacy

To protect sensitive information:
- Use the "Clear All Data" button in the "View Existing Data" tab
- Always clear data before sharing the application with others
- Database file (qr_data.db) is excluded from version control

## License

MIT License
