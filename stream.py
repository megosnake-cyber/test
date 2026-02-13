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
        # استخدام headers لمنع الكاش نهائياً وجلب الرابط والوقت لحظياً
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(f"{URL_FILE_RAW}?t={time.time()}", headers=headers)
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

# 1️⃣ تشغيل الشاشة الوهمية بنفس أبعاد كودك القديم المظبوط (720x1400)
disp = Display(visible=0, size=(720, 1400), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# جلب مبدئي للبيانات
all_urls, switch_interval = get_remote_data()
current_url = all_urls[0] if all_urls else "https://meja.do.am/asd/obs1.html"

# 2️⃣ إعدادات الكروم (استرجاع وضع التطبيق App Mode السريع من كودك القديم)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1400')
opts.add_argument('--hide-scrollbars')
opts.add_argument(f'--app={current_url}') # 🟢 السر هنا: وضع التطبيق الخفيف
opts.add_argument('--autoplay-policy=no-user-gesture-required')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)
driver.set_window_size(720, 1400)
driver.set_window_position(0, 0)

RTMP_KEY = os.environ.get('RTMP_KEY')

if not RTMP_KEY:
    print("❌ خطأ: لم يتم العثور على مفتاح البث (RTMP_KEY).")
    driver.quit()
    disp.stop()
    exit(1)

# 3️⃣ محرك FFmpeg (كودك القديم حرفياً + دمج المزامنة)
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '8192', # الذاكرة للفيديو فقط كما في كودك المظبوط
    '-f', 'x11grab', '-draw_mouse', '0', '-framerate', '60', '-video_size', '720x1400', '-i', os.environ['DISPLAY'],
    '-f', 'pulse', '-i', 'default', # 🟢 رجعنا للـ default لأنه سيعمل الآن
    '-vf', 'crop=720:1280:0:120', # القص الاحترافي الخاص بك
    '-af', 'aresample=async=1:min_hard_comp=0.100000:first_pts=0', # مزامنة الصوت لحظياً
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '5000k', '-maxrate', '5000k', '-bufsize', '10000k',
    '-pix_fmt', 'yuv420p', '-r', '60', '-vsync', 'cfr', # إجبار ثبات الفريمات
    '-g', '120', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ بمزامنة كاملة. الرابط الحالي: {current_url}")

# 🔄 حلقة التبديل الذكية واللحظية
try:
    start_time = time.time()
    last_switch_time = time.time()
    current_urls_list = all_urls
    url_index = 0

    while (time.time() - start_time) < 20700:
        time.sleep(3) # فحص التحديثات كل 3 ثوانٍ فقط لتكون الاستجابة لحظية
        new_urls, new_interval = get_remote_data()
        
        # إذا تم اكتشاف تغيير في الروابط بملف url.txt
        if new_urls and new_urls != current_urls_list:
            print(f"⚡ تحديث فوري! تم اكتشاف روابط جديدة...")
            current_urls_list = new_urls
            switch_interval = new_interval
            url_index = 0
            driver.get(current_urls_list[url_index])
            last_switch_time = time.time()
            time.sleep(2)
            try: 
                driver.execute_script("window.scrollBy(0, 1); window.scrollBy(0, -1); document.body.style.overflow = 'hidden';")
            except: pass

        # إذا انتهى الوقت المخصص للرابط الحالي (interval)
        elif current_urls_list and (time.time() - last_switch_time) >= switch_interval:
            url_index = (url_index + 1) % len(current_urls_list)
            print(f"⏱️ تبديل تلقائي إلى: {current_urls_list[url_index]}")
            driver.get(current_urls_list[url_index])
            last_switch_time = time.time()
            time.sleep(2)
            try: 
                driver.execute_script("window.scrollBy(0, 1); window.scrollBy(0, -1); document.body.style.overflow = 'hidden';")
            except: pass

except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    if 'process' in locals():
        process.terminate()
    driver.quit()
    disp.stop()
