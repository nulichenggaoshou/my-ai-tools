# -*- coding: utf-8 -*-
"""
文件格式转换器 —— 后端版
我的第一个后端作品：Word / PDF / Excel 三种格式互转

支持 5 个转换方向：
  📄 Word → PDF   （LibreOffice 命令行）
  📑 PDF → Word   （pdf2docx）
  📊 Excel → PDF  （LibreOffice 命令行）
  📊 Excel → CSV  （pandas）
  📄 CSV → Excel  （pandas）

用到的后端技术：
  Flask（网页后端框架）+ LibreOffice + pdf2docx + pandas

怎么运行：终端  python app.py  →  浏览器打开 http://127.0.0.1:5000
"""
import os
import time
import subprocess
import pandas as pd
from flask import Flask, request, send_file
from pdf2docx import Converter

app = Flask(__name__)

# 项目所在文件夹
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# LibreOffice 的位置（用于 Word/Excel → PDF）
SOFFICE = r'C:\Program Files\LibreOffice\program\soffice.exe'

# 每个转换方向：from = 上传后缀，to = 结果后缀
TYPES = {
    'word2pdf':  {'from': '.docx', 'to': '.pdf',  'name': 'Word → PDF'},
    'pdf2word':  {'from': '.pdf',  'to': '.docx', 'name': 'PDF → Word'},
    'excel2pdf': {'from': '.xlsx', 'to': '.pdf',  'name': 'Excel → PDF'},
    'excel2csv': {'from': '.xlsx', 'to': '.csv',  'name': 'Excel → CSV'},
    'csv2excel': {'from': '.csv',  'to': '.xlsx', 'name': 'CSV → Excel'},
}

# 用 LibreOffice 转的方向（它都能输出成 pdf）
LIBRE_TYPES = ('word2pdf', 'excel2pdf')


HOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>文件格式转换器</title>
  <style>
    :root {
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --bg: #f4f5f7;
      --card: #ffffff;
      --border: #e5e7eb;
      --text: #1f2937;
      --muted: #6b7280;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
      background: var(--bg); color: var(--text); padding: 32px 16px; line-height: 1.6;
    }
    .container { max-width: 620px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 24px; }
    header h1 { font-size: 28px; font-weight: 700; }
    header h1 .emoji { display: block; font-size: 44px; margin-bottom: 4px; }
    header p { color: var(--muted); margin-top: 6px; font-size: 15px; }
    header a { color: var(--primary); text-decoration: none; font-size: 14px; }

    .card {
      background: var(--card); border: 1px solid var(--border); border-radius: 14px;
      padding: 22px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .type-tabs { display: flex; gap: 8px; margin-bottom: 18px; flex-wrap: wrap; }
    .type-tab {
      border: 1px solid var(--border); background: #fff; color: var(--muted);
      padding: 9px 14px; border-radius: 999px; font-size: 14px; cursor: pointer;
      transition: all .15s; font-family: inherit;
    }
    .type-tab.active { background: var(--primary); color: #fff; border-color: var(--primary); font-weight: 600; }

    .drop {
      border: 2px dashed var(--border); border-radius: 12px; padding: 30px 16px;
      text-align: center; color: var(--muted); font-size: 14px; cursor: pointer;
      transition: all .15s; background: #fafbfc;
    }
    .drop:hover, .drop.over { border-color: var(--primary); background: #f5f6ff; color: var(--primary); }
    .drop .big { font-size: 32px; display: block; margin-bottom: 6px; }
    .drop .file-name { color: var(--primary); font-weight: 600; margin-top: 8px; word-break: break-all; }

    input[type="file"] { display: none; }
    button {
      border: none; border-radius: 10px; padding: 13px 0; width: 100%;
      font-size: 16px; cursor: pointer; transition: all .15s; font-family: inherit;
      margin-top: 16px;
    }
    .btn-primary { background: var(--primary); color: #fff; font-weight: 600; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-primary:disabled { background: #c7d2fe; cursor: not-allowed; }

    .hint { text-align: center; color: #9ca3af; font-size: 13px; margin-top: 12px; }

    .types-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; }
    .t-item { background: #fafbfc; border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
    .t-item .ico { font-size: 22px; }
    .t-item .name { font-size: 13px; font-weight: 600; margin-top: 4px; }
    .t-item .tech { font-size: 11px; color: var(--muted); margin-top: 2px; }

    footer { text-align: center; color: #9ca3af; font-size: 13px; margin-top: 24px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="emoji">🔄</span>文件格式转换器</h1>
      <p>上传文件，一键转换格式 —— 我的第一个后端作品</p>
      <a href="../index.html">← 返回工具集</a>
    </header>

    <div class="card">
      <div class="type-tabs">
        <button class="type-tab active" data-type="word2pdf">📄 Word → PDF</button>
        <button class="type-tab" data-type="pdf2word">📑 PDF → Word</button>
        <button class="type-tab" data-type="excel2pdf">📊 Excel → PDF</button>
        <button class="type-tab" data-type="excel2csv">📊 Excel → CSV</button>
        <button class="type-tab" data-type="csv2excel">📄 CSV → Excel</button>
      </div>

      <form action="/convert" method="post" enctype="multipart/form-data" id="form">
        <input type="hidden" name="convert_type" id="convert_type" value="word2pdf">
        <div class="drop" id="drop">
          <span class="big">📁</span>
          <span id="drop-text">点击选择文件，或拖到这里</span>
          <div class="file-name" id="file-name"></div>
        </div>
        <input type="file" name="file" id="file" accept=".docx" required>
        <button class="btn-primary" type="submit" id="submit" disabled>开始转换</button>
      </form>
      <p class="hint">转换在你自己电脑上完成，文件不会上传到任何地方</p>
    </div>

    <div class="card">
      <div class="types-info">
        <div class="t-item"><div class="ico">📄→📕</div><div class="name">Word → PDF</div><div class="tech">LibreOffice</div></div>
        <div class="t-item"><div class="ico">📕→📄</div><div class="name">PDF → Word</div><div class="tech">pdf2docx</div></div>
        <div class="t-item"><div class="ico">📊→📕</div><div class="name">Excel → PDF</div><div class="tech">LibreOffice</div></div>
        <div class="t-item"><div class="ico">📊→📄</div><div class="name">Excel → CSV</div><div class="tech">pandas</div></div>
        <div class="t-item"><div class="ico">📄→📊</div><div class="name">CSV → Excel</div><div class="tech">pandas</div></div>
      </div>
    </div>

    <footer>我的第一个后端作品 · Flask + LibreOffice + pdf2docx + pandas</footer>
  </div>

  <script>
    var ACC = { word2pdf: '.docx', pdf2word: '.pdf', excel2pdf: '.xlsx', excel2csv: '.xlsx', csv2excel: '.csv' };
    var fileInput = document.getElementById('file');
    var drop = document.getElementById('drop');
    var dropText = document.getElementById('drop-text');
    var fileName = document.getElementById('file-name');
    var submit = document.getElementById('submit');
    var hidden = document.getElementById('convert_type');

    function showName(name) {
      fileName.textContent = name;
      dropText.textContent = '已选好文件：';
      submit.disabled = false;
    }

    // 切换转换方向
    document.querySelectorAll('.type-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        document.querySelectorAll('.type-tab').forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        hidden.value = tab.dataset.type;
        fileInput.value = '';
        fileInput.setAttribute('accept', ACC[tab.dataset.type]);
        fileName.textContent = '';
        dropText.textContent = '点击选择文件，或拖到这里';
        submit.disabled = true;
      });
    });

    // 点上传区 = 点文件框
    drop.addEventListener('click', function () { fileInput.click(); });

    // 拖入文件
    drop.addEventListener('dragover', function (e) { e.preventDefault(); drop.classList.add('over'); });
    drop.addEventListener('dragleave', function () { drop.classList.remove('over'); });
    drop.addEventListener('drop', function (e) {
      e.preventDefault();
      drop.classList.remove('over');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        showName(fileInput.files[0].name);
      }
    });

    // 选中文件后显示文件名
    fileInput.addEventListener('change', function () {
      if (fileInput.files.length) showName(fileInput.files[0].name);
    });
  </script>
</body>
</html>"""


@app.route('/')
def home():
    return HOME_HTML


@app.route('/convert', methods=['POST'])
def convert():
    """一个函数处理所有转换方向：收文件 → 按方向转换 → 送下载"""
    convert_type = request.form.get('convert_type', 'word2pdf')
    if convert_type not in TYPES:
        return '❌ 未知的转换类型', 400

    file = request.files.get('file')
    if not file or not file.filename:
        return '❌ 没收到文件，请先选择文件', 400

    src_ext = TYPES[convert_type]['from']
    if not file.filename.lower().endswith(src_ext):
        return '❌ 这个方向只支持 ' + src_ext + ' 文件，请重新选择', 400

    # ① 保存上传的文件（名字加时间戳，避免重名覆盖）
    stem = str(int(time.time()))
    src_path = os.path.join(UPLOAD_DIR, stem + src_ext)
    file.save(src_path)
    out_path = os.path.join(UPLOAD_DIR, stem + TYPES[convert_type]['to'])

    # ② 按方向，调用不同的转换
    if convert_type in LIBRE_TYPES:
        # Word / Excel → PDF：都交给 LibreOffice
        subprocess.run(
            [SOFFICE, '--headless', '--convert-to', 'pdf', src_path, '--outdir', UPLOAD_DIR],
            capture_output=True, text=True, timeout=120,
        )
    elif convert_type == 'pdf2word':
        # PDF → Word：交给 pdf2docx
        cv = Converter(src_path)
        cv.convert(out_path)
        cv.close()
    elif convert_type == 'excel2csv':
        # Excel → CSV：pandas 读进数据表，再写成 CSV（utf-8-sig 让中文不乱码）
        pd.read_excel(src_path).to_csv(out_path, index=False, encoding='utf-8-sig')
    elif convert_type == 'csv2excel':
        # CSV → Excel：CSV 可能是 UTF-8 或 GBK，先试 UTF-8，失败再试 GBK
        try:
            df = pd.read_csv(src_path)
        except UnicodeDecodeError:
            df = pd.read_csv(src_path, encoding='gbk')
        df.to_excel(out_path, index=False)

    # ③ 转换成功就送回浏览器下载
    if not os.path.exists(out_path):
        return '❌ 转换失败，请确认文件没坏、不是图片扫描件', 500

    return send_file(out_path, as_attachment=True, download_name='转换结果' + TYPES[convert_type]['to'])


if __name__ == '__main__':
    app.run(port=5000, debug=True)
