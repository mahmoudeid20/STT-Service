"""
Audio Processing Module
Handles audio transcription using multiple engines
"""
import os
import logging
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import numpy as np
import wave
import struct

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_formats = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        
    def preprocess(self, audio_path):
        """
        Preprocess audio file
        - Convert to WAV if needed
        - Normalize volume
        - Remove silence
        """
        try:
            # Get file extension
            file_ext = os.path.splitext(audio_path)[1].lower()
            
            # Load audio
            if file_ext == '.wav':
                audio = AudioSegment.from_wav(audio_path)
            elif file_ext == '.mp3':
                audio = AudioSegment.from_mp3(audio_path)
            elif file_ext == '.flac':
                audio = AudioSegment.from_file(audio_path, 'flac')
            elif file_ext == '.ogg':
                audio = AudioSegment.from_ogg(audio_path)
            elif file_ext == '.m4a':
                audio = AudioSegment.from_file(audio_path, 'm4a')
            else:
                audio = AudioSegment.from_file(audio_path)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Set sample rate to 16kHz (optimal for speech recognition)
            audio = audio.set_frame_rate(16000)
            
            # Normalize audio
            audio = self.normalize_audio(audio)
            
            # Remove silence from beginning and end
            audio = self.remove_silence(audio)
            
            # Export as WAV
            output_path = audio_path.rsplit('.', 1)[0] + '_processed.wav'
            audio.export(output_path, format='wav')
            
            logger.info(f"Audio preprocessed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}")
            return audio_path  # Return original if preprocessing fails
    
    def normalize_audio(self, audio):
        """Normalize audio volume"""
        # Target loudness
        target_dBFS = -20.0
        change_in_dBFS = target_dBFS - audio.dBFS
        return audio.apply_gain(change_in_dBFS)
    
    def remove_silence(self, audio, silence_thresh=-40):
        """Remove silence from audio"""
        chunks = split_on_silence(
            audio,
            min_silence_len=500,  # milliseconds
            silence_thresh=silence_thresh,
            keep_silence=200
        )
        
        if not chunks:
            return audio
        
        # Combine chunks
        combined = AudioSegment.empty()
        for chunk in chunks:
            combined += chunk
        
        return combined
    
    def transcribe(self, audio_path, language='en-US'):
        """
        Transcribe audio using Google Speech Recognition
        Falls back to Sphinx if Google fails
        """
        try:
            # Use preprocessed audio
            if not audio_path.endswith('_processed.wav'):
                audio_path = self.preprocess(audio_path)
            
            with sr.AudioFile(audio_path) as source:
                # Record the audio
                audio_data = self.recognizer.record(source)
                
                # Try Google Speech Recognition first
                try:
                    text = self.recognizer.recognize_google(
                        audio_data,
                        language=language
                    )
                    logger.info("Transcription completed using Google Speech Recognition")
                    return text
                    
                except sr.UnknownValueError:
                    logger.warning("Google Speech Recognition could not understand audio")
                    # Try Sphinx as fallback
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data)
                        logger.info("Transcription completed using Sphinx")
                        return text
                    except:
                        return "[Could not transcribe audio]"
                        
                except sr.RequestError as e:
                    logger.error(f"Google Speech Recognition error: {str(e)}")
                    # Try Sphinx as fallback
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data)
                        logger.info("Transcription completed using Sphinx (fallback)")
                        return text
                    except:
                        return "[Transcription service unavailable]"
                        
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return f"[Error: {str(e)}]"
    
    def transcribe_with_timestamps(self, audio_path, language='en-US'):
        """
        Transcribe audio with word-level timestamps
        """
        try:
            # Split audio into chunks
            audio = AudioSegment.from_wav(audio_path)
            chunks = split_on_silence(
                audio,
                min_silence_len=500,
                silence_thresh=-40,
                keep_silence=200
            )
            
            results = []
            current_time = 0
            
            for i, chunk in enumerate(chunks):
                # Export chunk
                chunk_path = f"/tmp/chunk_{i}.wav"
                chunk.export(chunk_path, format="wav")
                
                # Transcribe chunk
                with sr.AudioFile(chunk_path) as source:
                    audio_data = self.recognizer.record(source)
                    try:
                        text = self.recognizer.recognize_google(audio_data, language=language)
                        results.append({
                            'text': text,
                            'start_time': current_time / 1000,  # Convert to seconds
                            'end_time': (current_time + len(chunk)) / 1000,
                            'duration': len(chunk) / 1000
                        })
                    except:
                        pass
                
                current_time += len(chunk)
                os.remove(chunk_path)
            
            return results
            
        except Exception as e:
            logger.error(f"Timestamp transcription error: {str(e)}")
            return []
    
    def calculate_confidence(self, audio_path):
        """
        Calculate transcription confidence score
        Based on audio quality metrics
        """
        try:
            # Load audio
            with wave.open(audio_path, 'rb') as wav_file:
                # Get audio parameters
                sample_rate = wav_file.getframerate()
                num_frames = wav_file.getnframes()
                
                # Read audio data
                audio_data = wav_file.readframes(num_frames)
                
                # Convert to numpy array
                if wav_file.getsampwidth() == 2:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                else:
                    audio_array = np.frombuffer(audio_data, dtype=np.int8)
            
            # Calculate metrics
            # 1. Signal-to-noise ratio approximation
            signal_power = np.mean(audio_array ** 2)
            noise_estimate = np.var(audio_array[audio_array < np.percentile(audio_array, 10)])
            snr = 10 * np.log10(signal_power / (noise_estimate + 1e-10))
            
            # 2. Normalize confidence (0-1 scale)
            confidence = min(max((snr + 10) / 50, 0), 1)
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5  # Default medium confidence
    
    def get_duration(self, audio_path):
        """Get audio duration in seconds"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return round(len(audio) / 1000.0, 2)
        except Exception as e:
            logger.error(f"Error getting duration: {str(e)}")
            return 0.0
    
    def extract_features(self, audio_path):
        """
        Extract audio features for analysis
        """
        try:
            audio = AudioSegment.from_wav(audio_path)
            
            features = {
                'duration': len(audio) / 1000.0,
                'channels': audio.channels,
                'sample_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'frame_count': audio.frame_count(),
                'loudness': audio.dBFS,
                'max_dBFS': audio.max_dBFS
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return {}