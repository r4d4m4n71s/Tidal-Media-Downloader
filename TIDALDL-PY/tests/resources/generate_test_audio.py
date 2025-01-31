import os
import numpy as np
from scipy.io import wavfile
import subprocess
import time

def generate_sine_wave(duration=3, sample_rate=44100, frequency=440):
    """Generate a sine wave audio sample."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    samples = np.sin(2 * np.pi * frequency * t)
    # Normalize to 16-bit range
    samples = (samples * 32767).astype(np.int16)
    return samples, sample_rate

def safe_remove(path):
    """Safely remove a file with retries."""
    if not os.path.exists(path):
        return
    
    for _ in range(3):  # Try 3 times
        try:
            os.remove(path)
            break
        except PermissionError:
            time.sleep(1)  # Wait a bit and try again
        except Exception as e:
            print(f"Warning: Could not remove {path}: {e}")
            break

def create_test_files():
    """Create test audio files with and without metadata."""
    # Paths
    resources_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(resources_dir, 'audio')
    cover_art = os.path.join(resources_dir, 'cover.jpg')

    # Clean up existing files
    if os.path.exists(audio_dir):
        for filename in os.listdir(audio_dir):
            safe_remove(os.path.join(audio_dir, filename))
    else:
        os.makedirs(audio_dir)

    # Generate base audio
    samples, sample_rate = generate_sine_wave()
    base_wav = os.path.join(audio_dir, 'base.wav')
    wavfile.write(base_wav, sample_rate, samples)

    # Metadata to add
    metadata = {
        'title': 'Test Song',
        'artist': 'Test Artist',
        'lyrics': 'Test lyrics;Second line'  # Using semicolon as separator
    }

    # Format configurations
    formats = {
        'wav': {
            'ext': 'wav',
            'codec': 'pcm_s16le',
            'extra': [],
            'supports_cover': False
        },
        'flac': {
            'ext': 'flac',
            'codec': 'flac',
            'extra': ['-compression_level', '8'],
            'supports_cover': True
        },
        'mp3': {
            'ext': 'mp3',
            'codec': 'libmp3lame',
            'extra': ['-b:a', '320k', '-id3v2_version', '3'],
            'supports_cover': True
        },
        'm4a': {
            'ext': 'm4a',
            'codec': 'aac',
            'extra': ['-b:a', '256k', '-f', 'mp4'],
            'supports_cover': True
        }
    }

    # Create two versions of each format: with and without metadata
    for fmt_name, fmt_config in formats.items():
        # Version with metadata and cover art
        output_file = os.path.join(audio_dir, f'test.{fmt_config["ext"]}')
        output_file_notags = os.path.join(audio_dir, f'test_notags.{fmt_config["ext"]}')
        
        for include_metadata in [True, False]:
            current_output = output_file if include_metadata else output_file_notags
            
            # Remove existing file if any
            safe_remove(current_output)
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-i', base_wav  # Audio input
            ]
            
            # Add cover art input and mapping for supported formats
            if include_metadata and fmt_config['supports_cover'] and os.path.exists(cover_art):
                cmd.extend([
                    '-i', cover_art,
                    '-map', '0:a',  # Map audio from first input
                    '-map', '1:v',  # Map video (cover) from second input
                    '-c:v', 'mjpeg',  # Use MJPEG for cover art
                    '-disposition:v:0', 'attached_pic'  # Set as attached picture
                ])
            
            # Add metadata if this is the tagged version
            if include_metadata:
                for key, value in metadata.items():
                    if key == 'lyrics':
                        # Convert semicolons to newlines
                        value = value.replace(';', '\n')
                    cmd.extend(['-metadata', f'{key}={value}'])
            else:
                # For untagged version, explicitly remove all metadata
                cmd.extend(['-map_metadata', '-1'])
            
            # Add format-specific options
            cmd.extend(['-acodec', fmt_config['codec']])
            cmd.extend(fmt_config['extra'])
            
            # Add output file
            cmd.append(current_output)
            
            try:
                print(f"\nCreating {fmt_name.upper()} file {'with' if include_metadata else 'without'} metadata...")
                print("Command:", ' '.join(cmd))
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"Successfully created {fmt_name.upper()} file")
                
                # Verify the file was created with cover art if supported and metadata included
                if include_metadata and fmt_config['supports_cover']:
                    probe_cmd = ['ffprobe', current_output]
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                    if 'Stream #0:1' not in probe_result.stderr:
                        print(f"Warning: Cover art may not have been properly embedded in {fmt_name.upper()} file")
                    
            except subprocess.CalledProcessError as e:
                print(f"Error creating {fmt_name.upper()} file:")
                print(e.stderr)
    
    # Clean up base WAV file
    safe_remove(base_wav)

if __name__ == "__main__":
    create_test_files()