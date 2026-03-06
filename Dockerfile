FROM python:3.11-slim

# System libraries required by WeasyPrint (PDF) and Playwright/Chromium (screenshots)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint deps
    libglib2.0-0 \
    libgobject-2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libharfbuzz0b \
    libfontconfig1 \
    shared-mime-info \
    # Chromium deps for Playwright screenshots
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libx11-xcb1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

COPY . .

# Add src/ to Python path so retina package is importable
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
