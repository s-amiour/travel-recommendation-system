FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend/ codebase (detects dockerfile's location folder is and copies all files in it)
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Boot up the Streamlit server
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]