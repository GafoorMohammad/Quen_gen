import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from pydub import AudioSegment
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import requests
import random

# Load environment variables from .env file
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

# Speech-to-text transcription
def transcribe_audio(audio_data, language) -> str:
    r = sr.Recognizer()
    result = r.recognize_google(audio_data, language=language, show_all=True)
    if isinstance(result, dict) and 'alternative' in result:
        best_transcription = max(result['alternative'], key=lambda x: x['confidence'])['transcript']
        return best_transcription
    else:
        return result

# Transcribe speech from audio file
def speech_to_text(input_path: str, language: str) -> str:
    wav_file = prepare_voice_file(input_path)
    with sr.AudioFile(wav_file) as source:
        audio_data = sr.Recognizer().record(source)
        return transcribe_audio(audio_data, language)

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

# Main Function
def main():
    input_type = input("Would you like to enter input via voice, audio, text file, or video? (voice/audio/file/video): ").strip().lower()

    if input_type == "voice":
        syllabus = speech_to_text(input("Enter audio path: ").strip(), "en-US")

    elif input_type == "audio":
        input_path = input("Enter the audio file path: ").strip()
        language = input("Enter the language code (e.g., en-US): ").strip()
        syllabus = speech_to_text(input_path, language)
        print("\nTranscribed Text from Audio:")
        print(syllabus)

    elif input_type == "file":
        file_path = input("Enter the file path: ").strip()
        syllabus = load_text(file_path)

    elif input_type == "video":
        video_path = input("Enter the video file path: ").strip()
        language = input("Enter the language code for transcription (e.g., en-US): ").strip()
        syllabus = convert_video_to_text(video_path, language)
        print("\nTranscribed Text from Video:")
        print(syllabus)
    else:
        print("Invalid option.")
        return

    print("Extracted Syllabus:", syllabus)
    print("\nSelect question type:")
    print("1. MCQ")
    print("2. Fill in the Blanks")
    print("3. True/False")
    print("4. Matching")
    question_type = input("Enter your choice (1/2/3/4): ").strip()
    num_questions = int(input("Enter the number of questions to generate: "))
    difficulty = input("Enter the difficulty level (easy, medium, or hard): ").strip().lower()

    if question_type == "1":
        print(generate_mcq(syllabus, num_questions, difficulty))
    elif question_type == "2":
        print(generate_fill_in_the_blanks(syllabus, num_questions, difficulty))
    elif question_type == "3":
        print(generate_true_false(syllabus, num_questions, difficulty))
    elif question_type == "4":
        col1, col2 = generate_matching_questions(syllabus, num_questions, difficulty)
        for left, right in zip(col1, col2):
            print(f"{left} -> {right}")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
