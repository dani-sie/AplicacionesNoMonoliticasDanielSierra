FROM python:3.12-slim
WORKDIR /service
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY app ./app
COPY db ./db
CMD ["uvicorn", "app.interfaces.http:app", "--host", "0.0.0.0", "--port", "8000"]
