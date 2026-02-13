import os
import subprocess
import time
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. تشغيل الشاشة الوهمية بمقاس عمودي
disp = Display(visible=0, size=(720, 1280), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم (وضع الكشك لإخفاء الروابط والقوائم)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1280') 
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required')
# الإضافة الأهم لملئ الشاشة بالكامل:
opts.add_argument('--kiosk') 

driver = webdriver.Chrome(options=opts)

# وظيفة لقراءة الرابط من ملف url.txt
def get_url_from_file():
    try:
        if os.path.exists("url.txt"):
            with open("url.txt", "r") as f:
                return f.read().strip()
    except Exception as e:
        print(f"خطأ في قراءة الملف: {e}")
    return None

# البداية برابط افتراضي أو من الملف
current_url = get_url_from_file() or "https://meja.do.am/asd/obs1.html"
driver.get(current_url)

print(f"🌐 الموقع الحالي: {current_url}")
print("⌛ ننتظر 30 ثانية لضمان استقرار الصوت قبل بدء البث...")
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

print(f"📡 بدأت عملية البث على {os.environ['DISPLAY']}")
process = subprocess.Popen(ffmpeg_cmd)

try:
    print("🔄 نظام المراقبة يعمل: قم بتغيير الرابط داخل url.txt لتحديث البث فوراً...")
    
    # حلقة المراقبة (ستعمل لمدة 5 ساعات و 45 دقيقة تقريباً)
    end_time = time.time() + 20700
    while time.time() < end_time:
        new_url = get_url_from_file()
        
        # إذا تغير الرابط في الملف عن الرابط الحالي
        if new_url and new_url != current_url:
            print(f"🚀 تم اكتشاف رابط جديد: {new_url}")
            driver.get(new_url)
            current_url = new_url
        
        time.sleep(5) # التحقق كل 5 ثوانٍ لتوفير الجهد

except KeyboardInterrupt:
    print("🛑 تم إيقاف السكربت يدوياً")
finally:
    process.terminate() # إغلاق FFmpeg
    driver.quit()
    disp.stop()
