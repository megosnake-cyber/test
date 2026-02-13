import os, subprocess, time, requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- إعدادات التحكم عن بعد ---
GITHUB_USER = "megosnake-cyber" 
REPO_NAME = "test" 
URL_FILE_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/url.txt"

def get_remote_url():
    try:
        # استخدام headers لمنع الكاش نهائياً وجلب الرابط لحظياً
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(f"{URL_FILE_RAW}?t={int(time.time())}", headers=headers)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return None

# 1. تشغيل الشاشة الوهمية (720x1400)
disp = Display(visible=0, size=(720, 1400), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم (App Mode)
current_url = get_remote_url() or "https://meja.do.am/asd/obs1.html"
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1400')
opts.add_argument('--hide-scrollbars')
opts.add_argument(f'--app={current_url}') 
opts.add_argument('--autoplay-policy=no-user-gesture-required')

driver = webdriver.Chrome(options=opts)
driver.set_window_size(720, 1400)
driver.set_window_position(0, 0)

RTMP_KEY = os.environ.get('RTMP_KEY')

# 3. محرك البث مع ضبط المزامنة (AV Sync Fix)
# أضفنا -af aresample للمزامنة و -vsync cfr لثبات الفريمات
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '8192', # زيادة الذاكرة لمنع التأخير
    '-f', 'x11grab', '-draw_mouse', '0', '-framerate', '60', '-video_size', '720x1400', '-i', os.environ['DISPLAY'],
    '-f', 'pulse', '-i', 'default',
    '-vf', 'crop=720:1280:0:120', # القص الاحترافي
    '-af', 'aresample=async=1:min_hard_comp=0.100000:first_pts=0', # 🟢 مزامنة الصوت لحظياً
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '5000k', '-maxrate', '5000k', '-bufsize', '10000k',
    '-pix_fmt', 'yuv420p', '-r', '60', '-vsync', 'cfr', # 🟢 إجبار ثبات الفريمات
    '-g', '120', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ بمزامنة كاملة. الرابط الحالي: {current_url}")

# 🔄 حلقة فحص الرابط السريعة (كل 5 ثوانٍ)
try:
    start_time = time.time()
    while (time.time() - start_time) < 20700: 
        time.sleep(5) # 🟢 تقليل الانتظار ليكون التغيير شبه لحظي
        
        new_url = get_remote_url()
        if new_url and new_url != current_url:
            print(f"🔄 تغيير لحظي للمحتوى: {new_url}")
            driver.get(new_url)
            current_url = new_url
            time.sleep(2) # وقت بسيط جداً للتحميل
            driver.execute_script("window.scrollBy(0, 1); window.scrollBy(0, -1);")
            
except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    driver.quit()
    disp.stop()
