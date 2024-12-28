# Quen_gen

Quen_gen is a Python project for generating and handling various tasks. This project uses FastAPI for building a web application and includes a set of dependencies specified in the `requirements.txt` file.

## Features

- FastAPI for building APIs
- Interactive API documentation using Swagger UI
- Local development server with Uvicorn

## Setup Instructions

Follow the steps below to get the project up and running.

### 1. Clone the repository

Clone the repository to your local machine:

```bash
git clone https://github.com/GafoorMohammad/Quen_gen.git
cd Quen_gen
```

### 2. Create or activate a Python environment

It's recommended to use a virtual environment to manage dependencies. You can create a new virtual environment or activate an existing one:

- **Activate the virtual environment**:

  On Windows:

  ```bash
  venv\Scripts\activate
  ```

  On macOS/Linux:

  ```bash
  source venv/bin/activate
  ```

  If you already have an existing virtual environment, simply activate it using the command above.

  - **Create a new virtual environment** (if you don't have one already):

  On Windows:

  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```

  On macOS/Linux:

  ```bash
  python3 -m venv venv
  ```


### 3. Install dependencies

Make sure you have Python and pip installed, then install the required dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Run the application

To start the FastAPI app, use Uvicorn to run the server:

```bash
uvicorn main:app --reload
```

This command will start a local development server. The `--reload` flag enables automatic reloading when you make changes to the code.

### 5. Access the API documentation

Once the server is running, you can access the interactive API documentation at:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

This page provides an easy way to explore and test the available API endpoints.
```

Here's a comprehensive documentation of the API routes and payloads for the FastAPI application deployed on your local machine (`http://127.0.0.1:8000`).

---

## API Documentation

### **Base URL**
`http://127.0.0.1:8000`

---

### 1. **Process Text**

**Endpoint**: `/process-text/`  
**Method**: `POST`  
**Description**: Processes a given text and returns the result.  

**Request Payload**:
```json
{
  "text": "Sample text to process"
}
```

**Response**:
```json
{
  "request_id": "unique-request-id",
  "processed_text": "Processed version of the text"
}
```

---

### 2. **Process File**

**Endpoint**: `/process-file/`  
**Method**: `POST`  
**Description**: Uploads and processes a file (text, audio, or video).  

**Request Payload**:  
`multipart/form-data`
- `file`: The file to upload.

**Response**:
```json
{
  "request_id": "unique-request-id",
  "result": "Processed result from the file"
}
```

---

### 3. **Translate Text**

**Endpoint**: `/translate/`  
**Method**: `POST`  
**Description**: Translates a given text to the specified target language.  

**Request Payload**:
`application/x-www-form-urlencoded`
- `text`: Text to translate.
- `target_language`: Language code for the target language (e.g., `fr` for French).

**Response**:
```json
{
  "request_id": "unique-request-id",
  "translated_text": "Translated version of the text"
}
```

---

### 4. **Supported Languages**

**Endpoint**: `/supported-languages/`  
**Method**: `GET`  
**Description**: Fetches the list of supported languages for translation.  

**Response**:
```json
{
  "request_id": "unique-request-id",
  "languages": {
    "language_code": "Language Name"
  }
}
```

---

### 5. **Generate MCQ**

**Endpoint**: `/generate-mcq/`  
**Method**: `POST`  
**Description**: Generates multiple-choice questions (MCQs) based on a syllabus.  

**Request Payload**:
```json
{
  "syllabus": "Topic or syllabus",
  "num_questions": 5,
  "difficulty": "easy" // or "medium", "hard"
}
```

**Response**:
```json
{
  "request_id": "unique-request-id",
  "mcq": [
    {
      "id": "unique-question-id",
      "question": "Question text",
      "options": "Option A\nOption B\nOption C\nOption D",
      "answer": "Correct Option",
      "explanation": "Explanation text"
    }
  ]
}
```

---

### 6. **Generate Fill-in-the-Blanks**

**Endpoint**: `/generate-fill-in-the-blanks/`  
**Method**: `POST`  
**Description**: Generates fill-in-the-blank questions based on a syllabus.  

**Request Payload**:
```json
{
  "syllabus": "Topic or syllabus",
  "num_questions": 5,
  "difficulty": "easy" // or "medium", "hard"
}
```

**Response**:
```json
{
  "request_id": "unique-request-id",
  "fill_in_the_blanks": [
    {
      "id": "unique-question-id",
      "question": "Question text with blanks",
      "answer": "Correct Answer",
      "explanation": "Explanation text"
    }
  ]
}
```

---

### 7. **Generate True/False Questions**

**Endpoint**: `/generate-true-false/`  
**Method**: `POST`  
**Description**: Generates true/false questions based on a syllabus.  

**Request Payload**:
```json
{
  "syllabus": "Topic or syllabus",
  "num_questions": 5,
  "difficulty": "easy" // or "medium", "hard"
}
```

**Response**:
```json
{
  "request_id": "unique-request-id",
  "true_false_questions": [
    {
      "id": "unique-question-id",
      "question": "True/False question text",
      "answer": "True/False",
      "explanation": "Explanation text"
    }
  ]
}
```

---

### 8. **Generate Matching Questions**

**Endpoint**: `/generate-matching-questions/`  
**Method**: `POST`  
**Description**: Generates matching questions based on a syllabus.  

**Request Payload**:
```json
{
  "syllabus": "Topic or syllabus",
  "num_questions": 5,
  "difficulty": "easy" // or "medium", "hard"
}
```

**Response**:
```json
{
  "request_id": "unique-request-id",
  "questions": [
    {
      "question_id": "unique-question-id",
      "column1": ["Item 1", "Item 2", "Item 3"],
      "column2": ["Match 1", "Match 2", "Match 3"],
      "answers": {
        "Item 1": "Match 2",
        "Item 2": "Match 1",
        "Item 3": "Match 3"
      }
    }
  ]
}
```

---

### Notes
1. **Error Handling**:
   - All endpoints may return an error response in the format:
     ```json
     {
       "detail": "Error message"
     }
     ```

2. **Request ID**:
   - Each response includes a `request_id` header for tracking purposes.

3. **File Upload**:
   - Supported file formats:
     - Text files (`.pdf`, `.docx`, `.txt`)
     - Audio files (`.mp3`, `.wav`, `.m4a`)
     - Video files (`.mp4`, `.mkv`, `.avi`)

