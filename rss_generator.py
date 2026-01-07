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
import argparse
import sys


def create_webdriver(proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 启用无头模式
    chrome_options.add_argument("--no-sandbox")  # 解决 DevToolsActivePort 文件错误
    chrome_options.add_argument("--disable-dev-shm-usage")  # 解决资源限制
    chrome_options.add_argument("--disable-gpu")  # 如果不需要 GPU 加速，禁用它
    chrome_options.add_argument("--window-size=1920x1080")  # 设置窗口大小
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用自动化控制特征
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")  # 设置用户代理
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 隐藏自动化特征
    chrome_options.add_experimental_option('useAutomationExtension', False)  # 禁用自动化扩展
    
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')

    # 创建 Chrome 驱动
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # 隐藏 webdriver 特征
    return driver

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def fetch_blog_posts(config):
    print(f"Fetching posts from: {config['url']}")
    print(f"Using selectors: block={config['block_css']}, title={config['title_css']}, description={config['description_css']}, link={config['link_css']}, date={config.get('date_css', 'N/A')}")

    proxy = config.get('proxy')  # 获取代理设置

    if config['use_headless_browser']:
        print(f"Using headless browser to fetch {config['url']}")
        driver = create_webdriver(proxy)
        
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get(config['url'])
                print(f"Initial page load complete, waiting 5 seconds... (Attempt {attempt+1})")
                time_module.sleep(5)  # 增加等待时间
                
                # 滚动到页面底部以加载所有内容
                print("Starting scroll to bottom process...")
                last_height = driver.execute_script("return document.body.scrollHeight")
                scroll_count = 0
                while True:
                    # 滚动到页面底部
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print(f"Scroll iteration {scroll_count+1}, scrolled to {last_height}")
                    
                    # 等待新内容加载
                    time_module.sleep(3)  # 增加等待时间
                    
                    # 计算新的滚动高度
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    print(f"New page height: {new_height}")
                    if new_height == last_height:
                        print("Reached bottom of page, no more content to load")
                        break
                    last_height = new_height
                    scroll_count += 1
                    if scroll_count > 50:  # 防止无限滚动
                        print("Maximum scroll iterations reached, stopping")
                        break
                
                # 最终等待，确保所有内容加载完成
                print("Page scrolling complete, waiting 5 seconds for final content load...")
                time_module.sleep(5)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.quit()
                print("Headless browser closed")
                break  # 成功获取页面，跳出重试循环
                
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time_module.sleep(5)
                else:
                    print("Max retries reached. Raising exception.")
                    driver.quit()
                    raise e
    else:
        print(f"Using requests to fetch {config['url']}")
        proxies = {'http': proxy, 'https': proxy} if proxy else None
        response = requests.get(config['url'], proxies=proxies)
        print(f"Response status code: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')

    # 基于文本块选择器获取所有相关块
    blocks = soup.select(config['block_css'])
    print(f"Found {len(blocks)} blocks matching selector '{config['block_css']}'")

    posts = []
    for i, block in enumerate(blocks):
        print(f"Processing block {i+1}/{len(blocks)}")
        title = block.select_one(config['title_css'])
        description = block.select_one(config['description_css']) if config['description_css'] else block
        link = block.select_one(config['link_css']) if config['link_css'] else block
        date_element = block.select_one(config['date_css']) if config.get('date_css') else None

        # 获取额外信息
        extra_info = []
        if 'extra_css' in config:
            for css_selector in config['extra_css']:
                element = block.select_one(css_selector)
                if element:
                    extra_info.append(element.get_text(strip=True))
                else:
                    print(f"Warning: No element found for selector: {css_selector}")
                    extra_info.append("N/A")  # 用默认值填充缺失信息

        if title and description and link:
            post_data = {
                'title': title.get_text(strip=True),
                'description': description.get_text(strip=True),
                'link': link['href'] if link['href'].startswith('http') else urljoin(config['url'], link['href']),
                'extra_info': extra_info,
                'pub_date': None
            }

            # 处理日期
            if date_element:
                # 优先获取 dateTime 属性
                date_str = date_element.get('datetime') or date_element.get('dateTime')
                if date_str:
                    try:
                        # 解析 ISO 8601 格式日期
                        post_data['pub_date'] = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        print(f"Extracted date from dateTime attribute: {date_str}")
                    except Exception as e:
                        print(f"Failed to parse dateTime '{date_str}': {e}")
                        # 尝试解析文本内容
                        try:
                            post_data['pub_date'] = datetime.fromisoformat(date_element.get_text(strip=True))
                        except Exception as e2:
                            print(f"Failed to parse date text: {e2}")
                else:
                    # 没有 dateTime 属性，尝试解析文本
                    date_text = date_element.get_text(strip=True)
                    try:
                        # 尝试常见日期格式
                        for fmt in ['%Y-%m-%d', '%b %d, %Y', '%Y年%m月%d日']:
                            try:
                                post_data['pub_date'] = datetime.strptime(date_text, fmt)
                                print(f"Parsed date with format '{fmt}': {date_text}")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        print(f"Failed to parse date text '{date_text}': {e}")
            posts.append(post_data)
            print(f"Successfully parsed post: {post_data['title']}")
        else:
            print(f"Skipped block {i+1} due to missing data - Title: {bool(title)}, Description: {bool(description)}, Link: {bool(link)}")

    print(f"Total posts extracted: {len(posts)}")
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

        # 设置发布时间
        if post.get('pub_date'):
            entry.pubDate(post['pub_date'])
            print(f"Set pubDate for {post['title']}: {post['pub_date']}")

    return feed.rss_str(pretty=True).decode('utf-8')  # 确保返回字符串

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成网站RSS订阅源')
    parser.add_argument('--site', '-s', type=str, help='指定要生成的站点名称（例如：cursor_blog）')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用的站点名称')
    args = parser.parse_args()

    config = load_config()

    # 如果使用 --list 参数，列出所有站点
    if args.list:
        print("可用的站点列表：")
        for site in config['sites']:
            print(f"  - {site['name']}: {site['url']}")
        sys.exit(0)

    # 筛选要处理的站点
    sites_to_process = config['sites']
    if args.site:
        sites_to_process = [site for site in config['sites'] if site['name'] == args.site]
        if not sites_to_process:
            print(f"错误：未找到名为 '{args.site}' 的站点")
            print(f"使用 --list 参数查看所有可用站点")
            sys.exit(1)
        print(f"仅生成站点：{args.site}")
    else:
        print(f"生成所有站点的RSS")

    # 创建readme.md文件
    readme_path = "rss/readme.md"
    with open(readme_path, 'w', encoding='utf-8') as readme_file:
        readme_file.write("# RSS订阅\n\n")

    for site in sites_to_process:
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