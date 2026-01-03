import os
import sys
import runpy
from pathlib import Path
from types import ModuleType
from typing import Optional

import streamlit as st


def _ensure_sys_path(path: Path) -> None:
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


_ensure_sys_path(_root())


def _load_module_from_path(module_name: str, file_path: Path) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_streamlit_script(file_path: Path, working_dir: Optional[Path] = None) -> None:
    orig_set_page_config = st.set_page_config
    old_cwd = os.getcwd()
    try:
        st.set_page_config = lambda *args, **kwargs: None
        if working_dir is not None:
            os.chdir(str(working_dir))
        runpy.run_path(str(file_path), run_name="__main__")
    finally:
        st.set_page_config = orig_set_page_config
        os.chdir(old_cwd)


def _init_state() -> None:
    st.session_state.setdefault("raw_text", "")
    st.session_state.setdefault("clean_text", "")
    st.session_state.setdefault("sentences", [])
    st.session_state.setdefault("chapter_raw_texts", {})
    st.session_state.setdefault("chapter_clean_texts", {})
    st.session_state.setdefault("chapter_sentences", {})
    st.session_state.setdefault("shared_text", "")
    st.session_state.setdefault("campus_raw_text_for_nlp", "")


def _sync_nlp_source_text() -> None:
    text = st.session_state.get("raw_text", "")
    if isinstance(text, str):
        st.session_state["campus_raw_text_for_nlp"] = text


def _init_global_chat_state() -> None:
    st.session_state.setdefault("global_chat.messages", [])
    st.session_state.setdefault("global_chat.seeded", False)
    st.session_state.setdefault("global_chat.greeted_pages", [])
    st.session_state.setdefault("global_chat.input", "")
    st.session_state.setdefault("global_chat._greeting_migrated", False)

    if not st.session_state.get("global_chat._greeting_migrated", False):
        possible_pages = [
            "📈 段落关键词分析",
            "🧠 语义理解与概念关联",
            "📚 数据加载与预处理",
            "☁️ 智能词云生成",
            "📋 摘要与核心知识点",
            "📘 多类型习题生成",
            "🧩 标题生成与主题提炼",
            "🧬 视觉摘要生成器",
            "📉 梯度下降可视化",
            "👥 用户管理",
        ]
        greeting_texts = {str(_global_chat_greeting(p)).strip() for p in possible_pages}
        existing = st.session_state.get("global_chat.messages", [])
        if isinstance(existing, list) and existing:
            cleaned = []
            for m in existing:
                try:
                    role = str(m.get("role", "")).strip()
                    content = str(m.get("content", "")).strip()
                except Exception:
                    cleaned.append(m)
                    continue
                if role == "assistant" and content in greeting_texts:
                    continue
                cleaned.append(m)
            st.session_state["global_chat.messages"] = cleaned

        st.session_state["global_chat._greeting_migrated"] = True


def _global_chat_greeting(page: str) -> str:
    greetings = {
        "📈 段落关键词分析": "我是 TF-IDF/关键词分析学习助手。今天想从哪段文本开始提炼关键词与重点信息？",
        "🧠 语义理解与概念关联": "我是 Word2Vec 语义理解学习助手。今天想探索哪些词的相似词、类比关系或语义关联？",
        "📚 数据加载与预处理": "我是数据清洗与预处理助手。你想处理哪份讲义/章节？遇到了哪些清洗或分句问题？",
        "☁️ 智能词云生成": "我是词云与关键词可视化助手。你想突出哪些主题词？需要我帮你解读词云结果吗？",
        "📋 摘要与核心知识点": "我是摘要与核心知识点提炼助手。想生成多长的摘要？核心知识点需要偏概念还是偏方法步骤？",
        "📘 多类型习题生成": "我是习题助教。今天做点什么？你希望答案更偏理解、偏应用，还是偏总结对比？",
        "🧩 标题生成与主题提炼": "我是学术标题与关键词提炼助手。你希望生成什么样的标题？更偏学术严谨还是更偏友好？",
        "🧬 视觉摘要生成器": "我是视觉摘要生成助手。你想把哪段摘要转成更清晰的 Prompt 或视觉表达？",
        "📉 梯度下降可视化": "我是梯度下降学习助手。你想从直观理解、数学推导还是参数影响（学习率/初值）开始？",
        "👥 用户管理": "我是用户与权限管理助手。你想新增用户、调整权限，还是排查登录/角色问题？",
    }
    return greetings.get(page, "我是全局学习助手。今天想学点什么？")


