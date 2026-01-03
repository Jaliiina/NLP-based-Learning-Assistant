import streamlit as st
from io import BytesIO

from aid_integrated.campus import wordcloud_utils


def _fig_to_png_bytes(fig) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    return buf.getvalue()


def render() -> None:
    st.header("☁️ 智能词云生成")

    st.markdown(
        """
        <div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
        box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
        <div style="font-size:16px;color:#1e293b;line-height:1.8;">
            <b style="font-size:18px;color:#1e40af;">这个功能能帮你做什么？</b><br/>
            <span style="color:#2563eb;font-weight:700;">📊 按章节生成词云</span>：为每个上传的章节文件生成独立词云，直观展示各章节核心词汇<br/>
            <span style="color:#2563eb;font-weight:700;">⚖️ 权重驱动的词云</span>：基于算法计算词汇重要性，核心词汇显示更大更突出<br/>
            <span style="color:#2563eb;font-weight:700;">🎨 自定义词云样式</span>：可调整背景色、最大词数<br/>
            <span style="color:#2563eb;font-weight:700;">🌐 全局词云生成</span>：合并所有章节，生成整份讲义的核心词汇词云
        </div>
        <div style="margin-top:16px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
            💡 <b>TF-IDF 模型：</b>侧重「区分度」→ 找出本章节独有的核心词<br/>
            💡 <b>TextRank 模型：</b>侧重「重要性」→ 找出本章节内最核心的通用词<br/>
            ✨ 选择建议：想区分各章节特色用TF-IDF，想找全局核心用TextRank
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("campus_wordcloud_results", {})

    has_chapter_data = bool(st.session_state.get("chapter_clean_texts"))
    has_global_data = bool(isinstance(st.session_state.get("clean_text"), str) and st.session_state["clean_text"].strip())

    if not has_chapter_data and not has_global_data:
        st.warning("⚠️ 请先在「📚 数据加载与预处理」上传并清洗文本！")
        return

    generate_mode = st.radio(
        "生成模式",
        ["按章节生成（每个文件一张词云）", "全局生成（所有文件合并）"],
        index=0 if has_chapter_data else 1,
    )

    st.subheader("⚙️ 词云参数")
    col1, col2, col3 = st.columns(3)
    with col1:
        weight_method = st.radio("权重模型", ["TF-IDF", "TextRank"], index=0)
    with col2:
        bg_color = st.color_picker("背景颜色", value="#ffffff")
    with col3:
        max_words = st.slider("最大词数", 50, 500, 200, 50)

    if st.button("生成智能词云", type="primary", width="stretch"):
        results: dict = {
            "generate_mode": generate_mode,
            "weight_method": weight_method,
            "bg_color": bg_color,
            "max_words": int(max_words),
            "chapter": {},
            "global": None,
        }
        if generate_mode == "按章节生成（每个文件一张词云）" and has_chapter_data:
            with st.spinner("正在为每个章节生成词云..."):
                for idx, (file_name, cleaned_text) in enumerate(st.session_state["chapter_clean_texts"].items(), 1):
                    if not str(cleaned_text).strip():
                        st.warning(f"章节 {idx}：{file_name} 无有效文本，跳过！")
                        continue

                    if weight_method == "TF-IDF":
                        word2weight = wordcloud_utils.get_tfidf_weights(cleaned_text)
                    else:
                        word2weight = wordcloud_utils.get_textrank_weights(cleaned_text)

                    if not word2weight:
                        st.warning(f"章节 {idx}：{file_name} 无有效词汇生成词云！")
                        continue

                    fig = wordcloud_utils.generate_weighted_wordcloud(word2weight, bg_color, max_words)
                    results["chapter"][file_name] = _fig_to_png_bytes(fig)

        elif generate_mode == "全局生成（所有文件合并）" and has_global_data:
            with st.spinner("正在生成全局词云..."):
                clean_text = st.session_state["clean_text"]
                if weight_method == "TF-IDF":
                    word2weight = wordcloud_utils.get_tfidf_weights(clean_text)
                else:
                    word2weight = wordcloud_utils.get_textrank_weights(clean_text)

                if not word2weight:
                    st.warning("无有效词汇生成词云！")
                    return

                fig = wordcloud_utils.generate_weighted_wordcloud(word2weight, bg_color, max_words)
                results["global"] = _fig_to_png_bytes(fig)

        st.session_state["campus_wordcloud_results"] = results

    results = st.session_state.get("campus_wordcloud_results")
    if isinstance(results, dict) and (results.get("chapter") or results.get("global")):
        st.divider()
        st.subheader("📌 生成结果（已缓存）")
        if results.get("generate_mode"):
            st.caption(
                f"模式：{results.get('generate_mode')}｜权重模型：{results.get('weight_method')}｜背景：{results.get('bg_color')}｜最大词数：{results.get('max_words')}"
            )

        if results.get("chapter"):
            for idx, (file_name, png) in enumerate(results["chapter"].items(), 1):
                st.subheader(f"📖 章节 {idx}：{file_name}")
                st.image(png, width="stretch")

        if results.get("global"):
            st.subheader("🌐 全局文本词云（所有章节合并）")
            st.image(results["global"], width="stretch")
