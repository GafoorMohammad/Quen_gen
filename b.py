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
from pydantic import BaseModel
from fastapi import HTTPException


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
#Translation 
class TextInput(BaseModel):
    text: str

def translate_text(text: str, target_language: str) -> str:
    """Translate text using Google Translate API."""
    api_url = "https://translation.googleapis.com/language/translate/v2"
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")

    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured.")

    params = {
        "q": text,
        "target": target_language,
        "format": "text",
        "key": api_key,
    }
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        result = response.json()
        return result["data"]["translations"][0]["translatedText"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Translation API error: {e}")
    
def get_supported_languages() -> dict:
    """Fetch supported languages from Google Translate API."""
    api_url = "https://translation.googleapis.com/language/translate/v2/languages"
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")

    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured.")

    params = {
        "key": api_key,
        "target": "en",  # Fetch language names in English
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        result = response.json()
        return {lang["name"]: lang["language"] for lang in result["data"]["languages"]}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Language API error: {e}")




# Perplexity-based question generation
def query_perplexity(prompt, model=MODEL):
    if not PERPLEXITY_API_KEY:
        raise ValueError("Perplexity API key is missing. Please set the PERPLEXITY_API_KEY variable in your .env file.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Modify temperature to 0 for deterministic output
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for generating educational questions."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,  # Set temperature to 0 for deterministic responses
        "max_tokens": 10000,  # Ensure an appropriate max token limit
        # Optionally, add a seed parameter if supported by the API (uncomment below if supported)
        "seed": 12345,  # Optional seed for deterministic responses (if supported by the API)
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

    Instructions:
    - Generate {num_questions} multiple-choice questions (MCQs).
    - Provide exactly 4 options for each question.
    - Clearly indicate the correct answer and explain why it is correct.
    - Format output strictly as follows:

    Example:
    Q1. What is the population of Dubai as of 2024?
    A. 3.79 million
    B. 3.295 million
    C. 4.1 million
    D. 5 million
    Answer: A - Explanation: The population of Dubai as of 2024 is approximately 3.79 million, as stated in reliable sources.

    Questions must be unique, meaningful, and ensure the structure: Question -> Options -> Answer -> Explanation.
    Difficulty Level: {difficulty}.
    """
    # Generate the MCQs
    mcqs = query_perplexity(prompt)
    return mcqs



# Simulated response for generating fill-in-the-blank questions
def generate_fill_in_the_blanks(syllabus, num_questions, difficulty):
    prompt = f"""
    Syllabus:
    {syllabus}

    Instructions:
    - Generate {num_questions} 'Fill in the Blank' questions.
    - Format questions and answers exactly as shown in this example:

    Questions:
    1. Fill in the blank: The ____________ is the powerhouse of the cell.
       Mitochondria
       The mitochondria generate energy for cellular processes.
    2. Fill in the blank: Water freezes at ____________ degrees Celsius.
       Zero
       Zero degrees Celsius is the freezing point of water.

    Answers:
    1. Mitochondria - The mitochondria generate energy for cellular processes.
    2. Zero - Zero degrees Celsius is the freezing point of water.

    Ensure all outputs are unique, accurate, and aligned with the syllabus.
    Difficulty Level: {difficulty}.
    """
    # Simulated response for testing
    response = f"""
    Questions:
    1. Fill in the blank: The process of ____________ converts sunlight into chemical energy.
       Photosynthesis
       Photosynthesis is the process used by plants to convert light energy into chemical energy.
    2. Fill in the blank: The capital city of France is ____________.
       Paris
       Paris is the capital and largest city of France.

    Answers:
    1. Photosynthesis - Photosynthesis is the process used by plants to convert light energy into chemical energy.
    2. Paris - Paris is the capital and largest city of France.
    """
    return response.strip()


def generate_true_false(syllabus, num_questions, difficulty):
    prompt = f"""
    Topic: {syllabus}

    Instructions:
    - Generate {num_questions} True/False questions about the topic "{syllabus}".
    - Use the following strict format for each question:

    Q<n>. <Question text>? (True/False)
    Answer: <True or False>
    Explanation: <Concise explanation for the answer>

    Example:
    Q1. Cricket is played with a ball and bat? (True/False)
    Answer: True
    Explanation: Cricket is a game played with a bat and ball between two teams.

    Q2. A cricket team consists of 15 players? (True/False)
    Answer: False
    Explanation: A cricket team consists of 11 players, not 15.

    Ensure:
    - All questions are unique and align with the topic.
    - The explanation is concise and factual without repeating the answer.
    - The output is structured for easy parsing.
    - Matches the difficulty level specified: {difficulty}.
    """
    return query_perplexity(prompt)

    
def generate_matching_questions(syllabus, num_questions, difficulty):
    prompt = f"""
    Syllabus:
    {syllabus}

    Instructions:
    - Generate {num_questions} matching pairs of terms/items.
    - Strictly format the output as follows:

    Example:
    1. Term A1 | Match A1
    2. Term A2 | Match A2
    3. Term A3 | Match A3

    Each line should have exactly one pair, separated by a '|' symbol.
    Do NOT provide additional context or explanations.
    Difficulty Level: {difficulty}.
    """
    result = query_perplexity(prompt)  # Assuming this interacts with Perplexity AI
    # Parse the result into structured data
    pairs = [line.split(" | ") for line in result.split("\n") if " | " in line]
    
    # Separate columns and answers
    column1 = [{"id": f"c1_item_{i+1}", "item": pair[0]} for i, pair in enumerate(pairs)]
    column2 = [{"id": f"c2_item_{i+1}", "item": pair[1]} for i, pair in enumerate(pairs)]
    answers = [{"column1_id": f"c1_item_{i+1}", "column2_id": f"c2_item_{i+1}"} for i in range(len(pairs))]

    return column1, column2, answers

  
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

    # Input Type Selection
    input_type = st.sidebar.selectbox("Select Input Type", ["Text", "File", "Video", "Audio"])
    syllabus = None

    # Handle different input types
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

    # Display extracted content
    if syllabus:
        st.subheader("Extracted Syllabus:")
        st.text_area("Extracted Content", syllabus, height=200)

        # Question Generator Section
        st.subheader("Question Generator")
        question_type = st.selectbox("Select Question Type", ["MCQ", "Fill in the Blanks", "True/False", "Matching"])
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, step=1)
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"]).lower()

        # Fetch Supported Languages
        languages = get_supported_languages()
        if "Error" in languages:
            st.error("Could not fetch language options.")
            return
        selected_language = st.selectbox("Select Language", list(languages.keys()))
        target_language_code = languages[selected_language]

        # Generate Questions and Translate
        if st.button("Generate Questions"):
            with st.spinner("Generating questions..."):
                # Generate questions (dummy logic, replace with actual implementation)
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

                # Translate the output
                translated_result = translate_text(result, target_language_code)
                st.text_area("Translated Questions", translated_result, height=300)



if __name__ == "__main__":
    main()
