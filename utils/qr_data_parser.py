class QRDataParser:
    @staticmethod
    def parse_data(data):
        """Parse the QR code data into a structured format"""
        try:
            lines = data.split('\n')
            result = {'sender': {}, 'artist': {}}
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line == 'SR:':
                    current_section = 'sender'
                    continue
                elif line == 'AT:':
                    current_section = 'artist'
                    continue

                if current_section and ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if current_section == 'sender':
                        if key == 'NM':
                            result['sender']['name'] = value
                        elif key == 'ADD':
                            result['sender']['address'] = value
                        elif key == 'CT':
                            result['sender']['city'] = value
                        elif key == 'STT':
                            result['sender']['state'] = value
                        elif key == 'CD':
                            result['sender']['zip'] = value

                    elif current_section == 'artist':
                        if key == 'NM':
                            result['artist']['name'] = value
                        elif key == 'PH':
                            result['artist']['phone'] = value
                        elif key == 'ADD':
                            result['artist']['address'] = value

            return result
        except Exception as e:
            return {'error': f"Failed to parse QR data: {str(e)}"}

    @staticmethod
    def format_result(result):
        """Format the scan result for display"""
        if not result or 'error' in result:
            return "Failed to parse QR code data"

        formatted = []
        
        # Sender Information
        if result.get('sender'):
            formatted.append("📤 Sender Information")
            sender = result['sender']
            if sender.get('name'):
                formatted.append(f"Name: {sender['name']}")
            if sender.get('address'):
                formatted.append(f"Address: {sender['address']}")
            if all(sender.get(k) for k in ['city', 'state', 'zip']):
                formatted.append(f"Location: {sender['city']}, {sender['state']} {sender['zip']}")
            formatted.append("")

        # Artist Information
        if result.get('artist'):
            formatted.append("🎨 Artist Information")
            artist = result['artist']
            if artist.get('name'):
                formatted.append(f"Name: {artist['name']}")
            if artist.get('phone'):
                formatted.append(f"Phone: {artist['phone']}")
            if artist.get('address'):
                formatted.append(f"Address: {artist['address']}")

        return "\n".join(formatted)
