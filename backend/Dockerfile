FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /backend

# Copy requirements file and install dependencies
COPY requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir -r /backend/requirements.txt

COPY seed.py /backend/seed.py

# Copy /app codebase (detects dockerfile's location folder is and copies all files in it)
COPY /app /backend/app

# Expose the port fastapi runs on
EXPOSE 8000

# Inject db seed
RUN python /backend/seed.py

# Run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]