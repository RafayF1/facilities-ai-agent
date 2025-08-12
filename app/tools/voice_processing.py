"""
Voice input processing tools for better phone number recognition in ADK.
Add this file as: app/tools/voice_processing.py
"""
import re
from typing import Dict, Any, List

class VoiceInputProcessor:
    """Enhanced processor for voice input, especially phone numbers."""
    
    def __init__(self):
        # Common phone number variations from voice input
        self.phone_patterns = {
            # UAE phone patterns
            'uae_landline': r'\b0\d{1}\s*\d{3}\s*\d{3}\s*\d{3}\b',  # 03 225 430 399
            'uae_mobile': r'\b05\d\s*\d{3}\s*\d{4}\b',              # 050 123 4567
            'international': r'\+971\s*\d{1,2}\s*\d{3}\s*\d{4}\b',  # +971 3 225 4303
            
            # Common voice misrecognitions
            'spaced_digits': r'\b\d(\s+\d){7,10}\b',                # "0 3 2 2 5 4 3 0 3 9 9"
            'oh_zero': r'\boh\s+(\d+)\b',                           # "oh three two..."
            'zero_prefix': r'\bzero\s+(\d+)\b',                     # "zero three two..."
        }
        
        # Text-to-number mappings for voice
        self.word_to_digit = {
            'zero': '0', 'oh': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'double': '', 'triple': ''  # Handle "double five" = "55"
        }
        
        # Common voice recognition mistakes
        self.voice_corrections = {
            r'\boh\b': '0',
            r'\bzero\b': '0', 
            r'\bdouble\s+(\w+)': r'\1\1',
            r'\btriple\s+(\w+)': r'\1\1\1',
            r'\bphone\s+number\s+is\b': '',
            r'\bmy\s+number\s+is\b': '',
            r'\bits\b': '',
            r'\bthe\s+number\s+is\b': '',
            r'\bcall\s+me\s+at\b': '',
            r'\breach\s+me\s+at\b': '',
        }
    
    def process_voice_text(self, text: str) -> str:
        """
        Process voice-recognized text to improve phone number recognition.
        
        Args:
            text: Raw text from voice recognition
            
        Returns:
            Processed text with improved phone number formatting
        """
        if not text:
            return text
            
        processed_text = text.lower()
        
        # Handle common voice recognition issues
        processed_text = self._fix_common_voice_issues(processed_text)
        processed_text = self._normalize_phone_numbers(processed_text)
        processed_text = self._handle_spelled_numbers(processed_text)
        
        return processed_text
    
    def _fix_common_voice_issues(self, text: str) -> str:
        """Fix common voice recognition mistakes."""
        for pattern, replacement in self.voice_corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text.strip()
    
    def _normalize_phone_numbers(self, text: str) -> str:
        """Normalize phone number formats."""
        # Handle spaced digits: "0 3 2 2 5 4 3 0 3 9 9"
        spaced_pattern = r'\b(\d)(\s+\d){7,10}\b'
        matches = re.finditer(spaced_pattern, text)
        
        for match in reversed(list(matches)):
            original = match.group()
            # Remove spaces to create continuous number
            normalized = re.sub(r'\s+', '', original)
            text = text[:match.start()] + normalized + text[match.end():]
        
        return text
    
    def _handle_spelled_numbers(self, text: str) -> str:
        """Convert spelled-out numbers to digits."""
        # Find sequences of spelled numbers
        number_words = r'\b(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)\b'
        
        # Find sequences of number words
        pattern = f'({number_words}(?:\\s+{number_words})*)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in reversed(list(matches)):
            words = match.group().split()
            digits = ''.join(self.word_to_digit.get(word.lower(), word) for word in words)
            
            # Only replace if we got a reasonable phone number length
            if len(digits) >= 7:
                text = text[:match.start()] + digits + text[match.end():]
        
        return text
    
    def extract_phone_candidates(self, text: str) -> List[str]:
        """Extract potential phone numbers from processed text."""
        candidates = []
        
        # All phone number patterns
        patterns = [
            r'\b0\d{10}\b',           # UAE landline: 03225430399
            r'\b05\d{8}\b',           # UAE mobile: 0501234567
            r'\+971\d{8,9}\b',        # International: +97132254303
            r'\b971\d{8,9}\b',        # International without +: 97132254303
            r'\b\d{8,11}\b',          # Any 8-11 digit sequence
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            candidates.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def detect_phone_context(self, text: str) -> bool:
        """Detect if the text contains phone number context."""
        phone_indicators = [
            'phone', 'number', 'contact', 'reach', 'call',
            'mobile', 'landline', 'telephone', 'dial'
        ]
        
        return any(indicator in text.lower() for indicator in phone_indicators)

# ADK Tool Functions
async def process_voice_input_for_phone(voice_text: str) -> Dict[str, Any]:
    """
    Process voice input text to improve phone number recognition.
    
    Args:
        voice_text: Raw text from voice recognition
        
    Returns:
        Dictionary with processed text and extracted phone numbers
    """
    try:
        processor = VoiceInputProcessor()
        
        # Process the voice text
        processed_text = processor.process_voice_text(voice_text)
        
        # Extract phone number candidates
        phone_candidates = processor.extract_phone_candidates(processed_text)
        
        # Determine if this looks like a phone number inquiry
        is_phone_inquiry = processor.detect_phone_context(voice_text)
        
        return {
            "status": "success",
            "original_text": voice_text,
            "processed_text": processed_text,
            "phone_candidates": phone_candidates,
            "is_phone_inquiry": is_phone_inquiry,
            "best_phone_candidate": phone_candidates[0] if phone_candidates else None,
            "processing_applied": voice_text.lower() != processed_text,
            "candidates_count": len(phone_candidates)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error processing voice input: {str(e)}",
            "original_text": voice_text,
            "processed_text": voice_text,
            "phone_candidates": [],
            "is_phone_inquiry": False
        }

async def enhance_phone_for_voice_response(phone_number: str) -> Dict[str, Any]:
    """
    Format phone number for clear voice response.
    
    Args:
        phone_number: Phone number to format
        
    Returns:
        Dictionary with voice-formatted phone number
    """
    try:
        # Clean the number
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Format for voice confirmation - spaced digits
        if clean_number.startswith('0') and len(clean_number) == 11:
            # UAE format: "03225430399" -> "0 3 2 2 5 4 3 0 3 9 9"
            voice_format = ' '.join(clean_number)
            display_format = f"{clean_number[:4]} {clean_number[4:7]} {clean_number[7:]}"
        elif clean_number.startswith('+971'):
            # International format
            country_code = '+971'
            local_number = clean_number[4:]
            voice_format = f"plus 9 7 1 {' '.join(local_number)}"
            display_format = f"{country_code} {local_number[:2]} {local_number[2:5]} {local_number[5:]}"
        else:
            # Default: space all digits
            voice_format = ' '.join(clean_number)
            display_format = phone_number
        
        return {
            "status": "success",
            "original": phone_number,
            "voice_format": voice_format,
            "display_format": display_format,
            "clean_number": clean_number
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error formatting phone for voice: {str(e)}",
            "original": phone_number,
            "voice_format": phone_number,
            "display_format": phone_number
        }

async def validate_extracted_phone(phone_candidate: str) -> Dict[str, Any]:
    """
    Validate if extracted phone number looks legitimate.
    
    Args:
        phone_candidate: Extracted phone number candidate
        
    Returns:
        Dictionary with validation results
    """
    try:
        clean_phone = re.sub(r'[^\d]', '', phone_candidate)
        
        # UAE phone number validation
        is_valid = False
        phone_type = "unknown"
        
        if len(clean_phone) == 11 and clean_phone.startswith('0'):
            # UAE landline (e.g., 03225430399)
            if clean_phone.startswith(('02', '03', '04', '06', '07', '09')):
                is_valid = True
                phone_type = "uae_landline"
        elif len(clean_phone) == 10 and clean_phone.startswith('05'):
            # UAE mobile (e.g., 0501234567)
            is_valid = True
            phone_type = "uae_mobile"
        elif len(clean_phone) == 12 and clean_phone.startswith('971'):
            # International UAE (e.g., 971501234567)
            is_valid = True
            phone_type = "uae_international"
        elif len(clean_phone) >= 8:
            # Generic phone number
            is_valid = True
            phone_type = "generic"
        
        return {
            "status": "success",
            "phone_candidate": phone_candidate,
            "clean_phone": clean_phone,
            "is_valid": is_valid,
            "phone_type": phone_type,
            "length": len(clean_phone)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error validating phone: {str(e)}",
            "is_valid": False
        }