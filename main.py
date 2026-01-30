import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures

SOURCES = [
    "https://raw.githubusercontent.com/skid9000/all-iptv-links/main/premium.m3u",
    "https://raw.githubusercontent.com/billyskid/IPTV-Premium/main/premium.m3u",
    "https://raw.githubusercontent.com/T-IPTV/T-IPTV-Free/main/T-IPTV.m3u",
    "https://raw.githubusercontent.com/Moebis/TV/master/playlist.m3u",
    "https://iptv-org.github.io/iptv/index.m3u"
]

KEYWORDS = ["HD", "FHD", "1080P", "720P", "BEIN", "SSC", "OSN", "SKY", "CANAL", "SPORT", "MOVIE", "VIP"]

def create_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Range": "bytes=0-2048" # رفعنا النطاق قليلاً لضمان جلب أول قطعتين
    })
    return session

def is_live(session, url):
    """فحص عميق (Deep Analysis) لضمان تدفق البيانات الفعلي"""
    url_lower = url.lower()
    if not any(x in url_lower for x in [".m3u8", "live", "stream", "udp", "ts", "ch", "mkv", "mp4"]):
        return False
        
    try:
        # رفع الـ timeout لـ 8 ثوانٍ لإعطاء فرصة للسيرفرات البطيئة في الـ Buffering
        with session.get(url, timeout=8, stream=True, allow_redirects=True) as r:
            ctype = r.headers.get('Content-Type', '').lower()
            
            if r.status_code in (200, 206) and "html" not in ctype:
                # حل احترافي: التأكد من وصول القطعة الثانية لضمان استمرارية البث
                for i, _ in enumerate(r.iter_content(chunk_size=128)):
                    if i >= 1: # إذا استلمنا أكثر من Chunk واحد
                        return True
    except:
        pass
    return False

def hunt_and_organize_premium():
    sess = create_session()
    raw_channels = []
    seen_links = set()

    print("📡 جاري استخراج الروابط مع حماية ضد الـ Rate Limit...")
    for src in SOURCES:
        try:
            r = sess.get(src, timeout=20)
            # حماية إضافية ضد صفحات الخطأ من جيت هاب
            if "html" in r.headers.get("Content-Type", "").lower():
                print(f"⚠️ تخطي المصدر {src} بسبب Rate Limit (HTML response)")
                continue
                
            lines = r.text.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    info = lines[i]
                    link = lines[i+1].strip() if i+1 < len(lines) else ""
                    
                    if link.startswith("http") and link not in seen_links:
                        if not KEYWORDS or any(k in info.upper() for k in KEYWORDS):
                            seen_links.add(link)
                            raw_channels.append({"info": info, "link": link})
        except: continue

    print(f"🔎 فحص {len(raw_channels)} قناة (Deep-Check Mode)...")
    
    final_list = ['#EXTM3U x-tvg-url="http://www.teleguide.info/download/new3/jtv.zip"\n']
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_ch = {executor.submit(is_live, sess, ch['link']): ch for ch in raw_channels}
        
        for future in concurrent.futures.as_completed(future_to_ch):
            ch = future_to_ch[future]
            if future.result():
                final_list.append(f"{ch['info']}\n{ch['link']}\n")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(final_list)
    
    working = (len(final_list) - 1) // 2
    print(f"✅ تم الانتهاء! القنوات المؤكدة: {working}")
    
    raw_channels.clear()
    seen_links.clear()
    final_list.clear()

if __name__ == "__main__":
    hunt_and_organize_premium()

