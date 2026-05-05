FROM python:3.11-slim

WORKDIR /backend

# Copy requirements file and install dependencies
# . instead of /backend/requirements.txt as target because we already set WORKDIR /backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY infra ./infra
COPY app ./app

# grant execute permissions to the file
RUN chmod +x ./infra/entrypoint.sh

EXPOSE 8000

# Run app using uvicorn
CMD ["./infra/entrypoint.sh"]