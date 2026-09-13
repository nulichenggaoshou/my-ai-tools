# -*- coding: utf-8 -*-
"""
🤖 AI 工具集 —— Streamlit 版（免费云端部署用）

为什么从 Flask 换成 Streamlit？
  PythonAnywhere 免费账户连外部 API 要申请白名单（慢），
  而 Streamlit Cloud 免费、不用绑卡、能直接连 DeepSeek，马上能上线。
  另外 Streamlit 是 AI 应用领域超热门的框架，多会一个求职更加分。

3 个工具：
  1. ✨ AI 总结提炼
  2. 🌐 AI 翻译
  3. 💬 AI 聊天助手

用到的技术：
  Streamlit + requests + DeepSeek 大模型

本地运行：终端  streamlit run streamlit_app.py
云端运行：Streamlit Cloud 自动部署
"""
import os
import requests
import streamlit as st

# ========== DeepSeek 配置 ==========
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"


def get_api_key():
    """读取 API key：本地用 .env / 环境变量，云端用 Streamlit secrets"""
    key = os.environ.get('DEEPSEEK_API_KEY')
    if not key:
        try:
            key = st.secrets['DEEPSEEK_API_KEY']
        except Exception:
            key = None
    return key


API_KEY = get_api_key()


def call_deepseek(messages, temperature=0.7):
    """调用 DeepSeek，传入消息列表，返回回复文本"""
    resp = requests.post(
        API_URL,
        headers={
            'Authorization': 'Bearer ' + API_KEY,
            'Content-Type': 'application/json',
        },
        json={'model': MODEL, 'messages': messages, 'temperature': temperature},
        timeout=60,
    )
    data = resp.json()
    if resp.status_code != 200:
        raise Exception('调用失败：' + str(data))
    return data['choices'][0]['message']['content']


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


# ========== 页面 ==========
st.set_page_config(page_title='我的 AI 工具集', page_icon='🤖')

st.title('🤖 我的 AI 工具集')
st.caption('3 个 AI 工具，都由 DeepSeek 大模型驱动')

tool = st.sidebar.radio('选择工具', ['✨ AI 总结提炼', '🌐 AI 翻译', '💬 AI 聊天助手'])
st.sidebar.markdown('---')
st.sidebar.caption('作品集 · Streamlit + DeepSeek')

# ---- ① AI 总结提炼 ----
if tool == '✨ AI 总结提炼':
    st.header('✨ AI 总结提炼')
    text = st.text_area('把要总结的文章粘贴到这里', height=200)

    c1, c2, c3 = st.columns(3)
    with c1:
        fmt = st.selectbox('形式', ['要点列表', '一段话', '一句话'])
    with c2:
        det = st.selectbox('详细', ['简短', '标准', '详细'])
    with c3:
        tone = st.selectbox('语气', ['正式', '口语', '精炼'])

    fmt_map = {'要点列表': 'points', '一段话': 'paragraph', '一句话': 'one'}
    det_map = {'简短': 'brief', '标准': 'standard', '详细': 'detailed'}
    tone_map = {'正式': 'formal', '口语': 'casual', '精炼': 'concise'}

    if st.button('✨ 开始总结', type='primary'):
        if not text.strip():
            st.warning('请先粘贴要总结的内容')
        else:
            with st.spinner('🤖 DeepSeek 正在思考……'):
                try:
                    system_prompt = (
                        '你是一个擅长总结的助手。用中文回答。'
                        + FORMATS[fmt_map[fmt]]
                        + DETAILS[det_map[det]]
                        + TONES[tone_map[tone]]
                    )
                    result = call_deepseek([
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': '请把下面这段内容总结一下：\n\n' + text},
                    ], temperature=0.7)
                    st.write(result)
                except Exception as e:
                    st.error('出错了：' + str(e))

# ---- ② AI 翻译 ----
elif tool == '🌐 AI 翻译':
    st.header('🌐 AI 翻译')
    text = st.text_area('把要翻译的文字粘贴到这里', height=200)

    c1, c2, c3 = st.columns(3)
    with c1:
        direction = st.selectbox('方向', ['中 → 英', '英 → 中'])
    with c2:
        style = st.selectbox('风格', ['地道自然', '直译准确'])
    with c3:
        extra = st.selectbox('附加', ['只翻译', '翻译 + 重点词汇'])

    dir_map = {'中 → 英': 'zh2en', '英 → 中': 'en2zh'}
    style_map = {'地道自然': 'natural', '直译准确': 'literal'}
    extra_map = {'只翻译': 'none', '翻译 + 重点词汇': 'words'}

    if st.button('🌐 开始翻译', type='primary'):
        if not text.strip():
            st.warning('请先粘贴要翻译的内容')
        else:
            with st.spinner('🤖 DeepSeek 正在翻译……'):
                try:
                    system_prompt = (
                        '你是一名专业翻译，精通中英文。'
                        + DIRECTIONS[dir_map[direction]]
                        + STYLES[style_map[style]]
                        + EXTRAS[extra_map[extra]]
                    )
                    result = call_deepseek([
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': text},
                    ], temperature=0.3)
                    st.write(result)
                except Exception as e:
                    st.error('出错了：' + str(e))

# ---- ③ AI 聊天助手 ----
else:
    st.header('💬 AI 聊天助手')
    st.caption('像 ChatGPT 一样聊天，它记得你之前说过的话')

    # 多轮对话：用 session_state 保存历史（刷新页面也不会丢）
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # 先显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])

    # 输入框
    if prompt := st.chat_input('输入消息，回车发送……'):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.write(prompt)
        with st.chat_message('assistant'):
            with st.spinner('思考中……'):
                try:
                    full = [
                        {'role': 'system', 'content': '你是一个友好、有帮助的 AI 助手。用中文回答，简洁清晰。'}
                    ] + st.session_state.messages
                    reply = call_deepseek(full, temperature=0.7)
                    st.write(reply)
                    st.session_state.messages.append({'role': 'assistant', 'content': reply})
                except Exception as e:
                    st.error('出错了：' + str(e))