def _global_chat_system_prompt(page: str) -> str:
    return (
        "你是一个严谨、友好、面向学习的助教型对话助手。"
        "你的任务是围绕本系统的页面功能与相关知识点提供解释、引导与答疑。"
        f"当前用户所在页面：{page}。"
        "回答要简洁、有条理，必要时给出可操作步骤。"
    )


def _render_global_chat_sidebar(
    page: str,
    *,
    title: str = "💬 全局对话",
    use_expander: bool = True,
    expanded: bool = True,
    show_page_greeting: bool = True,
) -> None:
    from aid_integrated.campus import llm_helpers

    messages = st.session_state.get("global_chat.messages", [])
    if use_expander:
        container = st.expander(title, expanded=expanded)
    else:
        container = st.container()
        container.markdown(f"#### {title}")

    with container:
        if show_page_greeting:
            greeting_text = _global_chat_greeting(page)
            try:
                with st.chat_message("assistant"):
                    st.markdown(greeting_text)
            except Exception:
                st.markdown(f"**assistant**：{greeting_text}")

        if messages:
            for m in messages:
                role = str(m.get("role", "assistant"))
                content = str(m.get("content", ""))
                try:
                    with st.chat_message(role):
                        st.markdown(content)
                except Exception:
                    st.markdown(f"**{role}**：{content}")
        else:
            st.caption("在这里你可以和学习助手对话，本助手基于DeepSeek大语言模型。")

        with st.form("global_chat.form", clear_on_submit=True):
            st.text_area(
                "",
                key="global_chat.input",
                placeholder="输入消息…",
                height=80,
                label_visibility="collapsed",
            )
            c1, c2 = st.columns([1, 1])
            try:
                send = c1.form_submit_button("发送", type="primary", width="stretch", key="global_chat.send")
            except TypeError:
                send = c1.form_submit_button(
                    "发送", type="primary", use_container_width=True, key="global_chat.send"
                )
            try:
                clear = c2.form_submit_button("清空", width="stretch", key="global_chat.clear")
            except TypeError:
                clear = c2.form_submit_button("清空", use_container_width=True, key="global_chat.clear")

        if clear:
            st.session_state["global_chat.messages"] = []
            st.session_state["global_chat.seeded"] = False
            st.session_state["global_chat.greeted_pages"] = []
            st.rerun()

        if send:
            user_text = str(st.session_state.get("global_chat.input", "")).strip()
            if not user_text:
                st.warning("请输入内容后再发送")
            else:
                st.session_state["global_chat.messages"].append({"role": "user", "content": user_text})
                try:
                    history = st.session_state["global_chat.messages"][-20:]
                    api_messages = [{"role": "system", "content": _global_chat_system_prompt(page)}] + history
                    reply = llm_helpers.chat_completion(api_messages, temperature=0.5, max_tokens=800)
                    st.session_state["global_chat.messages"].append({"role": "assistant", "content": reply})
                except RuntimeError as e:
                    st.error(
                        "DeepSeek 未配置或不可用，请在 `.streamlit/secrets.toml` 配置 `DEEPSEEK_API_KEY` 后重试。"
                    )
                    st.caption(str(e))
                except Exception as e:
                    st.error(f"对话请求失败：{str(e)}")
                st.rerun()


