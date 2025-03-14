# QR Code Generator

A Streamlit web application that generates QR codes from spreadsheet data with persistent storage.

## Features

- Upload CSV or Excel files
- Automatically converts each row to QR codes
- Download or print QR codes
- Supports any spreadsheet structure
- No column name restrictions
- SQLite database for data persistence
- Unique reference IDs to avoid duplicates
- View all previously generated QR codes
- Clear data functionality for privacy protection

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

3. Upload your spreadsheet (CSV or Excel)

4. View, download, or print QR codes for each row

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
- Each row gets a unique reference ID
- Data is stored in JSON format
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
