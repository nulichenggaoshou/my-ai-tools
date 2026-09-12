# 🔄 文件格式转换器（后端版）

我的第一个**后端**作品 —— 用 Python + Flask 做的 Word / PDF / Excel 三种格式互转工具。

之前做的 6 个工具都是"双击 HTML 就能用"（纯前端），这个不一样：它背后有一个 Python 程序在跑，浏览器只是它的"脸"。这就是「前端 vs 后端」的区别。

## ✨ 功能

支持 **5 个转换方向**：

| 方向 | 靠什么实现 |
|------|-----------|
| 📄 Word → PDF | LibreOffice 命令行 |
| 📑 PDF → Word | pdf2docx |
| 📊 Excel → PDF | LibreOffice 命令行 |
| 📊 Excel → CSV | pandas |
| 📄 CSV → Excel | pandas |

## 🛠 技术栈

| 技术 | 是什么 | 用来干嘛 |
|------|--------|---------|
| Python | 后端语言 | 整个程序的"大脑" |
| Flask | Python 的网页框架 | 接收上传、返回下载 |
| pdf2docx | Python 库 | 把 PDF 转成 Word |
| pandas | Python 库 | 读写 Excel / CSV 表格 |
| LibreOffice | 独立软件 | 把 Word / Excel 转成 PDF |

## 🚀 怎么运行

```bash
# 1. 装依赖（只需一次）
pip install flask pdf2docx pandas

# 2. 启动服务
python app.py

# 3. 浏览器打开
http://127.0.0.1:5000
```

> 需要电脑上装了 LibreOffice（用来转 PDF）。

## 📁 目录结构

```
doc-converter/
├── app.py          # 后端主程序（一个文件搞定）
├── README.md       # 本说明
└── uploads/        # 上传和转换的临时文件
```

## 🧠 做这个项目我学到了什么

1. **前端 vs 后端**：前端 = 浏览器里跑的界面；后端 = 电脑/服务器上跑的逻辑。浏览器只能"看"和"点"，真正干活（转格式）的是 Python。
2. **Flask 框架**：怎么定义网址（路由）、怎么收文件、怎么把文件送回给浏览器下载。
3. **调用命令行工具**：让 Python 去"指挥" LibreOffice 干活（`subprocess`）。
4. **pandas 数据表思维**：把 Excel/CSV 当成一张「表」，读进来、写出去。
5. **中文编码**：CSV 用 `utf-8-sig` 存，才不会在 Excel 里乱码。

## 📌 后续可以做的

- 批量转换多个文件
- 把服务部署到线上，让网址能公开访问
- PDF → Excel（提取表格，难度较高）
