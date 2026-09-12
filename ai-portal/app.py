# -*- coding: utf-8 -*-
"""
🤖 AI 工具门户 —— 合并版（用于部署上线）

把 3 个 AI 工具合并成 1 个应用，方便一次性部署到云端：
  1. ✨ AI 总结提炼
  2. 🌐 AI 翻译
  3. 💬 AI 聊天助手

为什么合并？部署时只需要 1 个网址、配 1 次密钥，比部署 3 个服务简单得多。

用到的技术：
  Flask + requests + DeepSeek 大模型

怎么运行（本地）：终端  python app.py  →  浏览器打开 http://127.0.0.1:5000
怎么运行（云端）：gunicorn app:app（Render 会自己启动）
"""
import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

app = Flask(__name__)

# ========== DeepSeek 配置 ==========
load_dotenv()   # 从 .env 文件读取 key（本地）；云端从环境变量读取
API_KEY = os.environ.get('DEEPSEEK_API_KEY')
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


# ========== 提示词设计：选项 → 指令片段 ==========

# 总结工具的 3 组选项
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

# 翻译工具的 3 组选项
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

# 公共样式，3 个工具共用（导航页单独写）
BASE_STYLE = """
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
"""

# ① 导航首页
HOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 工具集</title>
  <style>
    :root { --primary: #4f46e5; --primary-hover: #4338ca; --bg: #f4f5f7; --card: #ffffff; --border: #e5e7eb; --text: #1f2937; --muted: #6b7280; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif; background: var(--bg); color: var(--text); padding: 48px 16px; line-height: 1.7; }
    .container { max-width: 720px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 32px; }
    header h1 { font-size: 30px; font-weight: 700; }
    header h1 .emoji { display: block; font-size: 48px; margin-bottom: 4px; }
    header p { color: var(--muted); margin-top: 8px; font-size: 15px; }
    .grid { display: flex; flex-direction: column; gap: 14px; }
    a.card { display: block; background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 20px; text-decoration: none; color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all .15s; }
    a.card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    a.card .title { font-size: 18px; font-weight: 700; }
    a.card .desc { color: var(--muted); font-size: 14px; margin-top: 4px; }
    footer { text-align: center; color: #9ca3af; font-size: 13px; margin-top: 32px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="emoji">🤖</span>我的 AI 工具集</h1>
      <p>3 个 AI 工具，都由 DeepSeek 大模型驱动</p>
    </header>
    <div class="grid">
      <a class="card" href="/summary">
        <div class="title">✨ AI 总结提炼</div>
        <div class="desc">粘贴文章，一键总结，可调形式 / 详细 / 语气</div>
      </a>
      <a class="card" href="/translate">
        <div class="title">🌐 AI 翻译</div>
        <div class="desc">中英互译，可选风格、附重点词汇解释</div>
      </a>
      <a class="card" href="/chat">
        <div class="title">💬 AI 聊天助手</div>
        <div class="desc">像 ChatGPT 一样多轮对话，它记得你说过的话</div>
      </a>
    </div>
    <footer>我的 AI 作品集 · Flask + DeepSeek</footer>
  </div>
</body>
</html>"""

# ② AI 总结页面
SUMMARY_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 总结提炼工具</title>
  <style>""" + BASE_STYLE + """</style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="emoji">✨</span>AI 总结提炼工具</h1>
      <p>粘贴文章，选好形式 / 详细 / 语气，DeepSeek 帮你总结</p>
      <a href="/">← 返回 AI 工具集</a>
    </header>

    <div class="card">
      <textarea id="input" placeholder="把要总结的文章粘贴到这里，支持中文……"></textarea>

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

    <footer>AI 总结 · Flask + DeepSeek + 提示词设计</footer>
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

# ③ AI 翻译页面
TRANSLATE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 翻译工具</title>
  <style>""" + BASE_STYLE + """</style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="emoji">🌐</span>AI 翻译工具</h1>
      <p>粘贴文字，选好方向 / 风格 / 附加，DeepSeek 帮你翻译</p>
      <a href="/">← 返回 AI 工具集</a>
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

    <footer>AI 翻译 · Flask + DeepSeek + 角色设定</footer>
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

      fetch('/api/translate', {
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

# ④ AI 聊天页面
CHAT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 聊天助手</title>
  <style>
    :root { --primary: #4f46e5; --primary-hover: #4338ca; --bg: #f4f5f7; --card: #ffffff; --border: #e5e7eb; --text: #1f2937; --muted: #6b7280; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif; background: var(--bg); color: var(--text); padding: 32px 16px; line-height: 1.7; }
    .container { max-width: 680px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 20px; }
    header h1 { font-size: 28px; font-weight: 700; }
    header h1 .emoji { display: block; font-size: 44px; margin-bottom: 4px; }
    header p { color: var(--muted); margin-top: 6px; font-size: 15px; }
    header a { color: var(--primary); text-decoration: none; font-size: 14px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .chat-box { height: 420px; overflow-y: auto; padding: 6px; display: flex; flex-direction: column; gap: 12px; }
    .msg { display: flex; }
    .msg.user { justify-content: flex-end; }
    .msg.assistant { justify-content: flex-start; }
    .bubble { max-width: 78%; padding: 10px 14px; border-radius: 14px; font-size: 15px; white-space: pre-wrap; word-break: break-word; }
    .msg.user .bubble { background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
    .msg.assistant .bubble { background: #f3f4f6; color: var(--text); border-bottom-left-radius: 4px; }
    .empty-hint { text-align: center; color: #9ca3af; font-size: 14px; margin-top: 40px; }
    .input-row { display: flex; gap: 10px; margin-top: 14px; }
    .input-row input { flex: 1; border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; font-size: 15px; font-family: inherit; outline: none; }
    .input-row input:focus { border-color: var(--primary); }
    .input-row button { border: none; border-radius: 10px; padding: 0 22px; font-size: 15px; cursor: pointer; font-family: inherit; background: var(--primary); color: #fff; font-weight: 600; margin-top: 0; }
    .input-row button:hover { background: var(--primary-hover); }
    .input-row button:disabled { background: #c7d2fe; cursor: not-allowed; }
    footer { text-align: center; color: #9ca3af; font-size: 13px; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1><span class="emoji">💬</span>AI 聊天助手</h1>
      <p>像 ChatGPT 一样聊天，它记得你之前说过的话</p>
      <a href="/">← 返回 AI 工具集</a>
    </header>

    <div class="card">
      <div class="chat-box" id="chatBox">
        <div class="empty-hint" id="hint">👋 你好，我是你的 AI 助手，跟我聊聊吧</div>
      </div>
      <div class="input-row">
        <input type="text" id="input" placeholder="输入消息，回车发送……">
        <button id="send">发送</button>
      </div>
    </div>

    <footer>AI 聊天 · Flask + DeepSeek + 多轮对话</footer>
  </div>

  <script>
    var chatBox = document.getElementById('chatBox');
    var hint = document.getElementById('hint');
    var input = document.getElementById('input');
    var sendBtn = document.getElementById('send');

    // ★ 多轮对话的核心：这个数组存下所有聊天记录
    //   注意：变量名不能叫 history！因为浏览器已内置 window.history，
    //   用 var history = [] 覆盖不了它，会导致 history.push 报错
    var chatHistory = [];

    function addMsg(role, content) {
      if (hint) { hint.remove(); hint = null; }
      var wrap = document.createElement('div');
      wrap.className = 'msg ' + role;
      var bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.textContent = content;
      wrap.appendChild(bubble);
      chatBox.appendChild(wrap);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    function send() {
      var text = input.value.trim();
      if (!text) return;

      addMsg('user', text);
      input.value = '';
      chatHistory.push({ role: 'user', content: text });

      sendBtn.disabled = true;
      sendBtn.textContent = '…';

      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: chatHistory }),
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        sendBtn.disabled = false;
        sendBtn.textContent = '发送';
        if (data.error) {
          addMsg('assistant', '❌ ' + data.error);
        } else {
          addMsg('assistant', data.result);
          chatHistory.push({ role: 'assistant', content: data.result });
        }
      })
      .catch(function (err) {
        sendBtn.disabled = false;
        sendBtn.textContent = '发送';
        addMsg('assistant', '❌ 请求失败：' + err);
      });
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') send();
    });
  </script>
</body>
</html>"""


# ========== 路由 ==========

@app.route('/')
def home():
    """导航首页：3 个工具的入口"""
    return HOME_HTML


@app.route('/summary')
def summary_page():
    return SUMMARY_HTML


@app.route('/summarize', methods=['POST'])
def summarize():
    """接收文章和选项 → 拼提示词 → 调用 DeepSeek → 返回总结"""
    text = request.json.get('text', '').strip()
    if not text:
        return jsonify({'error': '请输入要总结的内容'}), 400

    fmt = request.json.get('format', 'points')
    det = request.json.get('detail', 'standard')
    tone = request.json.get('tone', 'formal')

    system_prompt = (
        '你是一个擅长总结的助手。用中文回答。'
        + FORMATS.get(fmt, '')
        + DETAILS.get(det, '')
        + TONES.get(tone, '')
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


@app.route('/translate')
def translate_page():
    return TRANSLATE_HTML


@app.route('/api/translate', methods=['POST'])
def translate():
    """接收文字和选项 → 拼提示词 → 调用 DeepSeek → 返回翻译"""
    text = request.json.get('text', '').strip()
    if not text:
        return jsonify({'error': '请输入要翻译的内容'}), 400

    direction = request.json.get('direction', 'zh2en')
    style = request.json.get('style', 'natural')
    extra = request.json.get('extra', 'none')

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
                'temperature': 0.3,
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


@app.route('/chat')
def chat_page():
    return CHAT_HTML


@app.route('/api/chat', methods=['POST'])
def chat():
    """接收完整对话历史 → 调用 DeepSeek → 返回 AI 回复"""
    history = request.json.get('history', [])
    if not history:
        return jsonify({'error': '消息为空'}), 400

    messages = [
        {'role': 'system', 'content': '你是一个友好、有帮助的 AI 助手。用中文回答，简洁清晰。'}
    ] + history

    try:
        resp = requests.post(
            API_URL,
            headers={
                'Authorization': 'Bearer ' + API_KEY,
                'Content-Type': 'application/json',
            },
            json={
                'model': MODEL,
                'messages': messages,
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
    app.run(port=5000, debug=True)
