import json
import streamlit as st

def load_settings():
    """Load settings from session state or file"""
    # First check if settings exist in session state
    if 'settings' in st.session_state:
        return st.session_state.settings
    
    # Try to load from file
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            st.session_state.settings = settings
            return settings
    except:
        # Return default settings
        default_settings = {
            "sender": {
                "name": "Default Name",
                "address": "Default Address",
                "city": "Default City",
                "state": "Default State",
                "zip": "00000"
            }
        }
        st.session_state.settings = default_settings
        return default_settings

def save_settings(settings):
    """Save settings to session state and file"""
    # Update session state
    st.session_state.settings = settings
    
    # Try to save to file
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
    except:
        pass  # Ignore file write errors in cloud environment

def validate_sender_settings(settings):
    """Validate that all required sender settings are present"""
    if not settings or 'sender' not in settings:
        return False
        
    required_fields = ['name', 'address', 'city', 'state', 'zip']
    return all(field in settings['sender'] and settings['sender'][field] for field in required_fields)
