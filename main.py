import os, subprocess, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. إعدادات الكروم لكسر حاجز السواد
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=1280x720')
opts.add_argument('--autoplay-policy=no-user-gesture-required')
# إعدادات سرية لإجبار الرندر في السيرفرات
opts.add_argument('--disable-features=CalculateNativeWinOcclusion')
opts.add_argument('--force-color-profile=srgb')

driver = webdriver.Chrome(options=opts)
url = "https://meja.do.am/asd/obs1.html"
driver.get(url)

print("🌐 الموقع بيفتح.. بنشغل محرك الحركة لإجبار الرندر...")
time.sleep(20)

# 🚀 الحركة الذكية: سكريبت بيخلي الصفحة "تتهز" بسيط جداً عشان الـ AI والكروم ميبطلوش رندر
driver.execute_script("""
    setInterval(() => {
        window.scrollBy(0, 1);
        window.scrollBy(0, -1);
    }, 50);
""")

RTMP_KEY = os.environ.get('RTMP_KEY')

# 2. محرك البث الجبار (60 FPS + 5000k)
# رفعنا thread_queue_size لـ 1024 عشان يستوعب الـ 5000k
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '1024',
    '-f', 'x11grab', '-framerate', '60', '-video_size', '1280x720', '-i', ':99.0',
    '-f', 'pulse', '-i', 'default',
    '-c:v', 'libx264', 
    '-preset', 'ultrafast',   # لازم الترا فاست عشان المعالج ميهنجش في الـ 60 فريم
    '-tune', 'zerolatency', 
    '-b:v', '5000k',          # البت ريت المطلوب
    '-minrate', '5000k', 
    '-maxrate', '5000k', 
    '-bufsize', '10000k', 
    '-pix_fmt', 'yuv420p', 
    '-g', '120', 
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

print("📡 انطلقنا بـ 5000k.. راقب الأرقام دلوقتي!")
process = subprocess.Popen(ffmpeg_cmd)

try:
    time.sleep(20700) # 5.7 hours
except:
    pass
finally:
    driver.quit()
