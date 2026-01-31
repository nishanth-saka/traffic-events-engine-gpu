FROM python:3.11-slim

WORKDIR /app
COPY . .

# CMD ["python", "-c", "print('🔥 PYTHON CONTAINER STARTED'); import os; print('PORT=', os.getenv('PORT'))"]
CMD ["python", "-m", "app.main"]

