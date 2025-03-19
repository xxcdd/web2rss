import yaml
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time as time_module
from soupsieve.util import SelectorSyntaxError
from datetime import datetime
from urllib.parse import urljoin


def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 启用无头模式
    chrome_options.add_argument("--no-sandbox")  # 解决 DevToolsActivePort 文件错误
    chrome_options.add_argument("--disable-dev-shm-usage")  # 解决资源限制
    chrome_options.add_argument("--disable-gpu")  # 如果不需要 GPU 加速，禁用它
    chrome_options.add_argument("--window-size=1920x1080")  # 设置窗口大小

    # 创建 Chrome 驱动
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    return driver

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def fetch_blog_posts(config):
    print(f"Fetching posts from: {config['url']}")
    print(f"Using selectors: block={config['block_css']}, title={config['title_css']}, description={config['description_css']}, link={config['link_css']}")

    if config['use_headless_browser']:
        driver = create_webdriver()

        driver.get(config['url'])
        time_module.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
    else:
        response = requests.get(config['url'])
        soup = BeautifulSoup(response.content, 'html.parser')

    # 基于文本块选择器获取所有相关块
    blocks = soup.select(config['block_css'])

    posts = []
    for block in blocks:
        title = block.select_one(config['title_css'])
        description = block.select_one(config['description_css'] or block)
        link = block.select_one(config['link_css']) if config['link_css'] else block
        
        # 获取额外信息
        extra_info = []
        if 'extra_css' in config:
            for css_selector in config['extra_css']:
                element = block.select_one(css_selector)
                if element:
                    extra_info.append(element.get_text(strip=True))

        if title and description and link:
            posts.append({
                'title': title.get_text(strip=True),
                'description': description.get_text(strip=True),
                'link': link['href'] if link['href'].startswith('http') else urljoin(config['url'], link['href']),
                'extra_info': extra_info
            })

    return posts

def generate_rss(posts, site):
    feed = FeedGenerator()
    feed.id(site['url'])
    feed.title(site['name'])
    feed.link(href=site['url'])
    feed.description(f"Latest posts from {site['url']}. follow.is: {site['follow_desc']}")

    for post in posts:
        entry = feed.add_entry()
        # 构建包含额外信息的标题
        title_parts = [post['title']]
        if post.get('extra_info'):
            title_parts.extend(post['extra_info'])
        entry.title(" | ".join(title_parts))
        entry.link(href=post['link'])
        entry.description(post['description'])

    return feed.rss_str(pretty=True).decode('utf-8')  # 确保返回字符串

def main():
    config = load_config()
    
    # 创建readme.md文件
    readme_path = "rss/readme.md"
    with open(readme_path, 'w', encoding='utf-8') as readme_file:
        readme_file.write("# RSS订阅\n\n")
    
    for site in config['sites']:
        try:
            posts = fetch_blog_posts(site)
            if not posts:
                print(f"No posts found for {site['url']}, skipping RSS generation.")
                continue
                
            rss_feed = generate_rss(posts, site)
            file_name = f"rss/{site['name']}.xml"
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(rss_feed)  # 确保写入的是字符串
            print(f"Generated RSS feed for {site['url']} -> {file_name}")
            
            # 更新readme.md文件
            with open(readme_path, 'a', encoding='utf-8') as readme_file:
                readme_file.write(f"""## {site['name']}
- 原网址：{site['url']}
- 订阅源：https://raw.githubusercontent.com/xxcdd/web2rss/refs/heads/master/{file_name}
- Follow订阅跳转：[follow://add?url=https://raw.githubusercontent.com/xxcdd/web2rss/refs/heads/master/{file_name}](follow://add?url=https://raw.githubusercontent.com/xxcdd/web2rss/refs/heads/master/{file_name})\n\n""")
                
        except Exception as e:
            print(f"Error generating RSS feed for {site['url']}: {e}")

if __name__ == '__main__':
    main()