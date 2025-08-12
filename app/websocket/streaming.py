"""
WebSocket streaming handlers for real-time agent communication with voice phone processing.
Updated version of your existing streaming.py file.
"""
import asyncio
import json
import base64
import uuid
import re
from typing import Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from google.genai.types import Part, Content, Blob
from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig

from app.config import settings
from app.agents.facilities_agent import root_agent
from app.tools.number_formatting import format_number_for_voice

class VoicePhoneProcessor:
    """Simple voice phone processor for integration with existing streaming."""
    
    def __init__(self):
        # Common voice recognition fixes
        self.voice_corrections = {
            r'\boh\b': '0',
            r'\bzero\b': '0',
            r'\bdouble\s+(\w+)': r'\1\1',
            r'\btriple\s+(\w+)': r'\1\1\1',
            r'\bphone\s+number\s+is\b': '',
            r'\bmy\s+number\s+is\b': '',
            r'\bcall\s+me\s+at\b': '',
            r'\bits\b': '',
        }
    
    def process_voice_text(self, text: str) -> str:
        """Process voice text to improve phone number recognition."""
        if not text:
            return text
            
        processed = text.lower()
        
        # Apply voice corrections
        for pattern, replacement in self.voice_corrections.items():
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
        
        # Handle spaced digits: "0 3 2 2 5..." -> "03225..."
        spaced_pattern = r'\b(\d)(\s+\d){7,10}\b'
        matches = re.finditer(spaced_pattern, processed)
        
        for match in reversed(list(matches)):
            original = match.group()
            normalized = re.sub(r'\s+', '', original)
            processed = processed[:match.start()] + normalized + processed[match.end():]
        
        return processed.strip()
    
    def extract_phone_candidates(self, text: str) -> list:
        """Extract potential phone numbers."""
        patterns = [
            r'\b0\d{10}\b',           # UAE landline: 03225430399
            r'\b05\d{8}\b',           # UAE mobile: 0501234567
            r'\+971\d{8,9}\b',        # International
            r'\b\d{8,11}\b',          # Any 8-11 digit sequence
        ]
        
        candidates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            candidates.extend(matches)
        
        return list(set(candidates))  # Remove duplicates
    
    def has_phone_context(self, text: str) -> bool:
        """Check if text contains phone number context."""
        indicators = ['phone', 'number', 'contact', 'call', 'mobile', 'reach']
        return any(indicator in text.lower() for indicator in indicators)

