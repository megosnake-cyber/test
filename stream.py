import os, subprocess, time, requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- 🛠️ إعدادات التحكم عن بعد (تأكد من كتابة اسم المستودع الجديد) ---
GITHUB_USER = "megosnake-cyber" 
REPO_NAME = "اسم-المستودع-بتاعك" 
URL_FILE_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/url.txt"

def get_remote_data():
    """يجلب الإعدادات والروابط من الملف النصي"""
    try:
        # إضافة t لمنع الكاش وجلب التعديل فوراً
        response = requests.get(f"{URL_FILE_RAW}?t={int(time.time())}")
        if response.status_code == 200:
            lines = response.text.splitlines()
            urls = []
            interval = 60  # الوقت الافتراضي
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if line.startswith('interval='):
                    try: interval = int(line.split('=')[1])
                    except: pass
                elif line.startswith('http'):
                    urls.append(line)
            return urls, interval
    except:
        pass
    return [], 60

# 1️⃣ إعداد الشاشة الوهمية (720x1120)
disp = Display(visible=0, size=(720, 1120), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2️⃣ إعدادات الكروم (وضع ملء الشاشة الكامل Kiosk)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1120')
opts.add_argument('--window-position=0,0')
opts.add_argument('--autoplay-policy=no-user-gesture-required')
opts.add_argument('--kiosk')  # إخفاء شريط العنوان والتبويبات
opts.add_argument('--hide-scrollbars')

driver = webdriver.Chrome(options=opts)

# جلب البيانات وبدء أول رابط
all_urls, switch_interval = get_remote_data()
current_url = all_urls[0] if all_urls else "https://meja.do.am/asd/obs1.html"
driver.get(current_url)

RTMP_KEY = os.environ.get('RTMP_KEY')

# 3️⃣ محرك البث (تم استبدال 'pulse' بمولد صوت صامت 'lavfi')
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-framerate', '60', '-video_size', '720x1120', '-i', os.environ['DISPLAY'],
    # 👇 هذا هو التعديل السحري: توليد صوت صامت لمنع انهيار السكريبت
    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '4500k', '-maxrate', '4500k', '-bufsize', '9000k',
    '-pix_fmt', 'yuv420p', '-g', '120', 
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ بمقاس 720x1120 في وضع ملء الشاشة.")

# 🔄 حلقة التبديل الذكي من ملف url.txt
try:
    start_time = time.time()
    url_index = 0
    while (time.time() - start_time) < 20700: # يعمل لمدة 5.7 ساعة
        all_urls, switch_interval = get_remote_data()
        
        if all_urls:
            target_url = all_urls[url_index % len(all_urls)]
            print(f"🔄 تبديل إلى: {target_url} | الانتظار: {switch_interval} ثانية")
            
            driver.get(target_url)
            time.sleep(5)
            driver.execute_script("document.body.style.overflow = 'hidden';")
            
            url_index += 1
            # الانتظار بناءً على الوقت المحدد في الملف
            time.sleep(max(5, switch_interval - 5))
        else:
            time.sleep(10)
            
except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    driver.quit()
    disp.stop()
