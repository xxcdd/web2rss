# web2rss

通过GitHub Action 自动生成网页的 RSS 订阅。
已有的RSS订阅：[点击查看](rss/readme.md)

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
| use_headless_browser | 是 | boolean | 是否使用无头浏览器进行页面加载，布尔值（`true` 或 `false`）。对于需要 JavaScript 渲染的页面，建议设置为 `true` |
| extra_css | 否 | array[string] | 额外的 CSS 选择器列表，用于获取更多信息（如语言、星标数等） |
| proxy | 否 | string | 代理服务器地址，用于访问需要代理的网站 |

### 注意事项

1. CSS 选择器应该尽可能精确，以确保正确提取内容。
2. 对于需要 JavaScript 渲染的网站，必须设置 `use_headless_browser: true`。
3. 如果网站需要代理访问，请设置 `proxy` 配置项。
4. `extra_css` 配置项可以用于提取额外的元数据，但需要确保选择器正确。

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