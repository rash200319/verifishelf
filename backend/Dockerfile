FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium + its OS-level deps for the real headless-browser screenshot
# layer (enforcement letter evidence capture) -- playwright the Python
# package alone does not ship the browser binary.
RUN playwright install --with-deps chromium

COPY . .

# Convert Windows line endings (CRLF) to Unix line endings (LF) for entrypoint.sh
# and make it executable.
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
