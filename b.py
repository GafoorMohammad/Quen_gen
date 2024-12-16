import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from pydub import AudioSegment
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import requests
import random
from pydub import AudioSegment
# Load environment variables from .env 
from dotenv import load_dotenv

load_dotenv()

# Get API key from environment variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "llama-3.1-sonar-small-128k-online"

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
    return text

# Function to extract text from Word document
def extract_text_from_word(file_path):
    doc = Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

# Function to load text
def load_text(file_path_or_text):
    if os.path.isfile(file_path_or_text):
        if file_path_or_text.endswith('.pdf'):
            return extract_text_from_pdf(file_path_or_text)
        elif file_path_or_text.endswith('.docx'):
            return extract_text_from_word(file_path_or_text)
        elif file_path_or_text.endswith('.txt'):
            with open(file_path_or_text, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            raise ValueError("Unsupported file format. Use PDF, Word (.docx), or plain text files.")
    return file_path_or_text

# Function to prepare audio files for speech-to-text
def prepare_voice_file(path: str) -> str:
    if os.path.splitext(path)[1] == '.wav':
        return path
    elif os.path.splitext(path)[1] in ('.mp3', '.m4a', '.ogg', '.flac'):
        audio_file = AudioSegment.from_file(path, format=os.path.splitext(path)[1][1:])
        wav_file = os.path.splitext(path)[0] + '.wav'
        audio_file.export(wav_file, format='wav')
        return wav_file
    else:
        raise ValueError(f'Unsupported audio format: {os.path.splitext(path)[1]}')
    
def convert_to_wav(input_audio, output_audio="converted_audio.wav"):
    try:
        audio = AudioSegment.from_file(input_audio)
        audio.export(output_audio, format="wav")
        return output_audio
    except Exception as e:
        raise ValueError(f"Error converting audio file: {e}")


# Speech-to-text transcription
def transcribe_audio(audio_data, language="en-US"):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_data) as source:
            audio = recognizer.record(source)
        result = recognizer.recognize_google(audio, language=language, show_all=True)
        
        if not result or 'alternative' not in result:
            return "No transcription available."

        # Handle missing 'confidence' key
        alternatives = result['alternative']
        best_transcription = max(
            alternatives,
            key=lambda x: x.get('confidence', 0)  # Default confidence to 0 if missing
        )['transcript']
        return best_transcription
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError as e:
        return f"Error with the speech recognition service: {e}"


# Transcribe speech from audio file
def speech_to_text(audio_path, language="en-US"):
    recognizer = sr.Recognizer()
    
    try:
        # Convert input audio to WAV format if necessary
        wav_file = convert_to_wav(audio_path)

        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
        result = recognizer.recognize_google(audio_data, language=language, show_all=True)
        
        if not result or 'alternative' not in result:
            return "No transcription available."

        # Handle missing 'confidence' key
        alternatives = result['alternative']
        best_transcription = max(
            alternatives,
            key=lambda x: x.get('confidence', 0)
        )['transcript']
        return best_transcription
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError as e:
        return f"Error with the speech recognition service: {e}"
    except ValueError as e:
        return f"File conversion error: {e}"


# Extract audio from video
def extract_audio_from_video(video_path, output_audio_path="extracted_audio.wav"):
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_audio_path, codec='pcm_s16le')
        print(f"Audio extracted and saved to {output_audio_path}")
        return output_audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

# Convert video to text
def convert_video_to_text(video_path, language="en-US"):
    audio_path = extract_audio_from_video(video_path)
    if audio_path:
        transcription = speech_to_text(audio_path, language)
        return transcription
    return "Failed to process the video."

# Perplexity-based question generation
def query_perplexity(prompt, model=MODEL):
    if not PERPLEXITY_API_KEY:
        raise ValueError("Perplexity API key is missing. Please set the PERPLEXITY_API_KEY variable in your .env file.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for generating educational questions."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 10000,
    }
    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        return "No output received from the API."
    except requests.exceptions.RequestException as e:
        return f"Error querying Perplexity API: {str(e)}"

# Question generation functions with difficulty
def generate_mcq(syllabus, num_questions, difficulty):
    prompt = f"""
    Syllabus:
    {syllabus}

    Based on the syllabus above, generate {num_questions} multiple-choice questions (MCQs).
    Provide 4 options for each question, and clearly indicate the correct answer.
    Difficulty Level: {difficulty}.
    """
    return query_perplexity(prompt)

def generate_fill_in_the_blanks(syllabus, num_questions, difficulty):
    prompt = f"""
    Syllabus:
    {syllabus}

    Based on the syllabus above, generate {num_questions} 'Fill in the Blanks' questions.
    Provide the correct answers for each blank.
    Difficulty Level: {difficulty}.
    """
    return query_perplexity(prompt)

