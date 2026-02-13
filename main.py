import os
import subprocess
import time
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- وظائف مساعدة ---
def validate_url(url):
    """تتأكد من أن الرابط يبدأ ببروتوكول صحيح ولا يسبب خطأ"""
    if not url or len(url.strip()) < 5:
        return None
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return url

def get_url_from_file():
    """تقرأ الرابط وتتأكد من صلاحيته"""
    try:
        if os.path.exists("url.txt"):
            with open("url.txt", "r") as f:
                raw_url = f.read().strip()
                return validate_url(raw_url)
    except Exception as e:
        print(f"⚠️ خطأ أثناء قراءة الملف: {e}")
    return None

# 1. تشغيل الشاشة الوهمية
disp = Display(visible=0, size=(720, 1280), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم (وضع الكشك + ملئ الشاشة)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1280') 
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required')
opts.add_argument('--kiosk') # لإخفاء شريط العنوان تماماً

driver = webdriver.Chrome(options=opts)

# تحديد الرابط الأول (إما من الملف أو رابط افتراضي)
default_url = "https://meja.do.am/asd/obs1.html"
current_url = get_url_from_file() or default_url

print(f"🌐 الرابط الذي سيتم فتحه: {current_url}")
try:
    driver.get(current_url)
except Exception as e:
    print(f"❌ فشل فتح الرابط الأولي، يتم العودة للافتراضي: {e}")
    driver.get(default_url)

print("⌛ ننتظر 30 ثانية لضمان استقرار الصوت...")
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

print(f"📡 بدأ البث على شاشة {os.environ['DISPLAY']}")
process = subprocess.Popen(ffmpeg_cmd)

try:
    # حلقة المراقبة (5 ساعات و 45 دقيقة)
    end_time = time.time() + 20700
    while time.time() < end_time:
        new_url = get_url_from_file()
        
        # إذا كان الرابط في الملف صالحاً ومختلفاً عن الحالي
        if new_url and new_url != current_url:
            print(f"🚀 تحديث الرابط إلى: {new_url}")
            try:
                driver.get(new_url)
                current_url = new_url
            except Exception as e:
                print(f"❌ لم يتمكن المتصفح من فتح الرابط الجديد: {e}")
        
        time.sleep(5)

except KeyboardInterrupt:
    print("🛑 إيقاف يدوي")
finally:
    if 'process' in locals(): process.terminate()
    driver.quit()
    disp.stop()
