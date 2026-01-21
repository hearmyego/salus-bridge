FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY app/ ./app/

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Expose port
EXPOSE 8000

# Run the application (now as an installed package)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
