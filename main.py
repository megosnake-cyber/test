import os
import subprocess
import time
import requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- 🛠️ إعدادات التحكم الخاصة بموقعك ---
# ضع هنا رابط الملف الموجود على سيرفرك الخاص
MY_WEBSITE_CONTROL = "https://meja.do.am/asd/url.txt" 
DEFAULT_URL = "https://meja.do.am/asd/obs1.html"

def get_url_from_my_site():
    """جلب الرابط من سيرفرك الخاص وتجاوز الكاش"""
    try:
        # إضافة t= لتجنب تخزين السيرفر للنسخة القديمة (Cache)
        response = requests.get(f"{MY_WEBSITE_CONTROL}?t={int(time.time())}", timeout=5)
        if response.status_code == 200:
            new_link = response.text.strip()
            if new_link.startswith("http"):
                return new_link
    except Exception as e:
        print(f"⚠️ تعذر الاتصال بموقعك: {e}")
    return None

# 1. تشغيل الشاشة الوهمية بمقاس الطول (Portrait)
disp = Display(visible=0, size=(720, 1280), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم (وضع الكشك + ملئ الشاشة الكاملة)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1280') 
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required')
# الكود السحري لإخفاء كل شيء (الروابط، القوائم، الأزرار)
opts.add_argument('--kiosk') 

driver = webdriver.Chrome(options=opts)

# البدء بالرابط الموجود حالياً على موقعك
current_url = get_url_from_my_site() or DEFAULT_URL
print(f"🌐 جاري فتح الرابط الأول: {current_url}")
driver.get(current_url)

print("⌛ استقرار الصوت لمدة 30 ثانية...")
time.sleep(30)

RTMP_KEY = os.environ.get('RTMP_KEY')

# 3. محرك البث FFmpeg (جودة عالية 60 فريم)
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

process = subprocess.Popen(ffmpeg_cmd)

try:
    print("🚀 البث يعمل الآن.. سأراقب موقعك كل 10 ثوانٍ لأي تغيير...")
    while True:
        # فحص موقعك بحثاً عن رابط جديد
        target_url = get_url_from_my_site()
        
        if target_url and target_url != current_url:
            print(f"🔔 تم تغيير الرابط في موقعك إلى: {target_url}")
            try:
                driver.get(target_url)
                current_url = target_url
                print("✅ تم تحديث الشاشة في البث بنجاح")
            except Exception as e:
                print(f"❌ فشل تحديث المتصفح: {e}")
        
        time.sleep(10) # سرعة الفحص (يمكنك تقليلها لـ 5 ثوانٍ لسرعة أكبر)

except KeyboardInterrupt:
    print("🛑 إيقاف البث...")
finally:
    if 'process' in locals(): process.terminate()
    driver.quit()
    disp.stop()
