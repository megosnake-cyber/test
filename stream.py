import os
import subprocess
import time
import requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- 🛠️ إعدادات التحكم عن بعد (عدل اسم المستودع هنا) ---
GITHUB_USER = "megosnake-cyber" 
REPO_NAME = "اسم-المستودع-الجديد" # 👈 ضع اسم المستودع هنا
URL_FILE_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/url.txt"

def get_remote_data():
    try:
        response = requests.get(f"{URL_FILE_RAW}?t={int(time.time())}")
        if response.status_code == 200:
            lines = response.text.splitlines()
            urls, interval = [], 60
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith('interval='):
                    try: interval = int(line.split('=')[1])
                    except: pass
                elif line.startswith('http'): urls.append(line)
            return urls, interval
    except: pass
    return [], 60

# 1️⃣ تشغيل الشاشة الوهمية بمقاس البث (720x1120)
disp = Display(visible=0, size=(720, 1120), backend='xvfb')
disp.start()

# استخراج مسار الشاشة الوهمية التلقائي
display_port = os.environ.get('DISPLAY', ':0')

# 2️⃣ إعدادات الكروم (وضع ملء الشاشة الكامل Kiosk)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1120')
opts.add_argument('--kiosk') # يخفي شريط الروابط والتبويبات نهائياً
opts.add_argument('--hide-scrollbars')

# استخدام WebDriver Manager لضمان التوافق التلقائي مع إصدار كروم بالسيرفر
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

# جلب أول رابط والبدء
all_urls, switch_interval = get_remote_data()
current_url = all_urls[0] if all_urls else "https://google.com"
driver.get(current_url)

RTMP_KEY = os.environ.get('RTMP_KEY')

if not RTMP_KEY:
    print("❌ خطأ: لم يتم العثور على مفتاح البث (RTMP_KEY).")
    driver.quit()
    disp.stop()
    exit(1)

# 3️⃣ محرك FFmpeg (تم إصلاح مشكلة الصوت وتقليل الحمل على المعالج)
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-framerate', '30', '-video_size', '720x1120', '-i', display_port,
    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', # 👈 مسار صوتي صامت لحل مشكلة عدم وجود كارت صوت
    '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', 
    '-b:v', '2500k', '-maxrate', '2500k', '-bufsize', '5000k',
    '-pix_fmt', 'yuv420p', '-g', '60', 
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ بمقاس 720x1120 في وضع ملء الشاشة.")

# 🔄 حلقة التبديل الذكي
try:
    start_time = time.time()
    url_index = 0
    while (time.time() - start_time) < 20700: # يعمل لمدة 5 ساعات و 45 دقيقة (لتجنب إيقاف سيرفرات جيت هاب القسري)
        all_urls, switch_interval = get_remote_data()
        if all_urls:
            target_url = all_urls[url_index % len(all_urls)]
            print(f"🔄 تبديل إلى: {target_url}")
            driver.get(target_url)
            time.sleep(5)
            try:
                driver.execute_script("document.body.style.overflow = 'hidden';")
            except:
                pass
            url_index += 1
            time.sleep(max(5, switch_interval - 5))
        else:
            time.sleep(10)
except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    if 'process' in locals():
        process.terminate()
    driver.quit()
    disp.stop()
