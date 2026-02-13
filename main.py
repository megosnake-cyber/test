import os
import subprocess
import time
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- إعدادات أساسية ---
DEFAULT_URL = "https://meja.do.am/asd/obs1.html"
URL_FILE = "url.txt"

def get_valid_url():
    """تقرأ الرابط وتتأكد أنه صالح 100% للسيلينيوم"""
    try:
        if os.path.exists(URL_FILE):
            with open(URL_FILE, "r") as f:
                link = f.read().strip()
                if link.startswith("http"):
                    return link
                elif len(link) > 3: # إذا كان رابط بدون http مثل google.com
                    return "https://" + link
    except Exception as e:
        print(f"⚠️ فشل قراءة الملف: {e}")
    
    return DEFAULT_URL # العودة للرابط الافتراضي في حال الفشل

# 1. تشغيل الشاشة الوهمية
disp = Display(visible=0, size=(720, 1280), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم (ملئ الشاشة تماماً)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1280') 
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required')
opts.add_argument('--kiosk') # هذا هو وضع ملئ الشاشة الحقيقي

driver = webdriver.Chrome(options=opts)

# البدء بأول رابط متاح
current_url = get_valid_url()
print(f"🚀 محاولة فتح الرابط: {current_url}")
driver.get(current_url)

print("⌛ ننتظر 30 ثانية لاستقرار الصوت...")
time.sleep(30)

RTMP_KEY = os.environ.get('RTMP_KEY')

# 3. محرك البث FFmpeg
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-framerate', '60', '-video_size', '720x1280', '-i', os.environ['DISPLAY'],
    '-f', 'pulse', '-i', 'default',
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '5000k', '-maxrate', '5000k', '-bufsize', '10000k',
    '-pix_fmt', 'yuv420p', '-g', '120', 
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

print(f"📡 بدأ البث المباشر...")
process = subprocess.Popen(ffmpeg_cmd)

try:
    # حلقة المراقبة والتحديث الفوري
    while True:
        target_url = get_valid_url()
        
        if target_url != current_url:
            print(f"🔄 تغيير الرابط إلى: {target_url}")
            try:
                driver.get(target_url)
                current_url = target_url
            except Exception as e:
                print(f"❌ خطأ أثناء الانتقال للرابط الجديد: {e}")
        
        time.sleep(10) # فحص الملف كل 10 ثوانٍ

except KeyboardInterrupt:
    print("🛑 تم الإيقاف")
finally:
    if 'process' in locals(): process.terminate()
    driver.quit()
    disp.stop()
