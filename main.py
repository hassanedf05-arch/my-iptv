Import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import datetime
import os

# 🌍 المصادر العالمية + Premium + قنوات عربية ودولية
SOURCES = {
    "world": [
        "https://iptv-org.github.io/iptv/index.m3u",
    ],
    "ar": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ar.m3u"
    ],
    "us": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u"
    ],
    "uk": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u"
    ],
    "fr": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fr.m3u"
    ],
    "it": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/it.m3u"
    ],
    "de": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/de.m3u"
    ],
    "es": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/es.m3u"
    ],
    "tr": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tr.m3u"
    ],
    "br": [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u"
    ],
    "premium": [
        "https://raw.githubusercontent.com/skid9000/all-iptv-links/main/premium.m3u"
    ]
}

def create_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Range": "bytes=0-2048"
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

def collect_channels(sess, urls):
    """جمع كل القنوات من قائمة المصادر"""
    raw_channels = []
    seen_links = set()
    for src in urls:
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
    return raw_channels

def save_m3u(filename, channels):
    with open(filename, "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url="http://www.teleguide.info/download/new3/jtv.zip"\n')
        for ch in channels:
            f.write(f"{ch['info']}\n{ch['link']}\n")

def main():
    sess = create_session()
    os.makedirs("playlists", exist_ok=True)
    dashboard_counts = {}

    for category, urls in SOURCES.items():
        print(f"📡 معالجة قنوات {category}...")
        raw_channels = collect_channels(sess, urls)
        print(f"🔎 عدد الروابط المكتشفة: {len(raw_channels)}. جاري التحقق من عملها...")

        final_channels = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_map = {executor.submit(is_live, sess, ch["link"]): ch for ch in raw_channels}
            for future in concurrent.futures.as_completed(future_map):
                ch = future_map[future]
                if future.result():
                    final_channels.append(ch)

        filename = os.path.join("playlists", f"{category}.m3u")
        save_m3u(filename, final_channels)
        dashboard_counts[category] = len(final_channels)
        print(f"✅ {category}: تم حفظ {len(final_channels)} قناة شغالة")

    # إنشاء Dashboard HTML
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"<html><body style='background:#121212;color:white;font-family:sans-serif;text-align:center;'>"
    html += f"<h1>🌍 Ultra Premium IPTV Dashboard</h1>"
    for cat, count in dashboard_counts.items():
        html += f"<p style='font-size:24px;'>{cat.upper()}: <span style='color:#00ff88;'>{count}</span> قناة</p>"
    html += f"<p style='color:#777;'>آخر تحديث: {now}</p></body></html>"

    with open("playlists/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ اكتملت جميع الملفات والقنوات جاهزة في مجلد 'playlists'")

if __name__ == "__main__":
    main()
