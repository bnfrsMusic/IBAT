import speech_recognition as sr
import whisper
import numpy as np
import tempfile
import wave
import os
import io
from typing import Optional
from pathlib import Path
import scipy.signal

class WhisperVoiceActivityDetector:
    def __init__(self, recognizer: sr.Recognizer, microphone: sr.Microphone, 
                 whisper_model: str = "tiny", energy_threshold: int = 300, 
                 dynamic_threshold: bool = True, pause_threshold: float = 0.8, 
                 phrase_threshold: float = 0.3, non_speaking_duration: float = 0.5):
        
        self.recognizer = recognizer
        self.microphone = microphone
        self.energy_threshold = energy_threshold
        self.dynamic_threshold = dynamic_threshold
        self.pause_threshold = pause_threshold
        self.phrase_threshold = phrase_threshold
        self.non_speaking_duration = non_speaking_duration
        
        # Configure recognizer
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.phrase_threshold = phrase_threshold
        self.recognizer.non_speaking_duration = non_speaking_duration
        
        # Init Whisper
        self.whisper_model_name = whisper_model
        print(f"Loading Whisper model: {whisper_model}")
        try:
            self.whisper_model = whisper.load_model(whisper_model)
            print(f"Whisper model loaded successfully")
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            raise
        
        self.is_listening = False
        self.listen_thread = None
    
    def calibrate(self):
        
        print("Calibrating microphone for ambient noise...")
        print("Please remain quiet for a moment...")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        
        print(f"Calibration complete. Energy threshold: {self.recognizer.energy_threshold}")
    
    def transcribe_audio_data(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcribe audio data directly without creating temporary files."""
        try:
            # raw audio data
            raw_data = audio_data.get_raw_data()
            
            # Convert to numpy array
            if audio_data.sample_width == 2:  # 16-bit
                np_audio = np.frombuffer(raw_data, dtype=np.int16)
            elif audio_data.sample_width == 4:  # 32-bit
                np_audio = np.frombuffer(raw_data, dtype=np.int32)
            else:
                print(f"Unsupported sample width: {audio_data.sample_width}")
                return None
            
            # convert to float32 and normalize
            np_audio = np_audio.astype(np.float32)
            if np.abs(np_audio).max() > 0:
                np_audio = np_audio / np.abs(np_audio).max()
            
            # Resample to 16kHz if needed
            if audio_data.sample_rate != 16000:

                num_samples = int(len(np_audio) * 16000 / audio_data.sample_rate)
                np_audio = scipy.signal.resample(np_audio, num_samples)
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                np_audio,
                language='en', 
                task='transcribe',
                fp16=False,  
                verbose=False,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            print(f"[DEBUG] Whisper raw result (direct): {result}")
            text = result.get('text', '').strip()
            
            # Filter out very short or nonsensical transcriptions
            if len(text) < 2:
                return None
            
            # Filter out common Whisper hallucinations/artifacts
            whisper_artifacts = [
                'thank you', 'thanks for watching', 'subscribe', 'like and subscribe',
                'you', 'the', 'a', 'an', 'and', 'or', 'but', 'so', 'if', 'then',
                'uh', 'um', 'ah', 'eh', 'oh', 'wow', 'yeah', 'yes', 'no', 'okay', 'ok',
                '.', ',', '!', '?', ' ', ''
            ]
            
            if text.lower().strip() in whisper_artifacts:
                return None
            
            # Additional filtering for very short common words
            words = text.split()
            if len(words) == 1 and words[0].lower() in whisper_artifacts:
                return None
            
            return text
            
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return None
    
    def transcribe_with_whisper_fallback(self, audio_data: sr.AudioData) -> Optional[str]:
        """Fallback method using temporary WAV files with proper Windows path handling."""
        temp_file = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', mode='wb') as f:
                temp_file = f.name
                
                #WAV header and data
                with wave.open(f, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(audio_data.sample_width)
                    wav_file.setframerate(audio_data.sample_rate)
                    wav_file.writeframes(audio_data.get_wav_data())
            
            if not os.path.exists(temp_file):
                print(f"Temporary file was not created: {temp_file}")
                return None
            
            #Transcribe
            result = self.whisper_model.transcribe(
                temp_file,
                language='en',
                task='transcribe',
                fp16=False,
                verbose=False,
                beam_size=5,
                best_of=5,
                temperature=0.0
            )
            print(f"[DEBUG] Whisper raw result (fallback): {result}")
            # Extract and filter text
            text = result.get('text', '').strip()
            
            if len(text) < 2:
                return None
            
            # Filter artifacts
            whisper_artifacts = [
                'thank you', 'thanks for watching', 'subscribe', 'like and subscribe',
                'you', 'the', 'a', 'an', 'and', 'or', 'but', 'so', 'if', 'then',
                'uh', 'um', 'ah', 'eh', 'oh', 'wow', 'yeah', 'yes', 'no', 'okay', 'ok'
            ]
            
            if text.lower().strip() in whisper_artifacts:
                return None
            
            return text
            
        except Exception as e:
            print(f"Whisper file transcription error: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as cleanup_error:
                    print(f"Could not clean up temp file: {cleanup_error}")
    
    def listen_for_speech_vad(self, timeout: float = 10.0) -> Optional[str]:
        """Listen for speech with voice activity detection using Whisper."""
        try:
            print(f"\nWaiting for speech... (timeout: {timeout}s)")
            print("Start speaking when ready...")
            
            with self.microphone as source:
                # Wait for speech to start, then capture until silence
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=None  # No limit on phrase length
                )
            
            print("Processing speech with Whisper...")
            
            #direct transcription first
            # text = self.transcribe_audio_data(audio)
            text = None
            # try file-based approach
            if text is None:
                print("Trying fallback transcription method...")
                text = self.transcribe_with_whisper_fallback(audio)
            
            if text:
                print("TEXT: ", text)
                return text
            else:
                print("Could not understand the speech or text too short")
                return None
            
        except sr.WaitTimeoutError:
            print(f"No speech detected within {timeout} seconds")
            return None
        except Exception as e:
            print(f"Speech recognition error: {e}")
            return None
    
    def get_audio_level(self) -> float:
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                return self.recognizer.energy_threshold
        except:
            return 0