class StreamingManager:
    """Enhanced streaming manager with voice phone processing."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.voice_processor = VoicePhoneProcessor()
    
    async def start_agent_session(self, session_id: str, is_audio: bool = False) -> tuple:
        """
        Initialize a new agent session for streaming.
        """
        try:
            # Create ADK Runner
            runner = InMemoryRunner(
                app_name=settings.app_name,
                agent=root_agent,
            )
            
            # Create Session
            session = await runner.session_service.create_session(
                app_name=settings.app_name,
                user_id=session_id,
            )
            
            # Configure response modality based on audio mode
            modality = "AUDIO" if is_audio else "TEXT"
            run_config = RunConfig(response_modalities=[modality])
            
            # Create LiveRequestQueue for bidirectional communication
            live_request_queue = LiveRequestQueue()
            
            # Start agent live session
            live_events = runner.run_live(
                session=session,
                live_request_queue=live_request_queue,
                run_config=run_config,
            )
            
            return live_events, live_request_queue
            
        except Exception as e:
            print(f"Error starting agent session: {e}")
            raise
    
    async def handle_websocket_connection(
        self, 
        websocket: WebSocket, 
        session_id: str, 
        is_audio: str = "false"
    ):
        """
        Handle WebSocket connection for agent streaming.
        """
        await websocket.accept()
        
        # Convert is_audio string to boolean
        audio_mode = is_audio.lower() == "true"
        
        print(f"📞 Client #{session_id} connected, audio mode: {audio_mode}")
        
        try:
            # Start agent session
            live_events, live_request_queue = await self.start_agent_session(
                session_id, audio_mode
            )
            
            # Store session data
            self.active_sessions[session_id] = {
                'websocket': websocket,
                'live_request_queue': live_request_queue,
                'audio_mode': audio_mode,
                'connected_at': datetime.now(),
                'phone_context': {}
            }
            
            # Create tasks for bidirectional communication
            agent_to_client_task = asyncio.create_task(
                self._agent_to_client_messaging(websocket, live_events, audio_mode)
            )
            client_to_agent_task = asyncio.create_task(
                self._client_to_agent_messaging(websocket, live_request_queue, session_id)
            )
            
            # Wait for either task to complete or connection to close
            tasks = [agent_to_client_task, client_to_agent_task]
            await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            
        except WebSocketDisconnect:
            print(f"📞 Client #{session_id} disconnected normally")
        except Exception as e:
            print(f"❌ Error in WebSocket connection for client #{session_id}: {e}")
        finally:
            # Cleanup session
            await self._cleanup_session(session_id, live_request_queue)
    
    async def _agent_to_client_messaging(self, websocket: WebSocket, live_events, audio_mode: bool = False):
        """
        Handle streaming from agent to client with enhanced voice formatting.
        """
        try:
            async for event in live_events:
                # Handle turn completion or interruption
                if event.turn_complete or event.interrupted:
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: {message}")
                    continue
                
                # Read the Content and its first Part
                part: Part = (
                    event.content and 
                    event.content.parts and 
                    event.content.parts[0]
                )
                
                if not part:
                    continue
                
                # If it's audio, send Base64 encoded audio data
                is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        message = {
                            "mime_type": "audio/pcm",
                            "data": base64.b64encode(audio_data).decode("ascii")
                        }
                        await websocket.send_text(json.dumps(message))
                        print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")
                        continue
                
                # If it's text and a partial text, send it
                if part.text and event.partial:
                    # Format numbers for voice if in audio mode
                    text_content = part.text
                    if audio_mode:
                        try:
                            format_result = await format_number_for_voice(text_content)
                            if format_result.get("changes_made"):
                                text_content = format_result["formatted_text"]
                                print(f"📢 Voice formatting applied: {part.text} -> {text_content}")
                            
                            # Additional phone number enhancement for voice
                            text_content = self._enhance_phone_confirmations(text_content)
                            
                        except Exception as e:
                            print(f"⚠️ Voice formatting failed: {e}")
                            # Continue with original text
                    
                    message = {
                        "mime_type": "text/plain",
                        "data": text_content
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: text/plain: {text_content[:100]}...")
                    
        except WebSocketDisconnect:
            print("📞 WebSocket disconnected during agent to client messaging")
        except Exception as e:
            print(f"❌ Error in agent to client messaging: {e}")
    
    def _enhance_phone_confirmations(self, text: str) -> str:
        """Enhance phone number confirmations for better voice pronunciation."""
        # Look for phone numbers in confirmations and space them for voice
        phone_patterns = [
            r'\b(\d{11})\b',  # 11-digit numbers like 03225430399
            r'\b(\d{10})\b',  # 10-digit numbers
        ]
        
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in reversed(list(matches)):
                phone_num = match.group(1)
                # Convert to spaced format for voice: "03225430399" -> "0 3 2 2 5 4 3 0 3 9 9"
                spaced_phone = ' '.join(phone_num)
                text = text[:match.start()] + spaced_phone + text[match.end():]
        
        return text
    
    async def _client_to_agent_messaging(self, websocket: WebSocket, live_request_queue, session_id: str):
        """
        Handle messaging from client to agent with voice phone processing.
        """
        try:
            while True:
                # Decode JSON message
                message_json = await websocket.receive_text()
                message = json.loads(message_json)
                mime_type = message["mime_type"]
                data = message["data"]
                
                # Send the message to the agent
                if mime_type == "text/plain":
                    original_text = data
                    enhanced_text = original_text
                    
                    # Enhanced voice processing for phone numbers if in audio mode
                    if session_id in self.active_sessions and self.active_sessions[session_id]['audio_mode']:
                        enhanced_text = await self._process_voice_for_phones(original_text, session_id)
                    
                    content = Content(role="user", parts=[Part.from_text(text=enhanced_text)])
                    live_request_queue.send_content(content=content)
                    
                    if enhanced_text != original_text:
                        print(f"🎙️ [CLIENT TO AGENT] Enhanced: '{original_text}' -> '{enhanced_text}'")
                    else:
                        print(f"[CLIENT TO AGENT]: {original_text}")
                
                elif mime_type == "audio/pcm":
                    decoded_data = base64.b64decode(data)
                    live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
                    print(f"[CLIENT TO AGENT]: audio/pcm: {len(decoded_data)} bytes")
                else:
                    print(f"❌ Mime type not supported: {mime_type}")
                    
        except WebSocketDisconnect:
            print("📞 WebSocket disconnected during client to agent messaging")
        except Exception as e:
            print(f"❌ Error in client to agent messaging: {e}")
    
    async def _process_voice_for_phones(self, text: str, session_id: str) -> str:
        """Process voice text to improve phone number recognition."""
        try:
            # Process the text
            processed_text = self.voice_processor.process_voice_text(text)
            
            # Extract phone candidates
            phone_candidates = self.voice_processor.extract_phone_candidates(processed_text)
            
            # Check for phone context
            has_phone_context = self.voice_processor.has_phone_context(text)
            
            # Store context if phone numbers found
            if phone_candidates or has_phone_context:
                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['phone_context'] = {
                        'original_text': text,
                        'processed_text': processed_text,
                        'candidates': phone_candidates,
                        'has_context': has_phone_context
                    }
                
                print(f"📞 Phone processing - Original: '{text}'")
                print(f"📞 Phone processing - Processed: '{processed_text}'")
                print(f"📞 Phone candidates: {phone_candidates}")
                
                # If we found a clear phone candidate, enhance the text
                if len(phone_candidates) == 1 and len(phone_candidates[0]) >= 8:
                    best_phone = phone_candidates[0]
                    enhanced_text = f"My phone number is {best_phone}"
                    print(f"📞 Enhanced for agent: '{enhanced_text}'")
                    return enhanced_text
            
            return processed_text
            
        except Exception as e:
            print(f"❌ Error processing voice for phones: {e}")
            return text
    
    async def _cleanup_session(self, session_id: str, live_request_queue):
        """Clean up session resources."""
        try:
            # Close the live request queue
            if live_request_queue:
                live_request_queue.close()
            
            # Remove session from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            print(f"🧹 Client #{session_id} session cleaned up")
            
        except Exception as e:
            print(f"❌ Error cleaning up session {session_id}: {e}")
    
    def get_active_sessions_count(self) -> int:
        """Get the number of active streaming sessions."""
        return len(self.active_sessions)
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a specific session."""
        session = self.active_sessions.get(session_id)
        if session:
            return {
                'session_id': session_id,
                'audio_mode': session['audio_mode'],
                'connected_at': session['connected_at'].isoformat(),
                'duration_seconds': (
                    datetime.now() - session['connected_at']
                ).total_seconds(),
                'phone_context': session.get('phone_context', {})
            }
        return None

# Global streaming manager instance - this is what your main.py is trying to import
streaming_manager = StreamingManager()