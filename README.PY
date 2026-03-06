# --- התקנת ספריות ---
!pip install -U yt-dlp gspread google-auth google-auth-oauthlib google-auth-httplib2 --quiet

from google.colab import auth, drive
import gspread
import yt_dlp
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# --- 1. Auth ל‑Google APIs ---
auth.authenticate_user()
creds, _ = default()

# --- 2. Mount ל‑Drive ---
drive.mount('/content/drive', force_remount=True)

# --- 3. פתיחת גיליון לפי ID ---
SHEET_ID = "1sL2qvb0j_O95fjqZzrXHnkc8qv_S52DmHd343xQn06E"
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET_ID).sheet1
data = sh.get_all_values()

if len(data) < 2:
    print("אין שורות חדשות להורדה בטבלה.")
else:
    print("✅ החיבור לגיליון הצליח!")

# --- 4. מיפוי הכותרות שלך ---
headers = [h.strip().lower() for h in data[0]]

mapping = {}
for idx, h in enumerate(headers):
    if h in ["כתובת המייל לקובץ החוזר"]:
        mapping["email"] = idx
    if h in ["קישור ליוטיוב"]:
        mapping["url"] = idx
    if h in ["פורמט ההורדה"]:
        mapping["format"] = idx
    if h in ["סטטוס", "status"]:  # אם אין, נוציא ריק ונעדכן לאחר ההורדה
        mapping["status"] = idx

# אם אין עמודת status, ניצור אותה
if "status" not in mapping:
    sh.update_cell(1, len(headers)+1, "Status")
    mapping["status"] = len(headers)

# --- Drive API handle ---
drive_service = build('drive', 'v3', credentials=creds)

# --- תקיית הורדה בדרייב ---
DOWNLOAD_FOLDER = "/content/drive/MyDrive/הורדה מיוטיוב"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# --- 5. עיבוד כל הבקשות ---
for i, row in enumerate(data[1:], start=2):

    email = row[mapping["email"]].strip()
    url   = row[mapping["url"]].strip()
    fmt   = row[mapping["format"]].strip().lower()
    status_val = row[mapping["status"]].strip() if len(row) > mapping["status"] else ""

    if status_val.lower() == "done":
        continue

    print(f"\n✨ מטפל בבקשה: {email}")
    print(f"URL: {url}  |  Format: {fmt}")

    try:
        # --- הורדה עם yt-dlp ---
        out_template = f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s"

        if "mp3" in fmt:
            ydl_opts = {
                "outtmpl": out_template,
                "format": "bestaudio",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }
        else:
            ydl_opts = {
                "outtmpl": out_template,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        print("⬇️ הורדה הושלמה!")

        # --- העלאה ל‑Drive + שיתוף ---
        media = MediaFileUpload(filename, resumable=True)
        uploaded = drive_service.files().create(
            body={"name": os.path.basename(filename)},
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded.get("id")

        # שיתוף לכתובת המייל
        permission = {
            "type": "user",
            "role": "reader",
            "emailAddress": email
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()

        print(f"📤 שותף בהצלחה עם {email}")

        # --- עדכון סטטוס בגיליון ---
        sh.update_cell(i, mapping["status"]+1, "DONE")

    except Exception as e:
        print(f"❌ שגיאה בשורה {i}: {e}")

print("\n🎉 כל הבקשות טופלו.")
