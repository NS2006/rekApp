import os
import subprocess
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
import tempfile
import shutil
import imageio_ffmpeg

class VideoProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.ffmpeg_path = self._get_ffmpeg()
        
    def _get_ffmpeg(self):
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            print(f"FFmpeg found: {ffmpeg_path}")
            return ffmpeg_path
        except:
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                print(f"FFmpeg found in PATH: {ffmpeg_path}")
                return ffmpeg_path
        
        print("Warning: FFmpeg not found. Audio extraction may fail.")
        return None
    
    def extract_audio(self, video_path, audio_output_path):
        # Extract audio from video
        print(f"Extracting audio from: {os.path.basename(video_path)}")
        
        if not self.ffmpeg_path:
            print("Error: FFmpeg not available")
            return False
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,          # Input file
                '-vn',                     # No video
                '-acodec', 'pcm_s16le',    # Audio codec
                '-ar', '16000',           # 16kHz sample rate
                '-ac', '1',               # Mono
                '-y',                     # Overwrite
                audio_output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr[:200]}")
                return False
            
            if os.path.exists(audio_output_path):
                size = os.path.getsize(audio_output_path)
                print(f"Audio extracted: {size:,} bytes")
                return True
            else:
                print("Audio file not created")
                return False
                
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False
    
    def transcribe_audio(self, audio_path):
        # Transcribe audio to text
        print(f"Transcribing audio...")
        
        if not os.path.exists(audio_path):
            print("Audio file not found")
            return ""
        
        try:
            # Load and prepare audio
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000
            print(f"Audio duration: {duration:.1f} seconds")
            
            if duration < 2:
                print("Audio too short")
                return ""
            
            # Normalize audio
            audio = normalize(audio)
            
            # Split into 30-second chunks
            chunks = self._split_audio(audio, chunk_size=30)
            print(f"Split into {len(chunks)} chunks")
            
            # Transcribe each chunk
            full_text = []
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}...")
                text = self._transcribe_chunk(chunk)
                if text:
                    full_text.append(text)
            
            # Combine all text
            if full_text:
                result = " ".join(full_text)
                print(f"Transcription complete: {len(result):,} characters")
                return result
            else:
                print("No text transcribed")
                return ""
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
    
    def _split_audio(self, audio_segment, chunk_size=30):
        # Split audio into chunks
        chunks = []
        chunk_size_ms = chunk_size * 1000
        
        for i in range(0, len(audio_segment), chunk_size_ms):
            chunk = audio_segment[i:i + chunk_size_ms]
            if len(chunk) > 1000:  # At least 1 second
                chunks.append(chunk)
        
        return chunks
    
    def _transcribe_chunk(self, audio_chunk):
        # Transcribe a single chunk
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            audio_chunk.export(tmp_path, format="wav")
            
            with sr.AudioFile(tmp_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
            
            os.unlink(tmp_path)
            
            return text
            
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Google API error: {e}")
            return ""
        except Exception as e:
            print(f"Chunk transcription error: {e}")
            return ""
    
    def get_video_info(self, video_path):
        info = {
            'exists': os.path.exists(video_path),
            'size': 0,
            'size_mb': 0
        }
        
        if info['exists']:
            info['size'] = os.path.getsize(video_path)
            info['size_mb'] = info['size'] / (1024 * 1024)
        
        return info