"""
Meeting Transcription - Transcribe audio, extract insights, and generate summaries
Uses AssemblyAI API for speech-to-text and analysis
"""

import streamlit as st
import os
import requests
import time
import subprocess
import tempfile
from typing import Optional, Dict
from pathlib import Path


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def extract_audio_from_video(video_path: str, output_path: str) -> bool:
    """
    Extract audio from video file using ffmpeg.

    Args:
        video_path: Path to input video file
        output_path: Path to output audio file (mp3)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if ffmpeg is available
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)

        # Extract audio to mp3
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "libmp3lame",  # MP3 codec
            "-b:a", "128k",  # Bitrate
            "-ar", "44100",  # Sample rate
            "-y",  # Overwrite output file
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def upload_file_to_assemblyai(file_data: bytes, api_key: str) -> Optional[str]:
    """
    Upload file to AssemblyAI and get upload URL.

    Args:
        file_data: File bytes
        api_key: AssemblyAI API key

    Returns:
        Upload URL or None if failed
    """
    url = "https://api.assemblyai.com/v2/upload"

    headers = {
        "Authorization": api_key
    }

    try:
        response = requests.post(url, headers=headers, data=file_data, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result.get("upload_url")
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {str(e)}")
        return None


def submit_transcription(audio_url: str, api_key: str, options: Dict) -> Optional[Dict]:
    """
    Submit audio file for transcription via AssemblyAI API.

    Args:
        audio_url: URL to audio file or uploaded file
        api_key: AssemblyAI API key
        options: Transcription options (speaker_labels, auto_chapters, etc.)

    Returns:
        Response dict with transcript ID or error
    """
    url = "https://api.assemblyai.com/v2/transcript"

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "audio_url": audio_url,
        **options
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API Error: {str(e)}"}


def get_transcription_status(transcript_id: str, api_key: str) -> Optional[Dict]:
    """
    Get transcription status and results.

    Args:
        transcript_id: Transcript ID from submit_transcription
        api_key: AssemblyAI API key

    Returns:
        Response dict with status and transcript data
    """
    url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    headers = {
        "Authorization": api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API Error: {str(e)}"}


def render_transcription_app():
    """Render the Meeting Transcription interface."""

    st.markdown("## 🎙️ Meeting Transcription")
    st.caption("Transcribe audio files, extract insights, and generate summaries using AI")

    # Get API key from secrets
    api_key = get_credential("ASSEMBLYAI_API_KEY")

    if not api_key:
        st.error("❌ ASSEMBLYAI_API_KEY not configured in secrets.toml")
        st.info("💡 Add your AssemblyAI API key to secrets.toml:\n\n`ASSEMBLYAI_API_KEY = \"your_api_key\"`")
        st.info("Get your API key at: https://www.assemblyai.com/app/api-keys")
        return

    # Initialize session state
    if "transcripts" not in st.session_state:
        st.session_state.transcripts = []

    # Main interface
    st.markdown("### Upload or Provide Audio URL")

    tab1, tab2 = st.tabs(["📤 Upload File", "🔗 Audio URL"])

    uploaded_file = None
    audio_url = None

    with tab1:
        st.caption("Supports audio and video files. Video files will be automatically converted to audio.")

        uploaded_file = st.file_uploader(
            "Upload audio or video file",
            type=["mp3", "wav", "m4a", "flac", "ogg", "mp4", "mov", "avi", "mkv", "webm"],
            help="Max file size: 500MB. Video files will be converted to MP3."
        )

        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"📁 File: {uploaded_file.name} ({file_size_mb:.1f} MB)")

            if file_size_mb > 500:
                st.error("❌ File too large. Maximum size is 500MB.")
                uploaded_file = None

    with tab2:
        audio_url = st.text_input(
            "Audio file URL",
            placeholder="https://example.com/audio.mp3",
            help="Direct URL to audio file (mp3, wav, m4a, flac, ogg)"
        )

    # Transcription options
    st.markdown("### Transcription Options")

    col1, col2 = st.columns(2)

    with col1:
        speaker_labels = st.checkbox(
            "Speaker Detection",
            value=True,
            help="Identify different speakers in the audio"
        )

        auto_chapters = st.checkbox(
            "Auto Chapters",
            value=True,
            help="Automatically segment transcript into chapters"
        )

    with col2:
        sentiment_analysis = st.checkbox(
            "Sentiment Analysis",
            value=False,
            help="Analyze sentiment of each sentence"
        )

        entity_detection = st.checkbox(
            "Entity Detection",
            value=False,
            help="Detect entities like names, organizations, locations"
        )

    # Submit button
    if st.button("🎙️ Start Transcription", type="primary", use_container_width=True):
        if not uploaded_file and not audio_url:
            st.error("Please upload a file or provide an audio URL")
        else:
            # Build options
            options = {
                "speaker_labels": speaker_labels,
                "auto_chapters": auto_chapters,
                "sentiment_analysis": sentiment_analysis,
                "entity_detection": entity_detection
            }

            final_audio_url = audio_url

            # Handle file upload
            if uploaded_file:
                file_extension = Path(uploaded_file.name).suffix.lower()
                video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
                is_video = file_extension in video_extensions

                with st.spinner("Processing file..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_path = tmp_file.name

                        # If video, extract audio
                        if is_video:
                            st.info("🎬 Video file detected. Extracting audio to MP3...")
                            audio_tmp_path = tmp_path.replace(file_extension, '.mp3')

                            if extract_audio_from_video(tmp_path, audio_tmp_path):
                                st.success("✅ Audio extracted successfully")
                                os.remove(tmp_path)  # Remove original video
                                tmp_path = audio_tmp_path

                                # Show size reduction
                                original_size = uploaded_file.size / (1024 * 1024)
                                new_size = os.path.getsize(tmp_path) / (1024 * 1024)
                                st.success(f"📉 Size reduced: {original_size:.1f}MB → {new_size:.1f}MB")
                            else:
                                st.error("❌ Failed to extract audio. Please install ffmpeg or use an audio file.")
                                os.remove(tmp_path)
                                st.stop()

                        # Read file data
                        with open(tmp_path, 'rb') as f:
                            file_data = f.read()

                        # Upload to AssemblyAI
                        st.info("☁️ Uploading to AssemblyAI...")
                        final_audio_url = upload_file_to_assemblyai(file_data, api_key)

                        # Clean up temp file
                        os.remove(tmp_path)

                        if not final_audio_url:
                            st.error("❌ Upload failed")
                            st.stop()

                        st.success(f"✅ Upload complete!")

                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.stop()

            # Submit transcription
            if final_audio_url:
                with st.spinner("Submitting for transcription..."):
                    result = submit_transcription(final_audio_url, api_key, options)

                    if result.get("error"):
                        st.error(f"❌ {result['error']}")
                    elif result.get("id"):
                        st.success(f"✅ Transcription started! ID: {result['id']}")

                        # Add to session state
                        st.session_state.transcripts.insert(0, {
                            "id": result["id"],
                            "url": final_audio_url if not uploaded_file else f"Uploaded: {uploaded_file.name}",
                            "status": "queued",
                            "options": options
                        })

                        st.rerun()

    # Display transcripts
    if st.session_state.transcripts:
        st.markdown("---")
        st.markdown("### Your Transcriptions")

        for idx, transcript in enumerate(st.session_state.transcripts):
            transcript_id = transcript["id"]

            with st.expander(f"🎙️ Transcript {transcript_id[:8]}... - {transcript.get('status', 'unknown').upper()}", expanded=(idx == 0)):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.caption(f"**Audio URL:** {transcript['url'][:60]}...")
                    st.caption(f"**ID:** {transcript_id}")

                with col2:
                    if st.button("🔄 Refresh", key=f"refresh_{transcript_id}"):
                        with st.spinner("Checking status..."):
                            status_result = get_transcription_status(transcript_id, api_key)

                            if status_result.get("error"):
                                st.error(f"❌ {status_result['error']}")
                            else:
                                # Update transcript in session state
                                transcript["status"] = status_result.get("status", "unknown")
                                transcript["result"] = status_result
                                st.rerun()

                # Display results
                if transcript.get("result"):
                    result = transcript["result"]
                    status = result.get("status", "unknown")

                    if status == "completed":
                        st.success("✅ Transcription complete!")

                        # Display transcript
                        st.markdown("#### Transcript")
                        st.text_area(
                            "Full transcript",
                            value=result.get("text", ""),
                            height=200,
                            key=f"transcript_text_{transcript_id}"
                        )

                        # Display chapters if available
                        if result.get("chapters"):
                            st.markdown("#### Chapters")
                            for chapter in result["chapters"]:
                                st.markdown(f"**{chapter.get('headline', 'Chapter')}** ({chapter.get('start', 0) / 1000:.1f}s - {chapter.get('end', 0) / 1000:.1f}s)")
                                st.caption(chapter.get("summary", ""))

                        # Display speakers if available
                        if result.get("utterances"):
                            st.markdown("#### Speakers")
                            for utterance in result["utterances"][:5]:  # Show first 5
                                speaker = utterance.get("speaker", "Unknown")
                                text = utterance.get("text", "")
                                st.markdown(f"**Speaker {speaker}:** {text[:100]}...")

                        # Download button
                        st.download_button(
                            "📥 Download Transcript",
                            data=result.get("text", ""),
                            file_name=f"transcript_{transcript_id}.txt",
                            mime="text/plain",
                            key=f"download_{transcript_id}"
                        )

                    elif status == "error":
                        st.error(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")

                    elif status == "processing":
                        st.info("⏳ Transcription in progress...")

                    elif status == "queued":
                        st.info("⏳ Transcription queued...")
                else:
                    st.info("Click 'Refresh' to check transcription status")

    # Clear history button
    if st.session_state.transcripts:
        st.markdown("---")
        if st.button("🗑️ Clear All Transcripts", use_container_width=True):
            st.session_state.transcripts = []
            st.rerun()
