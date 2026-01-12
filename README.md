# web2rss

通过 GitHub Action 自动生成网页的 RSS 订阅。
已有的 RSS 订阅：[点击查看](rss/readme.md)

## 功能特点

- 支持从任意网页提取内容并生成 RSS 订阅源
- 支持 CSS 选择器配置，灵活提取文章标题、描述、链接、日期等信息
- 支持无头浏览器（Selenium）渲染 JavaScript 动态页面
- 支持自动滚动加载无限滚动页面
- 支持代理访问
- 支持提取额外元数据（如标签、星标数等）并添加到标题中
- 支持多种日期格式解析（ISO 8601、dateTime 属性、常见日期格式）
- 支持命令行参数生成指定站点或查看所有可用站点

## 使用方法

```bash
# 生成所有站点的 RSS
python rss_generator.py

# 生成指定站点的 RSS
python rss_generator.py --site <站点名称>
python rss_generator.py -s <站点名称>

# 列出所有可用站点
python rss_generator.py --list
python rss_generator.py -l
```

## 站点配置
配置文件：config.yaml

| 配置项 | 必填 | 类型 | 说明 |
|--------|------|------|------|
| name | 是 | string | 站点的名称，用于标识不同的站点 |
| follow_desc | 否 | string | 用于follow的订阅所有权描述方式的验证 |
| url | 是 | string | 站点的 URL 地址 |
| block_css | 是 | string | 父元素的 CSS 选择器，用于定位单个文章块 |
| title_css | 是 | string | 在父元素内部的标题选择器，用于提取文章标题 |
| description_css | 否 | string | 在父元素内部的描述选择器，用于提取文章描述 |
| link_css | 否 | string | 在父元素内部的链接选择器，用于提取文章链接。链接在父元素的情况下，该字段置空 |
| date_css | 否 | string | 在父元素内部的日期选择器，用于提取文章发布时间。支持 `datetime` 或 `dateTime` 属性，也支持常见日期格式的文本解析 |
| use_headless_browser | 是 | boolean | 是否使用无头浏览器进行页面加载，布尔值（`true` 或 `false`）。对于需要 JavaScript 渲染的页面，建议设置为 `true` |
| extra_css | 否 | array[string] | 额外的 CSS 选择器列表，用于获取更多信息（如语言、星标数等），这些信息会被添加到标题中 |
| proxy | 否 | string | 代理服务器地址，用于访问需要代理的网站 |

### 配置说明

#### CSS 选择器

CSS 选择器应该尽可能精确，以确保正确提取内容。可以使用浏览器开发者工具（F12）检查元素并复制选择器。

#### 无头浏览器模式

对于需要 JavaScript 渲染的网站（如无限滚动页面、动态加载内容的 SPA），必须设置 `use_headless_browser: true`。无头浏览器会：

- 自动滚动到页面底部以加载所有内容
- 最多滚动 50 次，每次等待 3 秒
- 支持重试机制，最多尝试 3 次

#### 日期解析

`date_css` 配置项支持以下日期格式：

- ISO 8601 格式（通过 `datetime` 或 `dateTime` 属性）
- 常见日期格式：`%Y-%m-%d`、`%b %d, %Y`、`%Y年%m月%d日`
- 如果解析失败，该文章不会设置发布时间

#### 额外信息

`extra_css` 配置项可以用于提取额外的元数据（如标签、星标数、语言等），这些信息会被添加到 RSS 标题中，格式为：`标题 | 额外信息1 | 额外信息2`

#### 代理配置

如果网站需要代理访问，请设置 `proxy` 配置项，格式为：`http://127.0.0.1:1080`

### 示例配置

```yaml
sites:
  - name: github_trending
    follow_desc:
    url: https://github.com/trending
    block_css: article.Box-row
    title_css: h2
    description_css: 
    link_css: h2 a
    extra_css:  # 额外的CSS选择器，用于获取更多信息
      - '[itemprop="programmingLanguage"]'  # 语言
      - ".Link.Link--muted.d-inline-block.mr-3"  # star数
    use_headless_browser: false
    proxy: http://127.0.0.1:1080
```