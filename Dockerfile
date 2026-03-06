# משתמשים בתמונת פייתון רשמית
FROM python:3.10-slim

# התקנת nodejs (כדי ש-yt-dlp יוכל לפצח את החסימות של יוטיוב)
RUN apt-get update && apt-get install -y nodejs && rm -rf /var/lib/apt/lists/*

# העתקת הקבצים לשרת
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# פקודת ההפעלה
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