def _hide_builtin_pages_nav() -> None:
    # 让“未登录时 sidebar 出现一堆内置页面列表”彻底消失
    st.markdown(
        """
        <style>
          [data-testid="stSidebarNav"] {display: none !important;}
          [data-testid="stSidebarNavItems"] {display: none !important;}
          [data-testid="stSidebarNavSeparator"] {display: none !important;}
          [data-testid="stSidebarNavLink"] {display: none !important;}
          [data-testid="stPageNav"] {display: none !important;}
          [data-testid="stPageNavLink"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _hide_sidebar_when_logged_out() -> None:
    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"] {display: none !important;}
          [data-testid="collapsedControl"] {display: none !important;}
          button[data-testid="collapsedControl"] {display: none !important;}
          [data-testid="stSidebarCollapsedControl"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _render_global_css() -> None:
    global_css = """
    <style>
    /* 全局字体与间距优化 */
    body {font-family: "Microsoft YaHei", sans-serif; line-height: 1.6;}
    .stApp {padding: 1rem 2rem;}
    /* 隐藏默认页眉页脚 */
    footer {visibility: hidden;}
    /* 标题样式统一 */
    .stApp > header + div > div > h1 {border-bottom: none !important;}
    h2 {color: #1e3a8a; border-bottom: 2px solid #dbeafe; padding-bottom: 8px; margin-top: 20px;}
    h3 {color: #334155;}
    h4 {color: #475569;}
    /* 按钮全局样式 */
    .stButton > button {border-radius: 8px; transition: all 0.3s ease;}
    .stButton > button:hover {transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    .stButton > button[type="primary"] {background-color: #3b82f6 !important; color: white !important;}
    .stButton > button[type="secondary"] {background-color: #f87171 !important; color: white !important;}
    /* 输入框/选择框样式 */
    .stTextInput > div > div, .stSelectbox > div > div, .stMultiselect > div > div {
        border-radius: 8px; border: 1px solid #e2e8f0;
    }
    /* -------------- 单选框样式区分：侧边栏（默认） + 页面内（美观） -------------- */
    /* 1. 侧边栏内的单选框：保持默认样式 */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: normal;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        padding: initial;
        border-radius: initial;
        border: none;
        background-color: transparent;
        cursor: pointer;
        transition: none;
    }
    section[data-testid="stSidebar"] .stRadio > div > label[data-selected="true"] {
        border-color: initial;
        background-color: transparent;
        font-weight: normal;
    }
    /* 2. 页面内的单选框：美观卡片样式 */
    .stAppMain .stRadio > div {
        gap: 1rem;
        display: flex;
        flex-direction: column; /* 垂直排列更整洁 */
    }
    .stAppMain .stRadio > div > label {
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background-color: #f8fafc;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .stAppMain .stRadio > div > label:hover {
        border-color: #93c5fd;
        background-color: #f0f9ff;
    }
    .stAppMain .stRadio > div > label[data-selected="true"] {
        border-color: #3b82f6;
        background-color: #eff6ff;
        font-weight: 500;
    }
    /* 文件上传器：恢复默认样式（去掉虚线和背景色自定义） */
    div[data-testid="stFileUploader"] {
        border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;
        background-color: white; transition: none;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #e2e8f0; background-color: white;
    }
    /* 文本框样式 */
    div[data-testid="stTextArea"] textarea {
        border-radius: 8px; font-family: "Microsoft YaHei", monospace;
        background-color: #fafafa; border: 1px solid #e5e7eb;
    }
    /* 展开器样式 */
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0; border-radius: 10px; background-color: #f8fafc;
        margin-bottom: 1rem;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600; color: #1e40af;
    }
    /* 提示框样式 */
    .stInfo, .stSuccess, .stWarning, .stError {
        border-radius: 10px; padding: 12px;
    }
    .stSuccess {background-color: #dcfce7 !important; border: 1px solid #a7f3d0 !important; color: #166534 !important;}
    .stInfo {background-color: #eff6ff !important; border: 1px solid #bfdbfe !important; color: #1e40af !important;}
    .stWarning {background-color: #fffbeb !important; border: 1px solid #fcd34d !important;}
    .stError {background-color: #fef2f2 !important; border: 1px solid #fca5a5 !important;}
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc; border-right: 1px solid #e2e8f0;
    }
    .stSidebar > div > div > div > div {padding: 1rem;}
    </style>
    """
    st.markdown(global_css, unsafe_allow_html=True)


def main() -> None:
    # ✅ set_page_config 必须尽早调用，且只调用一次
    st.set_page_config(page_title="基于NLP的讲义助学工具", layout="wide", initial_sidebar_state="expanded")

    _render_global_css()

    # ✅ 登录前就隐藏内置多页面导航（否则登录页会露出那一堆“奇怪页面”）
    _hide_builtin_pages_nav()

    # ✅ auth 门禁放在 main 里，避免 import 时产生副作用
    from aid_integrated.auth.service import ensure_auth_state, logout_user
    from aid_integrated.auth.ui import render_login_register

    ensure_auth_state()

    # ✅ 未登录：只渲染登录/注册页，并停止后续渲染
    if not st.session_state.get("auth.logged_in", False):
        _hide_sidebar_when_logged_out()
        render_login_register()
        st.stop()

    # ✅ 已登录：显示用户信息 + 退出按钮
    with st.sidebar:
        st.markdown(f"已登录：**{st.session_state.get('auth.username','')}**")
        role = st.session_state.get("auth.role", "user")
        st.caption(f"角色：{role}")
        if st.button("退出登录", width="stretch"):
            logout_user()
            st.session_state.pop("global_chat.messages", None)
            st.session_state.pop("global_chat.seeded", None)
            st.session_state.pop("global_chat.greeted_pages", None)
            st.session_state.pop("global_chat.input", None)
            st.rerun()
        
    # ---- 登录后才初始化你系统需要的 state ----
    _init_state()
    _sync_nlp_source_text()
    _init_global_chat_state()

    st.sidebar.title("基于NLP的讲义助学工具")

    # 一级模块列表
    modules = [
        "🏠 系统介绍",
        "📘 讲义理解",
        "📊 文本重点与结构分析",
        "🧠 语义理解与概念关联",
        "✨ 内容生成与学习辅助",
        "📉 算法原理与可视化",
    ]
    if st.session_state.get("auth.role") == "admin":
        modules.append("🛡️ 用户与权限")

    module = st.sidebar.selectbox("选择板块", modules, index=0)

    # 二级页面映射
    module_to_pages = {
        "🏠 系统介绍": ["🏠 系统介绍"],
        "📘 讲义理解": ["📚 数据加载与预处理", "☁️ 智能词云生成", "📋 摘要与核心知识点"],
        "📊 文本重点与结构分析": ["📈 段落关键词分析","📘 多类型习题生成"],
        "🧠 语义理解与概念关联": ["🧠 语义理解与概念关联"],
        "✨ 内容生成与学习辅助": ["🧩 标题生成与主题提炼", "🧬 视觉摘要生成器"],
        "📉 算法原理与可视化": ["📉 梯度下降可视化"],
        "🛡️ 用户与权限": ["👥 用户管理"],
    }

    page = st.sidebar.radio("选择功能", module_to_pages[module], index=0)
    
    with st.sidebar:
        try:
            st.image(
                "auth/image.png",  # 替换为你的logo路径
                width="stretch",
                caption="NLP 讲义助学工具"
            )
        except FileNotFoundError:
            st.markdown(
                "<div style='text-align: center; color: #666; font-size: 12px;'>Logo 加载中</div>",
                unsafe_allow_html=True
            )

    chat_enabled = page != "🏠 系统介绍"

    if chat_enabled:
        _, icon_col = st.columns([0.7, 0.3])
        with icon_col:
            try:
                pop = st.popover("💬有知识不懂？Click me！", use_container_width=True)
            except TypeError:
                pop = st.popover("💬有知识不懂？Click me！")
            with pop:
                _render_global_chat_sidebar(page, title="💬 学习助教对话", use_expander=False)

    page_to_render = {
        "🏠 系统介绍": "aid_integrated.pages.index",
        "📚 数据加载与预处理": "aid_integrated.pages.campus_upload_preprocess",
        "☁️ 智能词云生成": "aid_integrated.pages.campus_wordcloud",
        "📋 摘要与核心知识点": "aid_integrated.pages.campus_summary_core",
        "📈 段落关键词分析": "aid_integrated.pages.nlp_tfidf",
        "📘 多类型习题生成":"aid_integrated.pages.campus_question",
        "🧠 语义理解与概念关联": "aid_integrated.pages.nlp_word2vec",
        "🧩 标题生成与主题提炼": "aid_integrated.pages.c1218_titlegen",
        "🧬 视觉摘要生成器": "aid_integrated.pages.c1218_tti",
        "📉 梯度下降可视化": "aid_integrated.pages.campus_gradient_descent",
        "👥 用户管理": "aid_integrated.pages.admin_users",
    }

    mod_path = page_to_render[page]
    module_obj = __import__(mod_path, fromlist=["render"])

    module_obj.render()



if __name__ == "__main__":
    main()
