# -*- coding: utf-8 -*-
"""
🌐 AI 翻译工具 —— 我的第二个 AI 工具

和总结工具结构一样，但多了两个提示词新花样：
  1. 角色设定：让 AI「扮演专业翻译」
  2. 输出格式控制：让 AI 不只给译文，还能「附上重点词汇解释」

用到的技术：
  Flask + requests + DeepSeek 大模型

怎么运行：终端  python app.py  →  浏览器打开 http://127.0.0.1:5002
"""
import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

app = Flask(__name__)

# ========== DeepSeek 配置 ==========
load_dotenv()   # 从 .env 文件读取 key
API_KEY = os.environ.get('DEEPSEEK_API_KEY')   # 不再把 key 硬编码在代码里
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


# ========== 提示词设计：选项 → 指令片段 ==========
DIRECTIONS = {
    'zh2en': '把用户给的中文翻译成英文。',
    'en2zh': '把用户给的英文翻译成中文。',
}
STYLES = {
    'literal': '翻译要忠实原文、准确直译。',
    'natural': '翻译要地道自然，符合目标语言的表达习惯，不要逐字硬翻。',
}
EXTRAS = {
    'none': '只输出译文，不要加任何额外解释。',
    'words': '先输出译文；然后用「📚 重点词汇」作小标题，列出文中 3~5 个重点单词或短语，并简单解释它们的意思。',
}


# ========== 网页界面（前端） ==========
HOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 翻译工具</title>
  <style>
    :root { --primary: #4f46e5; --primary-hover: #4338ca; --bg: #f4f5f7; --card: #ffffff; --border: #e5e7eb; --text: #1f2937; --muted: #6b7280; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif; background: var(--bg); color: var(--text); padding: 32px 16px; line-height: 1.7; }
    .container { max-width: 720px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 24px; }
    header h1 { font-size: 28px; font-weight: 700; }
    header h1 .emoji { display: block; font-size: 44px; margin-bottom: 4px; }
    header p { color: var(--muted); margin-top: 6px; font-size: 15px; }
    header a { color: var(--primary); text-decoration: none; font-size: 14px; }

    .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 22px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    textarea { width: 100%; min-height: 170px; border: 1px solid var(--border); border-radius: 10px; padding: 14px; font-size: 15px; font-family: inherit; resize: vertical; outline: none; transition: border-color .15s; }
    textarea:focus { border-color: var(--primary); }

    .options { display: flex; gap: 16px; margin-top: 14px; flex-wrap: wrap; }
    .opt { display: flex; align-items: center; gap: 6px; }
    .opt-label { font-size: 13px; color: var(--muted); }
    select { border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; font-size: 14px; font-family: inherit; background: #fff; outline: none; cursor: pointer; }

    button { border: none; border-radius: 10px; padding: 13px 0; width: 100%; font-size: 16px; cursor: pointer; transition: all .15s; font-family: inherit; margin-top: 16px; }
    .btn-primary { background: var(--primary); color: #fff; font-weight: 600; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-primary:disabled { background: #c7d2fe; cursor: not-allowed; }

    #result { white-space: pre-wrap; font-size: 15px; line-height: 1.8; }
    .result-empty { color: #9ca3af; text-align: center; padding: 20px 0; }
    .result-loading { color: var(--muted); text-align: center; padding: 20px 0; }
    .result-error { color: #dc2626; }
    footer { text-align: center; color: #9ca3af; font-size: 13px; margin-top: 24px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="emoji">🌐</span>AI 翻译工具</h1>
      <p>粘贴文字，选好方向 / 风格 / 附加，DeepSeek 帮你翻译</p>
      <a href="../index.html">← 返回工具集</a>
    </header>

    <div class="card">
      <textarea id="input" placeholder="把要翻译的文字粘贴到这里……"></textarea>

      <div class="options">
        <div class="opt">
          <span class="opt-label">方向</span>
          <select id="direction">
            <option value="zh2en" selected>中 → 英</option>
            <option value="en2zh">英 → 中</option>
          </select>
        </div>
        <div class="opt">
          <span class="opt-label">风格</span>
          <select id="style">
            <option value="natural" selected>地道自然</option>
            <option value="literal">直译准确</option>
          </select>
        </div>
        <div class="opt">
          <span class="opt-label">附加</span>
          <select id="extra">
            <option value="none" selected>只翻译</option>
            <option value="words">翻译 + 重点词汇</option>
          </select>
        </div>
      </div>

      <button class="btn-primary" id="btn">🌐 开始翻译</button>
    </div>

    <div class="card">
      <div id="result" class="result-empty">翻译结果会显示在这里</div>
    </div>

    <footer>我的第二个 AI 工具 · Flask + DeepSeek + 角色设定</footer>
  </div>

  <script>
    var btn = document.getElementById('btn');
    var input = document.getElementById('input');
    var result = document.getElementById('result');
    var direction = document.getElementById('direction');
    var style = document.getElementById('style');
    var extra = document.getElementById('extra');

    btn.addEventListener('click', function () {
      var text = input.value.trim();
      if (!text) { alert('请先粘贴要翻译的内容'); return; }

      btn.disabled = true;
      btn.textContent = '翻译中，请稍候……';
      result.className = 'result-loading';
      result.textContent = '🤖 DeepSeek 正在翻译……';

      fetch('/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          direction: direction.value,
          style: style.value,
          extra: extra.value,
        }),
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = '🌐 开始翻译';
        if (data.error) {
          result.className = 'result-error';
          result.textContent = '❌ ' + data.error;
        } else {
          result.className = '';
          result.textContent = data.result;
        }
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = '🌐 开始翻译';
        result.className = 'result-error';
        result.textContent = '❌ 请求失败：' + err;
      });
    });
  </script>
</body>
</html>"""


@app.route('/')
def home():
    return HOME_HTML


@app.route('/translate', methods=['POST'])
def translate():
    """接收文字和选项 → 拼提示词 → 调用 DeepSeek → 返回翻译"""
    text = request.json.get('text', '').strip()
    if not text:
        return jsonify({'error': '请输入要翻译的内容'}), 400

    direction = request.json.get('direction', 'zh2en')
    style = request.json.get('style', 'natural')
    extra = request.json.get('extra', 'none')

    # 提示词设计：角色设定 + 方向 + 风格 + 输出格式
    system_prompt = (
        '你是一名专业翻译，精通中英文。'
        + DIRECTIONS.get(direction, '')
        + STYLES.get(style, '')
        + EXTRAS.get(extra, '')
    )

    try:
        resp = requests.post(
            API_URL,
            headers={
                'Authorization': 'Bearer ' + API_KEY,
                'Content-Type': 'application/json',
            },
            json={
                'model': MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': text},
                ],
                'temperature': 0.3,   # 翻译用低温度，输出更稳定、不跑偏
            },
            timeout=60,
        )

        data = resp.json()
        if resp.status_code != 200:
            return jsonify({'error': '调用失败：' + str(data)}), 500

        result = data['choices'][0]['message']['content']
        return jsonify({'result': result})

    except Exception as e:
        return jsonify({'error': '出错了：' + str(e)}), 500


if __name__ == '__main__':
    app.run(port=5002, debug=True)
