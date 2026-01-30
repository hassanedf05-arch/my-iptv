import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import datetime

# 🌍 المصادر العالمية + Premium + القنوات العربية (تمت إضافة الدول المطلوبة)
SOURCES = [
    "https://iptv-org.github.io/iptv/index.m3u",  # أكبر مصدر عالمي
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fr.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/it.m3u", # إيطاليا
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/de.m3u", # ألمانيا
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/es.m3u", # إسبانيا
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u", # تركيا
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u", # البرازيل
    "https://raw.githubusercontent.com/skid9000/all-iptv-links/main/premium.m3u"
]

def create_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Range": "bytes=0-2048"  # أول قطعتين من البث لتأكيد وجوده
    })
    return session

def is_live(session, url):
    """فحص سريع لجميع أنواع القنوات"""
    try:
        r = session.get(url, timeout=8, stream=True, allow_redirects=True)
        ctype = r.headers.get("Content-Type", "").lower()
        if r.status_code in (200, 206) and "html" not in ctype:
            return True
    except:
        pass
    return False

def main():
    sess = create_session()
    raw_channels = []
    seen_links = set()

    print("📡 استخراج كل القنوات من جميع المصادر...")
    for src in SOURCES:
        try:
            r = sess.get(src, timeout=20)
            if "html" in r.headers.get("Content-Type", "").lower():
                continue

            lines = r.text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    info = lines[i]
                    link = lines[i+1].strip() if i+1 < len(lines) else ""

                    if link.startswith("http") and link not in seen_links:
                        seen_links.add(link)
                        raw_channels.append({"info": info, "link": link})
        except:
            continue

    print(f"🔎 فحص {len(raw_channels)} قناة (Live Check)...")
    final_list = ['#EXTM3U x-tvg-url="http://www.teleguide.info/download/new3/jtv.zip"\n']

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_map = {executor.submit(is_live, sess, ch["link"]): ch for ch in raw_channels}

        for future in concurrent.futures.as_completed(future_map):
            ch = future_map[future]
            if future.result():
                final_list.append(f"{ch['info']}\n{ch['link']}\n")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(final_list)

    # إنشاء Dashboard سريع
    count = (len(final_list) - 1) // 2
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""
    <html>
    <body style="background:#121212;color:white;text-align:center;font-family:sans-serif;">
        <h1>🌍 World IPTV Dashboard</h1>
        <div style="font-size:70px;color:#00ff88;">{count}</div>
        <p>قنوات شغالة (مجانية + مدفوعة) حسب المصدر</p>
        <p style="color:#777;">آخر تحديث: {now}</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ انتهى! عدد القنوات الحية: {count}")

if __name__ == "__main__":
    main()

