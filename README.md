# web2rss

通过GitHub Action 自动生成网页的 RSS 订阅。
已有的RSS订阅：[点击查看](rss/readme.md)

## 站点配置
配置文件：config.yaml

每个站点的配置项如下：

- **name**: 站点的名称，用于标识不同的站点。
- **follow_desc**: 用于follow的订阅所有权描述方式的验证。
- **url**: 站点的 URL 地址。
- **block_css**: 父元素的 CSS 选择器，用于定位单个文章块。
- **title_css**: 在父元素内部的标题选择器，用于提取文章标题。
- **description_css**: 在父元素内部的描述选择器，用于提取文章描述。
- **link_css**: 在父元素内部的链接选择器，用于提取文章链接。链接在父元素的情况下，该字段置空
- **use_headless_browser**: 是否使用无头浏览器进行页面加载，布尔值（`true` 或 `false`）。
- **extra_css**: 额外的 CSS 选择器列表，用于获取更多信息（如语言、星标数等）。可选配置项。
- **proxy**: 代理服务器地址，用于访问需要代理的网站。可选配置项。

### 配置项说明

1. **name**: 必填项，用于在 RSS 输出中标识不同的站点。
2. **follow_desc**: 可选项，用于验证订阅所有权的描述文本。
3. **url**: 必填项，要抓取的网页地址。
4. **block_css**: 必填项，用于定位包含文章内容的父元素。
5. **title_css**: 必填项，用于从父元素中提取文章标题。
6. **description_css**: 可选项，用于提取文章描述。如果不需要描述，可以留空。
7. **link_css**: 可选项，用于提取文章链接。如果链接在父元素上，可以留空。
8. **use_headless_browser**: 必填项，决定是否使用无头浏览器加载页面。对于需要 JavaScript 渲染的页面，建议设置为 `true`。
9. **extra_css**: 可选项，用于提取额外的信息，如编程语言、星标数等。格式为 YAML 列表。
10. **proxy**: 可选项，设置代理服务器地址，用于访问需要代理的网站。

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