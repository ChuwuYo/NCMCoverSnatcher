import requests
import re
import time
import os
import random
from bs4 import BeautifulSoup

# ✅ 简化的通用请求头，更自然
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

def get_random_headers():
    """
    获取随机化的请求头，保持简单自然
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    headers = HEADERS.copy()
    headers["User-Agent"] = random.choice(user_agents)
    
    # 随机添加Referer，有时候有，有时候没有，更自然
    if random.choice([True, False]):
        headers["Referer"] = "https://music.163.com/"
    
    return headers

def safe_request(url, session, retries=2):
    """
    带重试逻辑的安全请求函数，增强网络错误处理
    """
    for attempt in range(retries):
        try:
            # 每次请求前添加随机延迟，避免请求过于频繁
            if attempt > 0:
                delay = random.uniform(2, 4)  # 重试时适度延迟
                print(f"⏳ 等待 {delay:.1f} 秒后重试...")
                time.sleep(delay)
            
            # 使用随机化的请求头
            headers = get_random_headers()
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # 检查HTTP状态码
            return response
            
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ 第 {attempt+1} 次连接失败：网络连接被重置")
        except requests.exceptions.Timeout as e:
            print(f"⚠️ 第 {attempt+1} 次请求超时")
        except requests.exceptions.HTTPError as e:
            print(f"⚠️ 第 {attempt+1} 次HTTP错误：{e.response.status_code}")
        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次未知错误：{str(e)[:100]}")
            
        if attempt < retries - 1:
            print(f"🔄 准备第 {attempt+2} 次尝试...")
    
    print("❌ 多次尝试失败，跳过该项")
    return None

def human_delay():
    """
    模拟人类访问延迟，避免请求过于频繁
    """
    delay = random.uniform(1.0, 2.0)  # 减少延迟时间
    time.sleep(delay)

def extract_id_and_type(user_input):
    """
    从用户输入中提取 ID 和类型（song 或 album）
    """
    if "music.163.com" in user_input:
        if "song?id=" in user_input:
            match = re.search(r'song\?id=(\d+)', user_input)
            return match.group(1), 'song' if match else (None, None)
        elif "album?id=" in user_input:
            match = re.search(r'album\?id=(\d+)', user_input)
            return match.group(1), 'album' if match else (None, None)
        else:
            return None, None
    else:
        return user_input.strip(), 'song'

def sanitize_filename(name):
    """
    清理文件名中的非法字符
    """
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def choose_filename_format():
    """
    让用户选择封面命名格式
    """
    print("\n请选择封面命名格式：")
    print("1. 歌手 - 歌名")
    print("2. 歌名 - 歌手")
    print("3. 序号.歌手 - 歌名")
    print("4. 序号.歌名 - 歌手")
    choice = input("请输入编号（1-4），默认1：").strip()
    return int(choice) if choice in ['1', '2', '3', '4'] else 1

def generate_filename(index, name1, name2, format_type):
    """
    根据命名格式生成文件名
    """
    if format_type == 1:
        name = f"{name1} - {name2}"
    elif format_type == 2:
        name = f"{name2} - {name1}"
    elif format_type == 3:
        name = f"{index:02d}.{name1} - {name2}"
    elif format_type == 4:
        name = f"{index:02d}.{name2} - {name1}"
    else:
        name = f"{name1} - {name2}"
    return sanitize_filename(name) + ".jpg"

def get_song_info(song_id, session):
    """
    获取歌曲封面图链接、歌名、歌手名
    """
    url = f"https://music.163.com/song?id={song_id}"
    res = safe_request(url, session)
    if not res:
        return None, f"song_{song_id}", "未知歌手"
    soup = BeautifulSoup(res.text, 'html.parser')

    title_tag = soup.find('meta', {'property': 'og:title'})
    song_name = title_tag['content'].split(' - ')[-1] if title_tag else f"song_{song_id}"

    artist_span = soup.select_one('p.des.s-fc4 span[title]')
    if artist_span and artist_span.get('title'):
        artist_str = '_'.join([a.strip().replace(' ', '') for a in artist_span['title'].split('/')])
    else:
        artist_str = "未知歌手"

    img_tag = soup.find('meta', {'property': 'og:image'})
    img_url = img_tag['content'].split('?')[0] if img_tag else None

    return img_url, song_name, artist_str

def get_album_cover(album_id, session):
    """
    获取专辑封面图链接和专辑名
    """
    url = f"https://music.163.com/album?id={album_id}"
    res = safe_request(url, session)
    if not res:
        return None, f"album_{album_id}"
    soup = BeautifulSoup(res.text, 'html.parser')

    img_tag = soup.select_one('div.cover.u-cover.u-cover-alb img')
    img_url = img_tag.get('data-src') if img_tag and img_tag.has_attr('data-src') else None
    if img_url:
        img_url = img_url.split('?')[0]

    title_tag = soup.find('meta', {'property': 'og:title'})
    album_name = title_tag['content'] if title_tag else f"album_{album_id}"

    return img_url, sanitize_filename(album_name)

def download_cover(id_or_url, session, format_type, index, fail_list):
    """
    下载歌曲或专辑封面图
    """
    item_id, content_type = extract_id_and_type(id_or_url)
    if not item_id:
        print(f"❌ [{index}] 无法识别链接或 ID：{id_or_url}")
        fail_list.append(id_or_url)
        return

    try:
        os.makedirs("covers", exist_ok=True)

        if content_type == 'album':
            img_url, album_name = get_album_cover(item_id, session)
            if not img_url:
                print(f"❌ [{index}] 未找到专辑封面图：{item_id}")
                fail_list.append(item_id)
                return
            filename = f"{album_name}.jpg"
            img_response = safe_request(img_url, session)
            if not img_response:
                print(f"❌ [{index}] 下载专辑封面失败：{item_id}")
                fail_list.append(item_id)
                return
            img_data = img_response.content
            with open(os.path.join("covers", filename), 'wb') as f:
                f.write(img_data)
            print(f"✅ [{index}] 专辑《{album_name}》封面已保存")
            human_delay()
            return

        elif content_type == 'song':
            img_url, song_name, artist_str = get_song_info(item_id, session)
            if not img_url:
                print(f"❌ [{index}] 未找到歌曲封面图：{item_id}")
                fail_list.append(item_id)
                return
            filename = generate_filename(index, artist_str, song_name, format_type)
            img_response = safe_request(img_url, session)
            if not img_response:
                print(f"❌ [{index}] 下载歌曲封面失败：{item_id}")
                fail_list.append(item_id)
                return
            img_data = img_response.content
            with open(os.path.join("covers", filename), 'wb') as f:
                f.write(img_data)
            print(f"✅ [{index}] {artist_str} - {song_name} 已保存")
            human_delay()
            return

        else:
            print(f"❌ [{index}] 暂不支持的类型：{content_type}")
            fail_list.append(item_id)

    except Exception as e:
        print(f"⚠️ [{index}] 出错了：{e}")
        fail_list.append(item_id)

def main():
    """
    主程序入口
    """
    print("🎵 请输入多个网易云歌曲或专辑链接/ID（每行一个），输入完后请直接回车留空一行确认：")
    try:
        user_input = []
        while True:
            line = input()
            if line.strip() == "":
                break
            user_input.append(line.strip())

        format_type = choose_filename_format()
        
        # 配置会话以提高稳定性
        session = requests.Session()
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=0))
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
        
        # 设置连接池参数
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=0
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        fail_list = []

        print(f"🚀 开始处理 {len(user_input)} 个项目...")
        for idx, item in enumerate(user_input, start=1):
            download_cover(item, session, format_type, idx, fail_list)

        # 输出处理结果统计
        success_count = len(user_input) - len(fail_list)
        print(f"📊 处理完成！成功：{success_count}，失败：{len(fail_list)}")
        
        if fail_list:
            print("❌ 失败列表：")
            for i, failed_item in enumerate(fail_list, 1):
                print(f"  {i}. {failed_item}")

    except KeyboardInterrupt:
        print("\n🛑 用户中断")

if __name__ == "__main__":
    main()
