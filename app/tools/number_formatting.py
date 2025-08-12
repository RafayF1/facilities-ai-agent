"""
Number formatting tool to help voice AI pronounce phone numbers and long digits correctly.
"""
import re
from typing import Dict, Any

async def format_number_for_voice(text: str) -> Dict[str, Any]:
    """
    Format phone numbers and long digit sequences for better voice pronunciation.
    
    Args:
        text: Text containing numbers that need voice formatting
        
    Returns:
        Dictionary with formatted text for better voice pronunciation
    """
    try:
        original_text = text
        formatted_text = text
        
        # Phone number patterns - focus on the problematic "03225430399" format
        phone_patterns = [
            r'\b0\d{10}\b',             # 03225430399 format (11 digits starting with 0)
            r'\+971\d{9}\b',            # +971xxxxxxxxx format
            r'\b971\d{9}\b',            # 971xxxxxxxxx format  
            r'\b\d{10,11}\b'            # Any 10-11 digit sequence (likely phone)
        ]
        
        for pattern in phone_patterns:
            matches = re.finditer(pattern, formatted_text)
            for match in reversed(list(matches)):  # Reverse to maintain positions
                number = match.group()
                # Clean the number
                clean_number = re.sub(r'[^\d]', '', number)
                
                if len(clean_number) >= 10:  # Definitely a phone number
                    # Format as spaced digits for voice: "03225430399" -> "0 3 2 2 5 4 3 0 3 9 9"
                    spaced_number = ' '.join(clean_number)
                    formatted_text = formatted_text[:match.start()] + spaced_number + formatted_text[match.end():]
                    print(f"📞 Phone formatting: {number} -> {spaced_number}")
        
        # Large standalone numbers (like customer looking up by just digits)
        large_number_patterns = [
            r'\b\d{8,}\b'  # 8+ digit standalone numbers
        ]
        
        for pattern in large_number_patterns:
            matches = re.finditer(pattern, formatted_text)
            for match in reversed(list(matches)):
                number = match.group()
                # Only format if it's not already spaced and looks like ID/phone
                if ' ' not in number and len(number) >= 8:
                    # Skip if it's a year or other common number
                    if number.startswith(('20', '19')) and len(number) == 4:
                        continue
                    
                    spaced_number = ' '.join(number)
                    formatted_text = formatted_text[:match.start()] + spaced_number + formatted_text[match.end():]
                    print(f"🔢 Large number formatting: {number} -> {spaced_number}")
        
        return {
            "status": "success",
            "original_text": original_text,
            "formatted_text": formatted_text,
            "changes_made": original_text != formatted_text,
            "formatting_applied": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error formatting numbers for voice: {str(e)}",
            "original_text": text,
            "formatted_text": text
        }

async def format_phone_number_for_display_and_voice(phone_number: str) -> Dict[str, Any]:
    """
    Format phone number for both display and voice pronunciation.
    Specifically handles the problematic "03225430399" format.
    
    Args:
        phone_number: Raw phone number
        
    Returns:
        Dictionary with formatted versions
    """
    try:
        # Clean the number
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Handle the specific UAE format "03225430399"
        if clean_number.startswith('0') and len(clean_number) == 11:
            # UAE local format: 03225430399
            display_format = f"{clean_number[:4]} {clean_number[4:7]} {clean_number[7:]}"
            voice_format = ' '.join(clean_number)  # "0 3 2 2 5 4 3 0 3 9 9"
        elif clean_number.startswith('+971'):
            country_code = '+971'
            local_number = clean_number[4:]
            display_format = f"{country_code} {local_number[:2]} {local_number[2:5]} {local_number[5:]}"
            voice_format = f"plus 9 7 1 {' '.join(local_number)}"
        elif clean_number.startswith('971'):
            country_code = '+971'
            local_number = clean_number[3:]
            display_format = f"{country_code} {local_number[:2]} {local_number[2:5]} {local_number[5:]}"
            voice_format = f"plus 9 7 1 {' '.join(local_number)}"
        else:
            # Default formatting
            display_format = phone_number
            voice_format = ' '.join(clean_number) if len(clean_number) >= 8 else phone_number
        
        return {
            "status": "success",
            "original": phone_number,
            "display_format": display_format,
            "voice_format": voice_format,
            "clean_number": clean_number
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error formatting phone number: {str(e)}",
            "original": phone_number,
            "display_format": phone_number,
            "voice_format": phone_number
        }