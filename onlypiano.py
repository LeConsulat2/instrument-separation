import os
import subprocess
import streamlit as st
from pydub import AudioSegment
import warnings

# pydub에서 발생할 수 있는 SyntaxWarning을 무시합니다.
warnings.filterwarnings("ignore", category=SyntaxWarning)

# 모델 파일이 저장될 디렉토리 경로를 설정합니다.
MODEL_DIR = os.path.join(os.getcwd(), "demucs_models")

# 모델 디렉토리가 존재하지 않으면 생성합니다.
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


# 쉘 명령어를 실행하고 그 결과를 캡처하는 함수입니다.
# 이 함수는 명령어 실행 중 발생할 수 있는 예외를 처리하여 오류 메시지를 반환합니다.
def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return "", f"Command '{e.cmd}' returned non-zero exit status {e.returncode}."


# Demucs v4를 사용하여 오디오를 여러 스템으로 분리하는 함수입니다.
def separate_audio(input_file, output_folder, progress_bar):
    st.write("🔄 Separating audio into stems...")

    # Demucs를 사용자 지정 모델 디렉토리와 함께 실행하는 명령어입니다.
    command = f'DEMUCS_CACHE={MODEL_DIR} demucs -n htdemucs_ft "{input_file}" -o "{output_folder}"'
    stdout, stderr = run_command(command)

    # 오류 발생 시, 오류 메시지를 출력하고 작업을 중단합니다.
    if stderr:
        st.error(f"Error during audio separation: {stderr}")
        progress_bar.progress(100)
        return False

    # 프로그레스 바를 50%로 업데이트합니다. (오디오 분리 작업이 완료되었다고 가정)
    progress_bar.progress(50)
    return True


# 각 스템을 별도의 MP3 파일로 저장하는 함수입니다.
def save_stems(output_folder, original_file_name, progress_bar):
    st.write("🔄 Saving stems as MP3 files...")
    stem_names = ["vocals", "drums", "bass", "other"]  # Demucs에 맞게 조정된 스템 이름
    base_name = os.path.splitext(original_file_name)[0]
    stems_folder = os.path.join(output_folder, base_name)

    # 스템 저장 작업이 완료될 때까지 프로그레스 바를 업데이트합니다.
    step_progress = 50 / len(stem_names)
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


# MP4 파일을 MP3로 변환하는 함수입니다.
# 이 함수는 업로드된 파일이 MP4 형식일 경우 MP3로 변환하여 저장합니다.
def convert_to_mp3(input_file):
    if input_file.endswith(".mp4"):
        st.write("🔄 Converting MP4 to MP3...")
        audio = AudioSegment.from_file(input_file, "mp4")
        mp3_file = input_file.replace(".mp4", ".mp3")
        audio.export(mp3_file, format="mp3")
        return mp3_file
    return input_file


# 오디오 파일을 처리하는 메인 함수입니다.
def process_audio(input_file):
    # 출력 폴더를 입력 파일의 위치로 설정합니다.
    output_folder = os.path.dirname(input_file)
    original_file_name = os.path.basename(input_file)

    # 필요하다면 MP4를 MP3로 변환합니다.
    input_file = convert_to_mp3(input_file)

    # 프로그레스 바 초기화
    progress_bar = st.progress(0)

    # 오디오 분리 작업을 수행합니다.
    if not separate_audio(input_file, output_folder, progress_bar):
        return  # 분리 작업이 실패한 경우 중단합니다.

    # 각 스템을 MP3 파일로 저장합니다.
    if not save_stems(output_folder, original_file_name, progress_bar):
        return  # 스템 저장 작업이 실패한 경우 중단합니다.

    st.success(f"All stems saved in {output_folder}")
    progress_bar.progress(100)


# Streamlit 인터페이스 설정
st.title("Audio Stem Separator")

# 오디오 파일 업로드 섹션
uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "mp4"])

if uploaded_file is not None:
    save_path = os.path.join("uploads", uploaded_file.name)

    # 업로드 디렉토리가 존재하지 않으면 생성합니다.
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # 업로드된 파일을 서버에 저장합니다.
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"File {uploaded_file.name} uploaded successfully!")

    # 'Process Audio' 버튼 클릭 시 오디오 처리 작업을 시작합니다.
    if st.button("Process Audio"):
        with st.spinner("Processing..."):
            process_audio(save_path)
