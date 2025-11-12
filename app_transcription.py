"""
Meeting Transcription - Transcribe audio, extract insights, and generate summaries
Uses AssemblyAI API for speech-to-text and analysis
"""

import streamlit as st
import os
import requests
import time
from typing import Optional, Dict


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


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

    with tab1:
        st.info("File upload feature coming soon. Please use Audio URL for now.")
        uploaded_file = st.file_uploader(
            "Upload audio file",
            type=["mp3", "wav", "m4a", "flac", "ogg"],
            disabled=True
        )

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
        if not audio_url:
            st.error("Please provide an audio URL")
        else:
            # Build options
            options = {
                "speaker_labels": speaker_labels,
                "auto_chapters": auto_chapters,
                "sentiment_analysis": sentiment_analysis,
                "entity_detection": entity_detection
            }

            with st.spinner("Submitting audio for transcription..."):
                result = submit_transcription(audio_url, api_key, options)

                if result.get("error"):
                    st.error(f"❌ {result['error']}")
                elif result.get("id"):
                    st.success(f"✅ Transcription started! ID: {result['id']}")

                    # Add to session state
                    st.session_state.transcripts.insert(0, {
                        "id": result["id"],
                        "url": audio_url,
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
