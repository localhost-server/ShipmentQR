import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_path: str = "qrcodes.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database with required tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS qr_codes (
                reference_id TEXT PRIMARY KEY,
                sender_name TEXT NOT NULL,
                sender_address TEXT NOT NULL,
                sender_city TEXT NOT NULL,
                sender_state TEXT NOT NULL,
                sender_zip TEXT NOT NULL,
                artist_name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                qr_code TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_entry(self, entry: dict) -> bool:
        """Save QR code entry to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO qr_codes (
                    reference_id, sender_name, sender_address, sender_city, sender_state, sender_zip,
                    artist_name, phone, address, qr_code, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['reference_id'],
                entry['data']['sender']['name'],
                entry['data']['sender']['address'],
                entry['data']['sender']['city'],
                entry['data']['sender']['state'],
                entry['data']['sender']['zip'],
                entry['data']['Artist Name'],
                entry['data']['Phone'],
                entry['data']['Address'],
                entry['qr_code'],
                entry['timestamp']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving to database: {e}")
            return False
        finally:
            conn.close()

    def get_all_entries(self) -> list:
        """Retrieve all QR code entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT * FROM qr_codes ORDER BY timestamp DESC')
            rows = c.fetchall()
            
            entries = []
            for row in rows:
                entry = {
                    'reference_id': row[0],
                    'data': {
                        'sender': {
                            'name': row[1],
                            'address': row[2],
                            'city': row[3],
                            'state': row[4],
                            'zip': row[5]
                        },
                        'Artist Name': row[6],
                        'Phone': row[7] or '',
                        'Address': row[8] or ''
                    },
                    'qr_code': row[9],
                    'timestamp': row[10]
                }
                entries.append(entry)
            return entries
        except Exception as e:
            print(f"Error retrieving entries: {e}")
            return []
        finally:
            conn.close()

    def clear_all(self) -> bool:
        """Clear all entries from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('DELETE FROM qr_codes')
            conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False
        finally:
            conn.close()
