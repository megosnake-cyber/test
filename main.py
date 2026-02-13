import os, subprocess, time
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. تشغيل الشاشة الوهمية بمقاس عمودي (720 عرض × 1280 طول)
# استخدام backend='xvfb' لضمان استقرار الصوت كما في تجربتك الناجحة
disp = Display(visible=0, size=(720, 1280), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم العمودية وإجبار الصوت
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1280') 
opts.add_argument('--hide-scrollbars')
opts.add_argument('--autoplay-policy=no-user-gesture-required')

driver = webdriver.Chrome(options=opts)
url = "https://meja.do.am/asd/obs1.html"
driver.get(url)

print("🌐 الموقع يحمل بالمقاس العمودي.. ننتظر 30 ثانية لضمان الصوت")
time.sleep(30)

RTMP_KEY = os.environ.get('RTMP_KEY')

# 3. محرك البث (60 فريم + 5000 بت ريت + مقاس عمودي)
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-framerate', '60', '-video_size', '720x1280', '-i', os.environ['DISPLAY'],
    '-f', 'pulse', '-i', 'default', # التقاط الصوت الافتراضي
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '5000k', '-maxrate', '5000k', '-bufsize', '10000k',
    '-pix_fmt', 'yuv420p', '-g', '120', 
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

print(f"📡 البث بدأ عمودياً على شاشة {os.environ['DISPLAY']}")
process = subprocess.Popen(ffmpeg_cmd)

try:
    # البث يستمر لمدة 5 ساعات و 45 دقيقة
    time.sleep(20700)
except:
    pass
finally:
    driver.quit()
    disp.stop()
