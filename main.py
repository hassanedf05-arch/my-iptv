import requests
import re
import concurrent.futures

# مصادر قوية يتم تحديثها عالمياً
SOURCES = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
    "https://raw.githubusercontent.com/billyskid/IPTV-Premium/main/premium.m3u",
    "https://iptv-org.github.io/iptv/categories/sports.m3u"
]

def check_link(url):
    try:
        # فحص سريع جداً للتأكد من استجابة السيرفر
        r = requests.head(url, timeout=3, allow_redirects=True)
        if r.status_code == 200:
            return url
    except:
        return None

def start_hunting():
    all_links = []
    print("📡 جاري سحب الروابط المحدثة...")
    for s in SOURCES:
        try:
            data = requests.get(s, timeout=10).text
            all_links.extend(re.findall(r'(http[s]?://[^\s\'"<>]+)', data))
        except: continue
    
    all_links = list(set(all_links))
    print(f"🔎 جاري فحص {len(all_links)} قناة...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        valid_links = list(executor.map(check_link, all_links))
    
    working = [v for v in valid_links if v]
    
    # حفظ النتائج في الملف الذي سيقرأه المشغل
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for link in working:
            f.write(f"#EXTINF:-1, [AUTO_UPDATED_LIVE]\n{link}\n")
    print(f"✅ تم تحديث القائمة بـ {len(working)} قناة شغالة.")

if __name__ == "__main__":
    start_hunting()

