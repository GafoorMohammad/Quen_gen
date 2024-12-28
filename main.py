from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from pydantic import BaseModel
import shutil
import os
import uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (replace "*" with specific URLs for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

from b import (
    load_text,
    transcribe_audio,
    convert_video_to_text,
    translate_text,
    get_supported_languages,
    generate_mcq,
    generate_fill_in_the_blanks,
    generate_true_false,
    generate_matching_questions,
)

# Temporary directory for storing uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class TextInput(BaseModel):
    text: str


class MCQInput(BaseModel):
    syllabus: str
    num_questions: int
    difficulty: str


@app.middleware("http")
async def assign_request_id(request: Request, call_next):
    """
    Middleware to assign a unique request ID to each incoming request.
    """
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.post("/process-text/")
async def process_text(input: TextInput, request: Request):
    processed_text = load_text(input.text)
    return {
        "request_id": request.state.request_id,
        "processed_text": processed_text,
    }


@app.post("/process-file/")
async def process_file(request: Request, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        if file.filename.endswith((".pdf", ".docx", ".txt")):
            result = load_text(file_path)
        elif file.filename.endswith((".mp3", ".wav", ".m4a")):
            result = transcribe_audio(file_path)
        elif file.filename.endswith((".mp4", ".mkv", ".avi")):
            result = convert_video_to_text(file_path)
        else:
            return {"error": "Unsupported file format."}
    finally:
        os.remove(file_path)  # Clean up

    return {"request_id": request.state.request_id, "result": result}



@app.post("/translate/")
async def translate(
    request: Request, text: str = Form(...), target_language: str = Form(...)
):
    """
    Translate a given text into the target language.
    - Input: Form fields for text and target language
    - Output: Translated text
    """
    try:
        translated_text = translate_text(text, target_language)
        return {
            "request_id": request.state.request_id,
            "translated_text": translated_text,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in translation: {str(e)}")



@app.get("/supported-languages/")
async def supported_languages(request: Request):
    """
    Get a list of supported languages.
    - Output: Dictionary with language names and their codes
    """
    try:
        languages = get_supported_languages()
        return {
            "request_id": request.state.request_id,
            "languages": languages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching languages: {str(e)}")


@app.post("/generate-mcq/")
async def generate_mcq_endpoint(input: MCQInput, request: Request):
    # Generate the MCQ response
    mcq_response = generate_mcq(input.syllabus, input.num_questions, input.difficulty)

    # Split the response into individual questions
    mcq_items = mcq_response.split("\n\n")

    mcq_with_ids = []
    for question in mcq_items:
        parts = question.split("\n")
        
        # Ensure we have at least 6 parts (question, options, answer, explanation)
        if len(parts) < 6:
            continue  # Skip this question if it doesn't have enough parts

        question_text = parts[0]  # First line is the question text
        options = "\n".join(parts[1:5])  # Next 4 lines are options
        answer_and_explanation = parts[5]  # Last line has the answer and explanation
        
        # Split answer and explanation
        if "Answer:" in answer_and_explanation and "- Explanation:" in answer_and_explanation:
            answer, explanation = answer_and_explanation.split(" - Explanation: ")
            answer = answer.split(":")[1].strip()  # Extract the correct option (e.g., A)
            explanation = explanation.strip()  # Clean the explanation
        else:
            continue  # Skip if the format is not as expected

        # Add the MCQ with unique ID
        mcq_with_ids.append({
            "id": str(uuid.uuid4()),
            "question": question_text,
            "options": options,
            "answer": answer,
            "explanation": explanation
        })

    # Return the MCQ response with unique IDs
    return {"request_id": request.state.request_id, "mcq": mcq_with_ids}


@app.post("/generate-fill-in-the-blanks/")
async def generate_fill_in_blanks_endpoint(input: MCQInput, request: Request):
    # Generate the questions using the refined prompt
    blanks = generate_fill_in_the_blanks(
        input.syllabus, input.num_questions, input.difficulty
    )
    
    # Log the raw output for debugging purposes
    print("Raw Output from Generator:\n", blanks)
    
    blanks_with_details = []
    
    # Ensure there is content to process
    if not blanks.strip():
        return {
            "request_id": request.state.request_id,
            "fill_in_the_blanks": [],
            "error": "No questions were generated. Please retry with a clearer syllabus or adjusted difficulty."
        }
    
    # Split the output into individual questions
    question_blocks = blanks.strip().split("\n\n")
    
    # Process each block
    for idx, question_block in enumerate(question_blocks):
        try:
            # Split the question into its components
            lines = question_block.strip().split("\n")
            
            # If there are 3 parts (question, answer, explanation), process them
            if len(lines) == 3:
                question_text = lines[0].replace("Fill in the blank:", "").strip()
                answer = lines[1].replace("Answer:", "").strip()
                explanation = lines[2].replace("Explanation:", "").strip()

                blanks_with_details.append({
                    "id": str(uuid.uuid4()),
                    "question": question_text,
                    "answer": answer,
                    "explanation": explanation,
                })
            else:
                print(f"Unexpected format for question block {idx + 1}: {question_block}")
        except Exception as e:
            print(f"Error processing question block {idx + 1}: {question_block} - {e}")
    
    # Return error if no valid questions were found
    if not blanks_with_details:
        return {
            "request_id": request.state.request_id,
            "fill_in_the_blanks": [],
            "error": "Generated questions were improperly formatted. Please retry."
        }

    # Return valid questions
    return {
        "request_id": request.state.request_id,
        "fill_in_the_blanks": blanks_with_details,
    }



@app.post("/generate-true-false/")
async def generate_true_false_endpoint(input: MCQInput, request: Request):
    tf_questions = generate_true_false(
        input.syllabus, input.num_questions, input.difficulty
    )

    tf_questions_with_details = []
    if not tf_questions.strip():
        return {
            "request_id": request.state.request_id,
            "true_false_questions": [],
            "error": "No questions were generated. Please check the syllabus and retry.",
        }

    for question_block in tf_questions.split("\n\n"):
        lines = question_block.split("\n")
        if len(lines) == 3:
            question_line = lines[0].strip()
            answer_line = lines[1].strip()
            explanation_line = lines[2].strip()

            if question_line.startswith("Q") and "?" in question_line:
                question_text = question_line.split(". ", 1)[1].strip()
                correct_answer = answer_line.replace("Answer:", "").strip()
                explanation_text = explanation_line.replace("Explanation:", "").strip()

                tf_questions_with_details.append({
                    "id": str(uuid.uuid4()),
                    "question": question_text,
                    "answer": correct_answer,
                    "explanation": explanation_text,
                })

    if not tf_questions_with_details:
        return {
            "request_id": request.state.request_id,
            "true_false_questions": [],
            "error": "Generated questions were improperly formatted. Please retry.",
        }

    return {
        "request_id": request.state.request_id,
        "true_false_questions": tf_questions_with_details,
    }

@app.post("/generate-matching-questions/")
async def generate_matching_questions_endpoint(input: MCQInput, request: Request):
    column1, column2, answers = generate_matching_questions(
        input.syllabus, input.num_questions, input.difficulty
    )

    # Create a unique question ID
    question_id = str(uuid.uuid4())

    return {
        "request_id": request.state.request_id,
        "questions": [
            {
                "question_id": question_id,
                "column1": column1,
                "column2": column2,
                "answers": answers
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
