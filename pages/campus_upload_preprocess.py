import streamlit as st
from io import BytesIO

from aid_integrated.campus import file_utils, text_cleaner


def _load_from_bytes(name: str, data: bytes) -> str:
    buf = BytesIO(data)
    buf.name = name
    return file_utils.load_file(buf)


def render() -> None:

    st.markdown(
        "<h2 style='color:#1565c0; margin-bottom: 10px;'>📤 数据加载与预处理</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
        box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
        <div style="font-size:16px;color:#1e293b;line-height:1.8;">
            <b style="font-size:18px;color:#1e40af;">这个功能能帮你做什么？</b><br/>
            <span style="color:#2563eb;font-weight:700;">📂 批量上传章节文件</span>：支持多文件同时上传，每个文件对应一个课程章节<br/>
            <span style="color:#2563eb;font-weight:700;">🧹 统一清洗文本</span>：自动去除冗余格式、过滤无效内容<br/>
            <span style="color:#2563eb;font-weight:700;">📝 标准化文本格式</span>：将不同类型文件（TXT/PDF/DOCX）转换为统一的可处理文本<br/>
            <span style="color:#2563eb;font-weight:700;">🔧 自定义预处理规则</span>：可按需选择「数字处理」「停用词过滤」等参数
        </div>
        <div style="margin-top:16px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
            💡 <b>停用词说明</b>：指"的、了、是、在"等无实际语义的高频词，过滤后可聚焦核心知识点，提升词云/摘要的准确性<br/>
            💡 <b>功能依赖提示</b>：先完成此步骤，后续的「词云生成」「知识点提取」功能才能使用哦！
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "campus_uploaded_files_bytes" not in st.session_state:
        st.session_state["campus_uploaded_files_bytes"] = {}

    c1, c2 = st.columns([1, 1])
    with c2:
        if st.button(
            "🗑️ 清空已缓存文件与处理结果",
            width="stretch",
            type="secondary",
            help="清空后需重新上传文件"
        ):
            st.session_state["campus_uploaded_files_bytes"] = {}
            st.session_state["chapter_raw_texts"] = {}
            st.session_state["chapter_clean_texts"] = {}
            st.session_state["chapter_sentences"] = {}
            st.session_state["raw_text"] = ""
            st.session_state["clean_text"] = ""
            st.session_state["sentences"] = []
            st.session_state.pop("campus_wordcloud_results", None)
            st.session_state.pop("campus_generated_results", None)
            st.rerun()

    st.markdown(
        "<div style='font-size:15px; color:#444; margin: 10px 0;'>上传讲义文件（支持txt/docx/pdf/csv，可多选，每文件对应一个章节）</div>",
        unsafe_allow_html=True
    )
    uploaded_files = st.file_uploader(
        "",  
        type=["txt", "docx", "pdf", "csv"],
        accept_multiple_files=True,
        key="campus_uploader",
        label_visibility="collapsed"
    )

    if uploaded_files:
        for f in uploaded_files:
            try:
                st.session_state["campus_uploaded_files_bytes"][f.name] = f.getvalue()
            except Exception as e:
                st.error(f"缓存文件失败：{f.name}：{e}")

    cached_bytes = st.session_state.get("campus_uploaded_files_bytes", {})
    if cached_bytes:
        if not st.session_state.get("chapter_raw_texts"):
            st.session_state["chapter_raw_texts"] = {}
            global_raw_text = ""
            for name, data in cached_bytes.items():
                with st.spinner(f"正在读取文件：{name}..."):
                    try:
                        raw_text = _load_from_bytes(name, data)
                    except Exception as e:
                        st.error(f"读取文件失败：{name}：{e}")
                        continue
                st.session_state["chapter_raw_texts"][name] = raw_text
                global_raw_text += raw_text + "\n\n"
            st.session_state["raw_text"] = global_raw_text

        st.markdown(
            f"<div style='background:#e8f5e9; padding:10px; border-radius:8px; color:#2e7d32; margin:10px 0;'>✅ 已缓存 {len(cached_bytes)} 个文件：切换页面后不会丢失。</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<div style='font-size:16px; color:#1565c0; margin:15px 0 10px 0;'><b>📄 原始文本预览</b></div>",
            unsafe_allow_html=True
        )
        for name, raw_text in st.session_state.get("chapter_raw_texts", {}).items():
            with st.expander(f"{name}", expanded=False):
                preview = raw_text[:1500] + ("..." if len(raw_text) > 1500 else "")
                st.text_area(
                    label=f"原始文本 - {name}",
                    value=preview,
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )

        st.markdown(
            "<div style='font-size:16px; color:#1565c0; margin:20px 0 10px 0;'><b>⚙️ 预处理参数（所有章节共用）</b></div>",
            unsafe_allow_html=True
        )
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            lower_case = st.checkbox("转小写", value=True, help="将文本统一转为小写")
        with col2:
            remove_formula = st.checkbox("移除公式", value=True, help="去除文本中的公式内容")
        with col3:
            num_process = st.selectbox("数字处理", ["保留", "去除"], index=0, help="选择保留或去除数字")
        with col4:
            remove_stopwords = st.checkbox("去停用词", value=True, help="过滤无实际语义的高频词")

        if st.button(
            "执行文本清洗（所有章节）",
            type="primary",
            width="stretch",
            help="对所有上传的章节文本执行清洗"
        ):
            global_clean_text = ""
            global_sentences = []

            with st.spinner("正在清洗所有章节文本..."):
                for file_name, raw_text in st.session_state.get("chapter_raw_texts", {}).items():
                    try:
                        cleaned_text, sentences = text_cleaner.process_text_cleaning(
                            raw_text,
                            lower_case=lower_case,
                            remove_formula=remove_formula,
                            num_process=num_process,
                            remove_stopwords=remove_stopwords,
                        )
                    except Exception as e:
                        st.error(f"清洗失败：{file_name}：{e}")
                        continue

                    st.session_state["chapter_clean_texts"][file_name] = cleaned_text
                    st.session_state["chapter_sentences"][file_name] = sentences
                    global_clean_text += cleaned_text + "\n\n"
                    global_sentences.extend(sentences)

            st.session_state["clean_text"] = global_clean_text
            st.session_state["sentences"] = global_sentences

            st.markdown(
                f"<div style='background:#e8f5e9; padding:10px; border-radius:8px; color:#2e7d32; margin:15px 0;'>✅ 文本清洗完成：共处理 {len(st.session_state['chapter_clean_texts'])} 个章节</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                "<div style='font-size:16px; color:#1565c0; margin:20px 0 10px 0;'><b>🧹 清洗后文本预览</b></div>",
                unsafe_allow_html=True
            )
            for file_name, cleaned_text in st.session_state.get("chapter_clean_texts", {}).items():
                with st.expander(f"{file_name}", expanded=False):
                    display_clean = str(cleaned_text)[:1500] + ("..." if len(str(cleaned_text)) > 1500 else "")
                    st.text_area(
                        label=f"清洗后文本 - {file_name}",
                        value=display_clean,
                        height=200,
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            with st.expander("全局合并后清洗文本", expanded=False):
                text = st.session_state.get("clean_text", "")
                if isinstance(text, str) and text.strip():
                    st.text_area(
                        label="全局清洗文本",
                        value=text[:3000] + ("..." if len(text) > 3000 else ""),
                        height=240,
                        disabled=True,
                        label_visibility="collapsed"
                    )
                else:
                    st.info("暂无全局清洗文本")

    else:
        st.markdown(
            "<div style='background:#f5f5f5; padding:12px; border-radius:8px; color:#666; margin:15px 0;'>💡 提示：上传文件后会自动缓存，即使切换页面也不会丢失。</div>",
            unsafe_allow_html=True
        )

    raw_text = st.session_state.get("raw_text", "")
    clean_text = st.session_state.get("clean_text", "")
    if isinstance(raw_text, str) and raw_text.strip():
        st.markdown(
            "<div style='margin:20px 0; color:#444;'>已准备好 NLP 实验的初始语料（默认使用原始文本以保留段落结构）。"
            "可以进入「📈 段落关键词分析」或「🧠 语义向量探索」开始实验；"
            "NLP 页面里的文本可单独编辑，不会反向影响本页。</div>",
            unsafe_allow_html=True
        )

    with st.expander("🔎 NLP 实验初始语料预览（只读）", expanded=False):
        preview_text = raw_text if isinstance(raw_text, str) and raw_text.strip() else clean_text
        if isinstance(preview_text, str) and preview_text.strip():
            st.text_area(
                "NLP 初始语料预览",
                value=preview_text[:3000] + ("..." if len(preview_text) > 3000 else ""),
                height=220,
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            st.info("尚未准备 NLP 初始语料：请先上传文件（可选：再执行清洗）。")