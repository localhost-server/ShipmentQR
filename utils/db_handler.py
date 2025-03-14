import sqlite3
import json
from typing import Optional, List, Dict

class DatabaseHandler:
    def __init__(self, db_path: str = "qr_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create table for storing shipping data
        c.execute('''
            CREATE TABLE IF NOT EXISTS shipping_data (
                reference_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_data(self, reference_id: str, data: Dict) -> bool:
        """Save shipping data to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Check if reference_id already exists
            c.execute("SELECT reference_id FROM shipping_data WHERE reference_id = ?", (reference_id,))
            if c.fetchone() is not None:
                return False  # Reference ID already exists
            
            # Insert new record
            c.execute(
                "INSERT INTO shipping_data (reference_id, data_json) VALUES (?, ?)",
                (reference_id, json.dumps(data))
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False
        finally:
            conn.close()

    def get_data(self, reference_id: str) -> Optional[Dict]:
        """Retrieve shipping data by reference ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("SELECT data_json FROM shipping_data WHERE reference_id = ?", (reference_id,))
            result = c.fetchone()
            
            if result:
                return json.loads(result[0])
            return None
            
        except Exception as e:
            print(f"Error retrieving from database: {e}")
            return None
        finally:
            conn.close()

    def reference_id_exists(self, reference_id: str) -> bool:
        """Check if a reference ID already exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("SELECT 1 FROM shipping_data WHERE reference_id = ?", (reference_id,))
            return c.fetchone() is not None
            
        finally:
            conn.close()

    def get_all_reference_ids(self) -> List[str]:
        """Get all existing reference IDs."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("SELECT reference_id FROM shipping_data")
            return [row[0] for row in c.fetchall()]
            
        finally:
            conn.close()

    def clear_data(self) -> bool:
        """Clear all data from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("DELETE FROM shipping_data")
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False
        finally:
            conn.close()
