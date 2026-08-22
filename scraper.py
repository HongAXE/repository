import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

FOLDERS = {
    "APP": {
        "url": "https://wwamp.lanzouu.com/b00zyvo2cf",
        "pwd": "hong"
    },
    "Malody": {"url": "", "pwd": ""},
    "Phira": {"url": "", "pwd": ""},
    "osu!": {"url": "", "pwd": ""}
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

def get_page_html(url, pwd):
    resp = session.get(url, timeout=10)
    html = resp.text

    if '请输入密码' in html or '输入密码' in html:
        sign_match = re.search(r"var sign = '([a-f0-9]+)'", html)
        if sign_match:
            sign = sign_match.group(1)
            post_data = {'action': 'filelist', 'pwd': pwd, 'sign': sign}
            ajax_url = 'https://wwamp.lanzouu.com/ajaxm.php'
            resp = session.post(ajax_url, data=post_data, headers={'Referer': url})
            html = resp.text
    return html

def parse_files_and_folders(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    files = []
    subfolders = []

    # ===== 激进模式：抓取页面中所有链接 =====
    for a in soup.find_all('a', href=True):
        href = a['href']
        name = a.get_text(strip=True)
        if not name or name in ['返回', '上一页', '首页']:
            continue

        full_url = urljoin(base_url, href)
        
        # 判断是否为文件夹：链接包含 b0 或 folder
        if 'b0' in href or 'folder' in href:
            subfolders.append({"name": name, "url": full_url})
            print(f"    [子文件夹] {name} -> {full_url}")
        else:
            # 如果是文件，尝试获取大小
            size = ''
            parent = a.find_parent('tr')
            if parent:
                size_td = parent.find('td', class_='file_size')
                if size_td:
                    size = size_td.get_text(strip=True)
            files.append({"name": name, "size": size, "url": full_url})

    # 如果还是没抓到，打印页面中的所有链接用于调试
    if not files and not subfolders:
        print("    [调试] 页面中所有链接:")
        for a in soup.find_all('a', href=True):
            print(f"      {a.get_text(strip=True)} -> {a['href']}")

    return files, subfolders

def fetch_recursive(url, pwd, visited=None, depth=0):
    if visited is None:
        visited = set()
    if not url or url in visited:
        return []
    visited.add(url)

    indent = "  " * depth
    print(f"{indent}📁 正在抓取: {url}")
    try:
        html = get_page_html(url, pwd)
        files, subfolders = parse_files_and_folders(html, url)

        print(f"{indent}   📄 当前文件夹: {len(files)} 个文件, {len(subfolders)} 个子文件夹")
        
        for sub in subfolders:
            sub_files = fetch_recursive(sub['url'], pwd, visited, depth + 1)
            files.extend(sub_files)

        time.sleep(0.8)
        return files
    except Exception as e:
        print(f"{indent}   ❌ 抓取失败: {e}")
        return []

def main():
    result = {}
    for name, config in FOLDERS.items():
        url = config.get('url')
        pwd = config.get('pwd', '')
        if not url:
            print(f'⚠️ 跳过 {name}：未配置链接')
            result[name] = []
            continue
        print(f'📁 开始递归抓取分类: {name}')
        files = fetch_recursive(url, pwd)
        print(f'   ✅ 抓取完成，共 {len(files)} 个文件')
        result[name] = files

    with open('files.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('✅ 已生成 files.json')

if __name__ == '__main__':
    main()