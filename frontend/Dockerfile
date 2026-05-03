FROM python:3.9-slim

# Set working directory
WORKDIR /frontend

# Copy requirements and install
COPY requirements.txt /frontend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend/ codebase (detects dockerfile's location folder is and copies all files in it)
COPY . /frontend

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]