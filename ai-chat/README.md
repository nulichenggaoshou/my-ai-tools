# 💬 AI 聊天助手

我的**第三个 AI 工具** —— 多轮对话，像 ChatGPT 一样聊天。

## 它和总结/翻译最大的不同

总结、翻译是「问一句答一句，答完就忘」；聊天助手**记得之前的对话**。

> 你说"我养了只猫"，下一句问"我养了什么？"，它能答出"猫"。

**多轮对话的秘密**：把之前的聊天记录（一个数组），每次都完整地重新发给大模型。大模型看到完整历史，自然就"记得"。

## 技术栈

| 技术 | 作用 |
|------|------|
| Flask | 网页后端 |
| requests | 调用 DeepSeek API |
| DeepSeek | 大模型（deepseek-chat） |

## 怎么运行

```bash
pip install flask requests
python app.py
# 浏览器打开 http://127.0.0.1:5003
```

## 我学到的新东西

1. **多轮对话原理**：前端存一个历史数组，每次完整发回。
2. **前端 messages 格式**：`system`（角色）+ 一串 `user`/`assistant` 来回。
3. **排查 bug 的方法**：打开 F12 控制台，看报错信息定位。

## 踩过的坑（重要）

报错 `history.push is not a function`：

`history` 是浏览器内置的全局对象（`window.history`，浏览历史）。我写 `var history = []` 想覆盖它，但浏览器不允许，所以 `history` 还是浏览器那个对象，没有 `.push` 方法。

**教训**：变量名别用浏览器保留字——`history`、`location`、`name`、`top`、`close`、`parent`、`open` 等。遇到 `xxx is not a function`，先想想是不是名字被占用了。
