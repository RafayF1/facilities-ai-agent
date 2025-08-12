"""
Date and time parsing tools with enhanced current date awareness.
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import calendar

async def parse_user_datetime(user_input: str, area_zone: str) -> Dict[str, Any]:
    """
    Parse flexible user date/time input into standardized format with current date awareness.
    
    Args:
        user_input: User's date/time input in any format
        area_zone: Geographic area for context
        
    Returns:
        Dictionary with parsed date/time information
    """
    try:
        user_input = user_input.strip().lower()
        
        # Current date for reference - ALWAYS use 2025!
        now = datetime.now()
        current_year = 2025  # Force current year to be 2025
        
        # Initialize result
        result = {
            "status": "success",
            "original_input": user_input,
            "parsed_date": None,
            "parsed_time": None,
            "formatted_date": None,
            "formatted_time": None,
            "suggested_times": [],
            "current_date_reference": now.strftime("%Y-%m-%d"),
            "current_year": current_year
        }
        
        # Pattern 1: YYYY-MM-DD format
        if re.match(r'\d{4}-\d{2}-\d{2}', user_input):
            try:
                parsed_date = datetime.strptime(user_input.split()[0], "%Y-%m-%d")
                # Validate that the date is not in the past
                if parsed_date.date() < now.date():
                    # If user provided a past date, suggest updating to current year
                    if parsed_date.year < current_year:
                        suggested_date = parsed_date.replace(year=current_year)
                        if suggested_date.date() >= now.date():
                            parsed_date = suggested_date
                            result["date_adjusted"] = f"Date adjusted from {parsed_date.year-1} to {current_year}"
                        else:
                            # If still in past, move to next year
                            parsed_date = parsed_date.replace(year=current_year + 1)
                            result["date_adjusted"] = f"Date moved to {current_year + 1} as {current_year} date is in the past"
                
                result["parsed_date"] = parsed_date
                result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # Pattern 2: MM/DD/YYYY or DD/MM/YYYY format
        elif re.search(r'\d{1,2}/\d{1,2}/\d{4}', user_input):
            date_part = re.search(r'\d{1,2}/\d{1,2}/\d{4}', user_input).group()
            try:
                # Try MM/DD/YYYY first
                parsed_date = datetime.strptime(date_part, "%m/%d/%Y")
                # Force to current year if year is in the past
                if parsed_date.year < current_year:
                    parsed_date = parsed_date.replace(year=current_year)
                    result["date_adjusted"] = f"Year updated to {current_year}"
                
                # Check if date is in the past
                if parsed_date.date() < now.date():
                    parsed_date = parsed_date.replace(year=current_year + 1)
                    result["date_adjusted"] = f"Date moved to {current_year + 1} as current year date is in the past"
                
                result["parsed_date"] = parsed_date
                result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Try DD/MM/YYYY
                    parsed_date = datetime.strptime(date_part, "%d/%m/%Y")
                    if parsed_date.year < current_year:
                        parsed_date = parsed_date.replace(year=current_year)
                        result["date_adjusted"] = f"Year updated to {current_year}"
                    
                    if parsed_date.date() < now.date():
                        parsed_date = parsed_date.replace(year=current_year + 1)
                        result["date_adjusted"] = f"Date moved to {current_year + 1} as current year date is in the past"
                    
                    result["parsed_date"] = parsed_date
                    result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    pass
        
        # Pattern 3: Month names (January 27th, Jan 27, etc.)
        elif re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', user_input):
            month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', user_input)
            day_match = re.search(r'(\d{1,2})', user_input)
            
            if month_match and day_match:
                month_name = month_match.group(1)
                day_num = int(day_match.group(1))
                
                # Convert month name to number
                month_mapping = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
                    'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
                    'december': 12, 'dec': 12
                }
                
                month_num = month_mapping.get(month_name)
                if month_num:
                    # Always start with current year
                    year = current_year
                    try:
                        parsed_date = datetime(year, month_num, day_num)
                        # If the date is in the past this year, move to next year
                        if parsed_date.date() < now.date():
                            parsed_date = datetime(year + 1, month_num, day_num)
                            result["date_adjusted"] = f"Date moved to {year + 1} as {year} date is in the past"
                        
                        result["parsed_date"] = parsed_date
                        result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        pass
        
        # Pattern 4: Relative dates (tomorrow, next week, etc.)
        elif "tomorrow" in user_input:
            parsed_date = now + timedelta(days=1)
            result["parsed_date"] = parsed_date
            result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
            result["relative_date"] = "tomorrow"
        
        elif "today" in user_input:
            result["parsed_date"] = now
            result["formatted_date"] = now.strftime("%Y-%m-%d")
            result["relative_date"] = "today"
        
        elif "next week" in user_input:
            # Find next Monday
            days_ahead = 7 - now.weekday()
            if days_ahead == 0:  # If today is Monday
                days_ahead = 7
            parsed_date = now + timedelta(days=days_ahead)
            result["parsed_date"] = parsed_date
            result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
            result["relative_date"] = "next week (Monday)"
        
        elif "next month" in user_input:
            # Find first day of next month
            if now.month == 12:
                parsed_date = datetime(current_year + 1, 1, 1)
            else:
                parsed_date = datetime(current_year, now.month + 1, 1)
            result["parsed_date"] = parsed_date
            result["formatted_date"] = parsed_date.strftime("%Y-%m-%d")
            result["relative_date"] = "next month"
        
        # Extract time if present
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 10:30 AM
            r'(\d{1,2})\s*(am|pm)',         # 10 AM
            r'(\d{1,2}):(\d{2})',           # 14:30 (24-hour)
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, user_input)
            if time_match:
                if 'am' in user_input or 'pm' in user_input:
                    # 12-hour format
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if len(time_match.groups()) > 2 and time_match.group(2) else 0
                    am_pm = time_match.group(-1)
                    
                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                        
                    result["parsed_time"] = f"{hour:02d}:{minute:02d}"
                    result["formatted_time"] = f"{hour:02d}:{minute:02d}"
                else:
                    # 24-hour format
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if len(time_match.groups()) > 1 and time_match.group(2) else 0
                    result["parsed_time"] = f"{hour:02d}:{minute:02d}"
                    result["formatted_time"] = f"{hour:02d}:{minute:02d}"
                break
        
        # Suggest default times if no time specified
        if not result["parsed_time"]:
            result["suggested_times"] = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        
        # If no date parsed, suggest asking for clarification
        if not result["parsed_date"]:
            result["status"] = "needs_clarification"
            result["message"] = f"I couldn't parse the date from '{user_input}'. Could you provide it in format like '{(now + timedelta(days=1)).strftime('%Y-%m-%d')}' or 'January 28th'? Today is {now.strftime('%A, %B %d, %Y')}."
        else:
            # Add helpful context about the parsed date
            result["date_context"] = {
                "day_of_week": result["parsed_date"].strftime("%A"),
                "relative_to_today": "today" if result["parsed_date"].date() == now.date() else 
                                   "tomorrow" if result["parsed_date"].date() == (now + timedelta(days=1)).date() else
                                   f"in {(result['parsed_date'].date() - now.date()).days} days"
            }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error parsing date/time: {str(e)}",
            "original_input": user_input,
            "current_date_reference": datetime.now().strftime("%Y-%m-%d")
        }

async def suggest_appointment_times(date_str: str, area_zone: str) -> Dict[str, Any]:
    """
    Suggest available appointment times for a given date and area with current date validation.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        area_zone: Geographic area/zone
        
    Returns:
        Dictionary with suggested appointment times
    """
    try:
        # Parse the date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {
                "status": "error",
                "error_message": "Invalid date format. Please use YYYY-MM-DD format."
            }
        
        # Validate that date is not in the past
        now = datetime.now()
        if target_date.date() < now.date():
            return {
                "status": "error",
                "error_message": f"Cannot schedule appointments in the past. Please choose a date on or after {now.strftime('%Y-%m-%d')}. Today is {now.strftime('%A, %B %d, %Y')}."
            }
        
        # Standard business hours for facilities management
        morning_slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"]
        afternoon_slots = ["14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
        
        # Check if it's Friday (weekend in UAE)
        if target_date.weekday() == 4:  # Friday = 4
            return {
                "status": "success",
                "date": date_str,
                "area_zone": area_zone,
                "suggested_times": ["09:00", "10:00", "11:00"],
                "note": "Friday service available with limited hours (9 AM - 12 PM)",
                "date_context": {
                    "day_of_week": "Friday (UAE weekend)",
                    "is_weekend": True
                }
            }
        
        # If it's today, filter out past times
        available_morning = morning_slots.copy()
        available_afternoon = afternoon_slots.copy()
        
        if target_date.date() == now.date():
            current_hour = now.hour
            current_minute = now.minute
            
            # Filter out past times for today
            available_morning = [time for time in morning_slots 
                               if datetime.strptime(time, "%H:%M").time() > now.time()]
            available_afternoon = [time for time in afternoon_slots 
                                 if datetime.strptime(time, "%H:%M").time() > now.time()]
        
        return {
            "status": "success",
            "date": date_str,
            "area_zone": area_zone,
            "morning_slots": available_morning,
            "afternoon_slots": available_afternoon,
            "suggested_times": available_morning + available_afternoon,
            "note": f"Business hours: 9 AM - 5 PM (excluding lunch 12-2 PM). Date: {target_date.strftime('%A, %B %d, %Y')}",
            "date_context": {
                "day_of_week": target_date.strftime("%A"),
                "is_today": target_date.date() == now.date(),
                "is_weekend": target_date.weekday() == 4,
                "days_from_today": (target_date.date() - now.date()).days
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error suggesting times: {str(e)}"
        }