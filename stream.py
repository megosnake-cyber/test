import os, subprocess, time, requests
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- إعدادات التحكم عن بعد (تأكد من دقة البيانات) ---
GITHUB_USER = "megosnake-cyber" 
REPO_NAME = "ضع_اسم_المستودع_هنا" 
URL_FILE_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/url.txt"

def get_remote_url():
    try:
        # إضافة رقم عشوائي (Timestamp) لمنع المتصفح من جلب نسخة قديمة مخزنة
        response = requests.get(f"{URL_FILE_RAW}?t={int(time.time())}")
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return None

# 1. تشغيل الشاشة الوهمية (المقاس العمودي 720x1280)
disp = Display(visible=0, size=(720, 1280), backend='xvfb')
disp.start()
os.environ['DISPLAY'] = ":" + str(disp.display)

# 2. إعدادات الكروم (إخفاء العناصر العلوية)
opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=720,1280')
opts.add_argument('--hide-scrollbars')
# 🟢 وضع الكشك: يفتح المتصفح بملء الشاشة ويخفي شريط الرابط والتبويبات
opts.add_argument('--kiosk') 
opts.add_argument('--autoplay-policy=no-user-gesture-required')

driver = webdriver.Chrome(options=opts)

# البداية بأول رابط موجود في url.txt
current_url = get_remote_url() or "https://meja.do.am/asd/obs1.html"
driver.get(current_url)

RTMP_KEY = os.environ.get('RTMP_KEY')

# 3. محرك البث مع ميزة "القص الذكي"
# شرح الفلتر: crop=العرض:الطول:البداية_من_اليسار:البداية_من_الأعلى
# هنا قمنا بقص أول 70 بكسل من الأعلى (شريط العنوان) ثم إعادة تكبير الصورة لملء 720x1280
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-thread_queue_size', '4096',
    '-f', 'x11grab', '-framerate', '60', '-video_size', '720x1280', '-i', os.environ['DISPLAY'],
    '-f', 'pulse', '-i', 'default',
    # 🟢 الفلتر السحري: يقص الجزء العلوي (70 بكسل) ويمط الصورة لتناسب يوتيوب
    '-vf', 'crop=720:1210:0:70,scale=720:1280', 
    '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency', 
    '-b:v', '5000k', '-maxrate', '5000k', '-bufsize', '10000k',
    '-pix_fmt', 'yuv420p', '-g', '120', 
    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
    '-f', 'flv', f"rtmp://a.rtmp.youtube.com/live2/{RTMP_KEY}"
]

process = subprocess.Popen(ffmpeg_cmd)
print(f"📡 البث بدأ عمودياً وبدون حواف علوية على رابط: {current_url}")

# 🔄 حلقة التحكم الذكية (تحديث المحتوى بدون قطع البث)
try:
    start_time = time.time()
    # يعمل لمدة 5.7 ساعات (مهلة GitHub القصوى)
    while (time.time() - start_time) < 20700: 
        time.sleep(60) # يفحص الرابط كل دقيقة واحدة
        
        new_url = get_remote_url()
        if new_url and new_url != current_url:
            print(f"🔄 تغيير المحتوى إلى: {new_url}")
            driver.get(new_url)
            current_url = new_url
            time.sleep(5)
            # إجبار المتصفح على الاستمرار في الرندر
            driver.execute_script("window.scrollBy(0, 1); window.scrollBy(0, -1);")
            
except Exception as e:
    print(f"❌ خطأ أثناء البث: {e}")
finally:
    driver.quit()
    disp.stop()