def generate_true_false(syllabus, num_questions, difficulty):
    prompt = f"""
    Syllabus:
    {syllabus}

    Based on the syllabus above, generate {num_questions} True/False questions.
    Clearly indicate the correct answers.
    Difficulty Level: {difficulty}.
    """
    return query_perplexity(prompt)

def generate_matching_questions(syllabus, num_questions, difficulty):
    prompt = f"""
    Syllabus:
    {syllabus}

    Based on the syllabus above, generate {num_questions} matching questions.
    Provide two columns of items where each item in column 1 matches with an item in column 2.
    Difficulty Level: {difficulty}.
    """
    matching_pairs = query_perplexity(prompt)
    col1, col2 = [], []

    # Split pairs and shuffle
    for pair in matching_pairs.split('\n'):
        if '|' in pair:
            left, right = map(str.strip, pair.split('|'))
            col1.append(left)
            col2.append(right)

    random.shuffle(col1)
    random.shuffle(col2)
    return col1, col2
  
def generate_questions(syllabus, num_questions, question_type, difficulty):
    """
    Generate questions based on syllabus and other parameters.
    :param syllabus: The input content/syllabus.
    :param num_questions: Number of questions to generate.
    :param question_type: Type of questions to generate ("MCQ", "Fill in the Blanks", etc.).
    :param difficulty: Difficulty level of questions.
    :return: Generated questions as a string.
    """
    # Simulating question generation based on input
    generated_questions = []
    for i in range(num_questions):
        if question_type == "MCQ":
            generated_questions.append(f"MCQ {i + 1}: [Question based on {syllabus}] (Difficulty: {difficulty})")
        elif question_type == "Fill in the Blanks":
            generated_questions.append(f"Fill in the Blanks {i + 1}: [Sentence based on {syllabus}] (Difficulty: {difficulty})")
        elif question_type == "True/False":
            generated_questions.append(f"True/False {i + 1}: [Statement based on {syllabus}] (Difficulty: {difficulty})")
        elif question_type == "Matching":
            generated_questions.append(f"Matching {i + 1}: [Pair based on {syllabus}] (Difficulty: {difficulty})")
    
    return "\n".join(generated_questions)



# Main Function

def main():
    st.title("Multilingual Question Generator")

    input_type = st.sidebar.selectbox("Select Input Type", ["Text", "File", "Video", "Audio"])
    syllabus = None

    if input_type == "Text":
        syllabus = st.text_area("Enter Syllabus or Content")

    elif input_type == "File":
        uploaded_file = st.file_uploader("Upload a PDF, Word, or Text file", type=["pdf", "docx", "txt"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.pdf'):
                syllabus = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.name.endswith('.docx'):
                syllabus = extract_text_from_word(uploaded_file)
            elif uploaded_file.name.endswith('.txt'):
                syllabus = uploaded_file.read().decode("utf-8")

    elif input_type == "Video":
        uploaded_video = st.file_uploader("Upload a Video file", type=["mp4", "mkv", "avi"])
        if uploaded_video is not None:
            with open("uploaded_video.mp4", "wb") as f:
                f.write(uploaded_video.read())
            audio_path = extract_audio_from_video("uploaded_video.mp4")
            syllabus = speech_to_text(audio_path, "en-US")

    elif input_type == "Audio":
        uploaded_audio = st.file_uploader("Upload an Audio file", type=["wav", "mp3", "m4a"])
        if uploaded_audio is not None:
            with open("uploaded_audio.wav", "wb") as f:
                f.write(uploaded_audio.read())
            syllabus = speech_to_text("uploaded_audio.wav", "en-US")

    if syllabus:
        st.subheader("Extracted Syllabus:")
        st.text_area("Extracted Content", syllabus, height=200)

        st.subheader("Question Generator")
        question_type = st.selectbox("Select Question Type", ["MCQ", "Fill in the Blanks", "True/False", "Matching"])
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, step=1)
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"]).lower()



        if st.button("Generate Questions"):
            with st.spinner("Generating questions..."):
                if question_type == "MCQ":
                    result = query_perplexity(f"Generate {num_questions} MCQs based on the following syllabus:\n\n{syllabus}\n\nDifficulty: {difficulty}.")
                elif question_type == "Fill in the Blanks":
                    result = query_perplexity(f"Generate {num_questions} 'Fill in the Blanks' questions based on the following syllabus:\n\n{syllabus}\n\nDifficulty: {difficulty}.")
                elif question_type == "True/False":
                    result = query_perplexity(f"Generate {num_questions} True/False questions based on the following syllabus:\n\n{syllabus}\n\nDifficulty: {difficulty}.")
                elif question_type == "Matching":
                    result = query_perplexity(f"Generate {num_questions} matching questions based on the following syllabus:\n\n{syllabus}\n\nDifficulty: {difficulty}.")
                else:
                    st.error("Invalid Question Type Selected.")
                    return


                st.success("Questions Generated!")
                st.text_area("Generated Questions", result, height=300)


if __name__ == "__main__":
    main()
