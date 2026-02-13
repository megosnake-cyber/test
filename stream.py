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
REPO_NAME = "test" # 👈 تم وضع اسم المستودع الجديد هنا
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

# 1️⃣ تشغيل الشاشة الوهمية بمقاس البث (720x1100)
disp = Display(visible=0, size=(720, 1100), backend='xvfb')
disp.start()

display_port = os.environ.get('DISPLAY', ':0')

# 2️⃣ إعدادات الكروم
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1100')
opts.add_argument('--kiosk')
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required') # 👈 إجبار المتصفح على تشغيل الصوت تلقائياً

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

all_urls, switch_interval = get_remote_data()
current_url = all_urls[0] if all_urls else "https://meja.do.am/asd/obs1.html"
driver.get(current_url)

RTMP_KEY = os.environ.get('RTMP_KEY')

if not RTMP_KEY:
    print("❌ خطأ: لم يتم العثور على مفتاح البث (RTMP_KEY).")
    driver.quit()
    disp.stop()
    exit(1)

# 3️⃣ محرك FFmpeg (مع حل مشكلة تزامن الصوت والصورة)
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-use_wallclock_as_timestamps', '1', # 👈 توحيد التوقيت للصورة
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-framerate', '30', '-video_size', '720x1100', '-i', display_port,
    '-use_wallclock_as_timestamps', '1', # 👈 توحيد التوقيت للصوت
    '-thread_queue_size', '4096',        # 👈 ذاكرة تخزين مؤقتة للصوت لمنع التقطيع
    '-f', 'pulse', '-i', 'auto_null.monitor',
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', # 👈 تقليل الحمل على المعالج لأقصى درجة
    '-b:v', '2500k', '-maxrate', '2500k', '-bufsize', '5000k',
    '-pix_fmt', 'yuv420p', '-g', '60', '-r', '30',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-af', 'aresample=async=1',          # 👈 فلتر المزامنة الإجبارية للصوت مع الصورة
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ بمقاس 720x1100 مع تفعيل الصوت.")

# 🔄 حلقة التبديل الذكي
try:
    start_time = time.time()
    url_index = 0
    while (time.time() - start_time) < 20700:
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
