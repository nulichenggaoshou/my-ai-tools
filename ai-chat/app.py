# -*- coding: utf-8 -*-
"""
💬 AI 聊天助手 —— 我的第三个 AI 工具

和总结/翻译最大的不同：这是「多轮对话」。
  之前是「问一句答一句，答完就失忆」；
  现在 AI 要记得之前的对话，才能接得上话。

多轮对话的秘密：
  前端把之前的聊天记录（一个数组）每次都完整地重新发给大模型，
  大模型看到完整历史，自然就「记得」之前聊过什么了。

用到的技术：
  Flask + requests + DeepSeek 大模型

怎么运行：终端  python app.py  →  浏览器打开 http://127.0.0.1:5003
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


# ========== 网页界面（前端） ==========
HOME_HTML = """<!DOCTYPE html>
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

    /* 聊天区 */
    .chat-box { height: 420px; overflow-y: auto; padding: 6px; display: flex; flex-direction: column; gap: 12px; }
    .msg { display: flex; }
    .msg.user { justify-content: flex-end; }
    .msg.assistant { justify-content: flex-start; }
    .bubble {
      max-width: 78%; padding: 10px 14px; border-radius: 14px;
      font-size: 15px; white-space: pre-wrap; word-break: break-word;
    }
    .msg.user .bubble { background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
    .msg.assistant .bubble { background: #f3f4f6; color: var(--text); border-bottom-left-radius: 4px; }
    .empty-hint { text-align: center; color: #9ca3af; font-size: 14px; margin-top: 40px; }

    /* 输入区 */
    .input-row { display: flex; gap: 10px; margin-top: 14px; }
    .input-row input {
      flex: 1; border: 1px solid var(--border); border-radius: 10px;
      padding: 12px 14px; font-size: 15px; font-family: inherit; outline: none;
    }
    .input-row input:focus { border-color: var(--primary); }
    .input-row button {
      border: none; border-radius: 10px; padding: 0 22px; font-size: 15px;
      cursor: pointer; font-family: inherit; background: var(--primary); color: #fff; font-weight: 600;
    }
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
      <a href="../index.html">← 返回工具集</a>
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

    <footer>我的第三个 AI 工具 · Flask + DeepSeek + 多轮对话</footer>
  </div>

  <script>
    var chatBox = document.getElementById('chatBox');
    var hint = document.getElementById('hint');
    var input = document.getElementById('input');
    var sendBtn = document.getElementById('send');

    // ★ 多轮对话的核心：这个数组存下所有聊天记录
    //   每次发消息，都把「整个历史」一起发给后端
    //   注意：变量名不能叫 history！因为浏览器已内置 window.history（浏览历史），
    //   用 var history = [] 覆盖不了它，会导致 history.push 报错
    var chatHistory = [];

    // 往聊天区加一条消息（用 textContent，安全，不会执行 HTML）
    function addMsg(role, content) {
      if (hint) { hint.remove(); hint = null; }
      var wrap = document.createElement('div');
      wrap.className = 'msg ' + role;
      var bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.textContent = content;
      wrap.appendChild(bubble);
      chatBox.appendChild(wrap);
      chatBox.scrollTop = chatBox.scrollHeight;   // 自动滚到最新消息
    }

    function send() {
      var text = input.value.trim();
      if (!text) return;

      // ① 先把用户说的话显示出来 + 存进历史
      addMsg('user', text);
      input.value = '';
      chatHistory.push({ role: 'user', content: text });

      sendBtn.disabled = true;
      sendBtn.textContent = '…';

      // ② 把「整个历史」发给后端
      fetch('/chat', {
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
          // ③ 把 AI 的回复显示出来 + 也存进历史
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
    // 回车也能发送
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') send();
    });
  </script>
</body>
</html>"""


@app.route('/')
def home():
    return HOME_HTML


@app.route('/chat', methods=['POST'])
def chat():
    """接收完整对话历史 → 调用 DeepSeek → 返回 AI 回复"""
    # ① 拿到前端传来的完整对话历史（一个数组）
    history = request.json.get('history', [])
    if not history:
        return jsonify({'error': '消息为空'}), 400

    # ② 在历史最前面加一条 system，告诉它「你是什么角色」
    messages = [
        {'role': 'system', 'content': '你是一个友好、有帮助的 AI 助手。用中文回答，简洁清晰。'}
    ] + history

    # ③ 把完整 messages（含历史）发给 DeepSeek —— 这就是它「记得」的原因
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
    app.run(port=5003, debug=True)
