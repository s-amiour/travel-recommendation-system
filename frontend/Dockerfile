FROM python:3.11-slim

# Set working directory
WORKDIR /frontend

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend/ codebase (detects dockerfile's location folder is and copies all files in it)
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]