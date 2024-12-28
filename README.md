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

### 2. Install dependencies

Make sure you have Python and pip installed, then install the required dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Run the application

To start the FastAPI app, use Uvicorn to run the server:

```bash
uvicorn main:app --reload
```

This command will start a local development server. The `--reload` flag enables automatic reloading when you make changes to the code.

### 4. Access the API documentation

Once the server is running, you can access the interactive API documentation at:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

This page provides an easy way to explore and test the available API endpoints.
```
