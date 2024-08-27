import os
import subprocess
import streamlit as st
from pydub import AudioSegment
import warnings

# Suppress SyntaxWarnings from pydub
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Define the directory where model files will be stored
MODEL_DIR = os.path.join(os.getcwd(), "demucs_models")

# Ensure the directory exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


# Function to run shell commands and capture output
def run_command(command):
    result = subprocess.run(
        command,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout, result.stderr


# Function to separate audio into different stems using Demucs v4
def separate_audio(input_file, output_folder, progress_bar):
    st.write("🔄 Separating audio into stems...")

    # Command to run Demucs with a custom model directory
    command = f'DEMUCS_CACHE={MODEL_DIR} demucs -n htdemucs_ft "{input_file}" -o "{output_folder}"'
    stdout, stderr = run_command(command)

    if stderr:
        st.error(f"Error during audio separation: {stderr}")
        progress_bar.progress(100)
        return False

    progress_bar.progress(50)  # Assume 50% of the work is done after separation
    return True


# Function to save each stem as a separate MP3 file
def save_stems(output_folder, original_file_name, progress_bar):
    st.write("🔄 Saving stems as MP3 files...")
    stem_names = ["vocals", "drums", "bass", "other"]  # Adjusted for Demucs
    base_name = os.path.splitext(original_file_name)[0]
    stems_folder = os.path.join(output_folder, base_name)

    step_progress = 50 / len(stem_names)  # Remaining 50% distributed across stems
    for i, stem in enumerate(stem_names):
        stem_file_path = os.path.join(stems_folder, f"{stem}.wav")
        if os.path.exists(stem_file_path):
            stem_audio = AudioSegment.from_file(stem_file_path)
            output_file = os.path.join(output_folder, f"{base_name}-{stem}.mp3")
            stem_audio.export(output_file, format="mp3")
            st.write(f"✅ Saved {output_file}")
        else:
            st.warning(f"Stem file {stem_file_path} not found.")
        progress_bar.progress(50 + (i + 1) * step_progress)
    return True


# Function to convert MP4 to MP3 if needed
def convert_to_mp3(input_file):
    if input_file.endswith(".mp4"):
        st.write("🔄 Converting MP4 to MP3...")
        audio = AudioSegment.from_file(input_file, "mp4")
        mp3_file = input_file.replace(".mp4", ".mp3")
        audio.export(mp3_file, format="mp3")
        return mp3_file
    return input_file


# Main function to process the audio file
def process_audio(input_file):
    # Define output_folder (same location as the input file)
    output_folder = os.path.dirname(input_file)
    original_file_name = os.path.basename(input_file)

    # Convert MP4 to MP3 if needed
    input_file = convert_to_mp3(input_file)

    # Initialize progress bar
    progress_bar = st.progress(0)

    # Separate the audio
    if not separate_audio(input_file, output_folder, progress_bar):
        return  # Stop if separation failed

    # Save each stem as a separate MP3 file
    if not save_stems(output_folder, original_file_name, progress_bar):
        return  # Stop if saving stems failed

    st.success(f"All stems saved in {output_folder}")
    progress_bar.progress(100)


# Streamlit Interface
st.title("Audio Stem Separator")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "mp4"])

if uploaded_file is not None:
    save_path = os.path.join("uploads", uploaded_file.name)

    # Create the uploads directory if it doesn't exist
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File {uploaded_file.name} uploaded successfully!")

    if st.button("Process Audio"):
        with st.spinner("Processing..."):
            process_audio(save_path)
