import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import datetime

# المصادر
SOURCES = [
    "https://raw.githubusercontent.com/skid9000/all-iptv-links/main/premium.m3u",
    "https://raw.githubusercontent.com/billyskid/IPTV-Premium/main/premium.m3u",
    "https://raw.githubusercontent.com/T-IPTV/T-IPTV-Free/main/T-IPTV.m3u",
    "https://iptv-org.github.io/iptv/index.m3u"
]

# لزيادة عدد القنوات، اجعل هذه القائمة فارغة []
KEYWORDS = [] # تم إفراغها بناءً على طلبك لزيادة العدد

def create_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0", "Range": "bytes=0-1024"})
    return session

def is_live(session, url):
    try:
        with session.get(url, timeout=5, stream=True) as r:
            if r.status_code in (200, 206) and "html" not in r.headers.get('Content-Type', ''):
                return True
    except: pass
    return False

# هذه الدالة هي التي ستحل مشكلة الخطأ في الـ Action
def generate_html(count):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"<html><body style='background:#121212;color:white;text-align:center;font-family:sans-serif;'>"
    html += f"<h1>🚀 IPTV Dashboard</h1><div style='font-size:50px;color:#00ff88;'>{count}</div>"
    html += f"<p>قناة شغالة الآن</p><p style='color:#666;'>آخر تحديث: {now}</p></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    sess = create_session()
    raw_ch = []
    seen = set()
    for src in SOURCES:
        try:
            lines = sess.get(src, timeout=15).text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    info, link = lines[i], lines[i+1].strip()
                    if link.startswith("http") and link not in seen:
                        seen.add(link)
                        raw_ch.append({"info": info, "link": link})
        except: continue

    final = ['#EXTM3U\n']
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(is_live, sess, ch['link']): ch for ch in raw_ch}
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                c = futures[f]
                final.append(f"{c['info']}\n{c['link']}\n")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(final)
    
    # استدعاء دالة إنشاء الملف لإصلاح خطأ الـ Action
    generate_html((len(final)-1)//2)

if __name__ == "__main__":
    main()

