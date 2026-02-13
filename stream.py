import os
import subprocess
import time
import requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- 🛠️ إعدادات التحكم عن بعد ---
GITHUB_USER = "megosnake-cyber" 
REPO_NAME = "test"
URL_FILE_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/url.txt"

def get_remote_data():
    try:
        # إضافة طابع زمني دقيق جداً لمنع التخزين المؤقت (Cache)
        response = requests.get(f"{URL_FILE_RAW}?t={time.time()}")
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
display_port = os.environ.get('DISPLAY', ':0')

# 2️⃣ إعدادات الكروم
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1120')
opts.add_argument('--kiosk')
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

# جلب مبدئي
all_urls, switch_interval = get_remote_data()
current_url = all_urls[0] if all_urls else "https://meja.do.am/asd/obs1.html"
driver.get(current_url)

RTMP_KEY = os.environ.get('RTMP_KEY')

if not RTMP_KEY:
    print("❌ خطأ: لم يتم العثور على مفتاح البث (RTMP_KEY).")
    driver.quit()
    disp.stop()
    exit(1)

# 3️⃣ محرك FFmpeg (تم حل مشكلة التزامن تماماً هنا)
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-draw_mouse', '0', '-framerate', '30', '-video_size', '720x1120', '-i', display_port,
    '-thread_queue_size', '4096',
    '-f', 'pulse', '-i', 'auto_null.monitor',
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '2500k', '-maxrate', '2500k', '-bufsize', '5000k',
    '-pix_fmt', 'yuv420p', '-g', '60', '-r', '30',
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-af', 'aresample=async=1', # 👈 مزامنة الصوت
    '-vsync', 'cfr',            # 👈 إجبار إطارات الصورة على الثبات لمنع التأخير
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ بمقاس 720x1120 مع تفعيل الصوت المتزامن.")

# 🔄 حلقة التبديل الذكية واللحظية
try:
    start_time = time.time()
    last_switch_time = time.time()
    current_urls_list = all_urls
    url_index = 0

    while (time.time() - start_time) < 20700:
        new_urls, new_interval = get_remote_data()
        
        # الحالة الأولى: إذا اكتشف السكريبت أنك قمت بتعديل الروابط في GitHub
        if new_urls and new_urls != current_urls_list:
            print(f"⚡ تحديث فوري! تم اكتشاف روابط جديدة...")
            current_urls_list = new_urls
            switch_interval = new_interval
            url_index = 0
            driver.get(current_urls_list[url_index])
            last_switch_time = time.time()
            time.sleep(2)
            try: driver.execute_script("document.body.style.overflow = 'hidden';")
            except: pass

        # الحالة الثانية: إذا لم تتغير الروابط، ولكن انتهى الوقت المحدد (interval)
        elif current_urls_list and (time.time() - last_switch_time) >= switch_interval:
            url_index = (url_index + 1) % len(current_urls_list)
            print(f"⏱️ تبديل تلقائي إلى: {current_urls_list[url_index]}")
            driver.get(current_urls_list[url_index])
            last_switch_time = time.time()
            time.sleep(2)
            try: driver.execute_script("document.body.style.overflow = 'hidden';")
            except: pass
        
        # النوم لمدة 3 ثوانٍ فقط (ليكون الاستشعار لحظياً) بدلاً من النوم طوال فترة الـ interval
        time.sleep(3)

except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    if 'process' in locals():
        process.terminate()
    driver.quit()
    disp.stop()
