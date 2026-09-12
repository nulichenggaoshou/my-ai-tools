# -*- coding: utf-8 -*-
"""
✨ AI 总结提炼工具 —— 我的第一个 AI 工具（带提示词选项）

新增 3 组选项：形式 / 详细 / 语气
这练的是「提示词设计（prompt engineering）」——
把用户的选择，翻译成大模型能听懂的指令。

核心思路：
  用户选「要点式 + 详细 + 正式」
      ↓
  代码把它拼成一段提示词：'用要点列表总结，尽量详细，语气正式'
      ↓
  这段提示词发给大模型，它照做

用到的技术：
  Flask + requests + DeepSeek 大模型

怎么运行：终端  python app.py  →  浏览器打开 http://127.0.0.1:5001
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
# 每个选项对应一句话，告诉大模型「该用什么形式/多详细/什么语气」
FORMATS = {
    'points': '用「要点列表」的形式总结，每一点占一行并加序号。',
    'paragraph': '用「一段话」的形式总结，连贯流畅，不要分点。',
    'one': '只用「一句话」总结，给出最核心的概括。',
}
DETAILS = {
    'brief': '尽量简短，只抓最核心的信息，不要展开。',
    'standard': '详略适中，覆盖主要内容。',
    'detailed': '尽量详细全面，重要细节都要提到。',
}
TONES = {
    'formal': '语气正式、书面化。',
    'casual': '语气口语化、轻松自然，像跟朋友说话。',
    'concise': '表达精炼，不啰嗦。',
}


# ========== 网页界面（前端） ==========
HOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 总结提炼工具</title>
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
      <h1><span class="emoji">✨</span>AI 总结提炼工具</h1>
      <p>粘贴文章，选好形式 / 详细 / 语气，DeepSeek 帮你总结</p>
      <a href="../index.html">← 返回工具集</a>
    </header>

    <div class="card">
      <textarea id="input" placeholder="把要总结的文章粘贴到这里，支持中文……"></textarea>

      <!-- 3 组提示词选项 -->
      <div class="options">
        <div class="opt">
          <span class="opt-label">形式</span>
          <select id="format">
            <option value="points" selected>要点列表</option>
            <option value="paragraph">一段话</option>
            <option value="one">一句话</option>
          </select>
        </div>
        <div class="opt">
          <span class="opt-label">详细</span>
          <select id="detail">
            <option value="brief">简短</option>
            <option value="standard" selected>标准</option>
            <option value="detailed">详细</option>
          </select>
        </div>
        <div class="opt">
          <span class="opt-label">语气</span>
          <select id="tone">
            <option value="formal" selected>正式</option>
            <option value="casual">口语</option>
            <option value="concise">精炼</option>
          </select>
        </div>
      </div>

      <button class="btn-primary" id="btn">✨ 开始总结</button>
    </div>

    <div class="card">
      <div id="result" class="result-empty">总结结果会显示在这里</div>
    </div>

    <footer>我的第一个 AI 工具 · Flask + DeepSeek + 提示词设计</footer>
  </div>

  <script>
    var btn = document.getElementById('btn');
    var input = document.getElementById('input');
    var result = document.getElementById('result');
    var format = document.getElementById('format');
    var detail = document.getElementById('detail');
    var tone = document.getElementById('tone');

    btn.addEventListener('click', function () {
      var text = input.value.trim();
      if (!text) { alert('请先粘贴要总结的内容'); return; }

      btn.disabled = true;
      btn.textContent = '总结中，请稍候……';
      result.className = 'result-loading';
      result.textContent = '🤖 DeepSeek 正在思考……';

      // 把文章 + 3 个选项一起发给后端
      fetch('/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          format: format.value,
          detail: detail.value,
          tone: tone.value,
        }),
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        btn.disabled = false;
        btn.textContent = '✨ 开始总结';
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
        btn.textContent = '✨ 开始总结';
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


@app.route('/summarize', methods=['POST'])
def summarize():
    """接收文章和选项 → 拼成提示词 → 调用 DeepSeek → 返回总结"""
    # ① 拿到文章 + 3 个选项
    text = request.json.get('text', '').strip()
    if not text:
        return jsonify({'error': '请输入要总结的内容'}), 400

    fmt = request.json.get('format', 'points')
    det = request.json.get('detail', 'standard')
    tone = request.json.get('tone', 'formal')

    # ② 提示词设计的核心：把选项翻译成给大模型的指令
    system_prompt = (
        '你是一个擅长总结的助手。用中文回答。'
        + FORMATS.get(fmt, '')
        + DETAILS.get(det, '')
        + TONES.get(tone, '')
    )

    # ③ 调用 DeepSeek
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
                    {'role': 'user', 'content': '请把下面这段内容总结一下：\n\n' + text},
                ],
                'temperature': 0.7,
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
    app.run(port=5001, debug=True)
