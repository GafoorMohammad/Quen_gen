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

