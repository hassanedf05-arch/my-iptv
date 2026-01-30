import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import datetime
import os

# المصادر العالمية
SOURCES = [
    "https://raw.githubusercontent.com/skid9000/all-iptv-links/main/premium.m3u",
    "https://raw.githubusercontent.com/billyskid/IPTV-Premium/main/premium.m3u",
    "https://raw.githubusercontent.com/T-IPTV/T-IPTV-Free/main/T-IPTV.m3u",
    "https://iptv-org.github.io/iptv/index.m3u" # مصدر ضخم لزيادة العدد
]

# اجعلها فارغة [] إذا أردت جلب كل القنوات المتاحة لرفع العدد
KEYWORDS = ["HD", "FHD", "BEIN", "SSC", "OSN", "SKY", "SPORT", "MOVIE", "VIP"]

def create_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Range": "bytes=0-1024" # طلب جزء صغير لسرعة الفحص
    })
    return session

def is_live(session, url):
    """فحص متوازن: تقليل الصرامة قليلاً لزيادة عدد القنوات المقبولة"""
    if not any(x in url.lower() for x in [".m3u8", "live", "stream", "ts", "ch"]):
        return False
    try:
        # تقليل الـ timeout لـ 5 ثوانٍ لتسريع العملية الإجمالية
        with session.get(url, timeout=5, stream=True, allow_redirects=True) as r:
            ctype = r.headers.get('Content-Type', '').lower()
            if r.status_code in (200, 206) and "html" not in ctype:
                # الاكتفاء بـ أول Chunk لضمان وجود بث (يرفع العدد المقبول)
                for _ in r.iter_content(chunk_size=128):
                    return True
    except: pass
    return False

def generate_dashboard(count):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>IPTV Status</title>
    <style>
        body {{ background: #121212; color: white; text-align: center; font-family: sans-serif; padding-top: 50px; }}
        .card {{ background: #1e1e1e; display: inline-block; padding: 40px; border-radius: 20px; border: 1px solid #00ff88; }}
        .num {{ font-size: 60px; color: #00ff88; font-weight: bold; }}
        .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #00ff88; color: black; text-decoration: none; border-radius: 5px; }}
    </style></head>
    <body>
        <div class="card">
            <h1>🚀 رادار القنوات الحية</h1>
            <div class="num">{count}</div>
            <p>قناة شغالة تم فحصها الآن</p>
            <a href="playlist.m3u" class="btn">تحميل القائمة M3U</a>
            <p style="color: #666; font-size: 12px;">تحديث: {now}</p>
        </div>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    sess = create_session()
    raw_channels = []
    seen = set()

    for src in SOURCES:
        try:
            r = sess.get(src, timeout=15)
            [span_1](start_span)if "html" in r.headers.get("Content-Type", "").lower(): continue[span_1](end_span)
            lines = r.text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    info, link = lines[i], lines[i+1].strip() if i+1 < len(lines) else ""
                    if link.startswith("http") and link not in seen:
                        # فلتر الكلمات المفتاحية
                        [span_2](start_span)if not KEYWORDS or any(k in info.upper() for k in KEYWORDS):[span_2](end_span)
                            seen.add(link)
                            raw_channels.append({"info": info, "link": link})
        except: continue

    [span_3](start_span)final_m3u = ['#EXTM3U x-tvg-url="http://www.teleguide.info/download/new3/jtv.zip"\n'][span_3](end_span)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(is_live, sess, ch['link']): ch for ch in raw_channels}
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                ch = futures[f]
                final_m3u.append(f"{ch['info']}\n{ch['link']}\n")

    [span_4](start_span)with open("playlist.m3u", "w", encoding="utf-8") as f:[span_4](end_span)
        f.writelines(final_m3u)
    
    count = (len(final_m3u) - 1) // 2
    generate_dashboard(count)
    print(f"✅ تم صيد {count} قناة بنجاح.")

if __name__ == "__main__":
    main()

