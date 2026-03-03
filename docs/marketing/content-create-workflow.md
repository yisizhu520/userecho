
userecho.app 的营销太费时间了，我要花费 2 个小时来写一篇小红书。

包括选题，写文案，生成配图，发布到各平台。这些明显能自动化。

我要做成一个 agent skill

但是这不能完全的自动化，因为我需要自己 review，进行几轮修改，才能发布。所以这个过程需要人工介入。（或者用不同 ai 互相 review？）


输入：
- 目标平台：小红书，微信图文，微信视频号图文，抖音图文
- 目标人群：创业者 / 中小企业老板 / 独立开发者
- 核心产品：userecho.app 的功能特性，产品截图
- 核心价值：降本增效、商业洞察
- 营销策略：从"硬广推销"转向"价值驱动"，贩卖"更先进的职业工作流"和"更高维的行业认知"。
- 人设定位：回响 UserEcho 创始人 / 独立开发者，Build in Public。


输出：
- 选题
- 文案
- 配图
    - 封面图： nano banana pro 根据文案生成
    - 内容图： 产品截图    
- 发布到各平台

内容形式：

- AI 生成 markdown 格式的文案
- AI 将内容划分成几个章节，每个章节调用 nano banana pro 生成图片
- 根据文案生成封面图（antigravity 的 nano banana pro api）
- 爱贝壳插件发布到各平台（用 browser mcp）

# 参考：

## 生图的代码:

```
from openai import OpenAI
 
 client = OpenAI(
     base_url="http://antigravity.memeflow.app/v1",
     api_key="sk-b22c3073332d4bc493c0fdb919972cce"
 )
 
 response = client.chat.completions.create(
     model="gemini-3-pro-image",
     # 方式 1: 使用 size 参数 (推荐)
     # 支持: "1024x1024" (1:1), "1280x720" (16:9), "720x1280" (9:16), "1216x896" (4:3)
     extra_body={ "size": "1024x1024" },
     
     # 方式 2: 使用模型后缀
     # 例如: gemini-3-pro-image-16-9, gemini-3-pro-image-4-3
     # model="gemini-3-pro-image-16-9",
     messages=[{
         "role": "user",
         "content": "Draw a futuristic city"
     }]
 )
 
 print(response.choices[0].message.content)
```
