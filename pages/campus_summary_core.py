from types import ModuleType
from typing import Optional

import streamlit as st

from aid_integrated.campus import llm_helpers, summary_utils


@st.cache_resource(show_spinner=False)
def _load_optional_llm_helpers_cached() -> Optional[ModuleType]:
    return llm_helpers


def render() -> None:
    st.header("📋 讲义摘要与核心知识点提取")

    st.markdown(
        """
        <div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
        box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
        <div style="font-size:16px;color:#1e293b;line-height:1.8;">
            <b style="font-size:18px;color:#1e40af;">这个功能能帮你做什么？</b><br/>
            <span style="color:#2563eb;font-weight:700;">✍️ 智能生成讲义摘要</span>：自动浓缩整份讲义/单章节核心内容<br/>
            <span style="color:#2563eb;font-weight:700;">🔑 提取核心知识点</span>：自动筛选不超过10个核心句子<br/>
            <span style="color:#2563eb;font-weight:700;">📝 智能学习建议</span>：基于内容生成针对性分点建议
        </div>
        <div style="margin-top:16px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
            💡 <b>核心知识点提取规则</b>：过滤无意义句子、自动去重，按语义重要性排序<br/>
            💡 <b>功能使用提示</b>：需先在「数据加载与预处理」上传并清洗文本
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.setdefault(
        "campus_generated_results",
        {
            "chapter": {},
            "global": {"summary": "", "core": [], "suggestions": [], "raw_core": []},
        },
    )

    has_chapter_data = bool(st.session_state.get("chapter_sentences"))
    has_global_data = bool(st.session_state.get("sentences"))

    if not has_chapter_data and not has_global_data:
        st.warning("⚠️ 请先在「📚 数据加载与预处理」上传并清洗文本！")
        return

    # ========== 修复：生成模式（水平排列+互斥单选） ==========
    st.markdown("<h5 style='margin: 15px 0 8px 0; color: #1e40af;'>生成模式</h5>", unsafe_allow_html=True)
    # 用st.radio的水平布局参数（Streamlit 1.28+支持）
    generate_mode = st.radio(
        "",
        ["按章节生成（每个文件独立分析）", "全局生成（所有文件合并）"],
        index=0 if has_chapter_data else 1,
        horizontal=True,  # 关键：水平排列
        label_visibility="collapsed"  # 隐藏默认标题
    )

    # ========== 修复：摘要长度（水平排列+互斥单选） ==========
    st.markdown("<h5 style='margin: 15px 0 8px 0; color: #1e40af;'>摘要长度（字符数）</h5>", unsafe_allow_html=True)
    summary_length = st.radio(
        "",
        [50, 100, 150],
        index=1,
        horizontal=True,  # 关键：水平排列
        label_visibility="collapsed"  # 隐藏默认标题
    )

    # ========== 复选框 ==========
    use_llm_opt = st.checkbox("使用 DeepSeek 优化表达（可选）", value=True)
    helpers = _load_optional_llm_helpers_cached() if use_llm_opt else None

    def _optimize_summary(text: str) -> str:
        fn = getattr(helpers, "optimize_summary", None) if helpers is not None else None
        if callable(fn):
            try:
                return fn(text)
            except Exception:
                return text
        return text

    def _optimize_core(lines: list[str]) -> list[str]:
        fn = getattr(helpers, "optimize_core_sentences_with_deepseek", None) if helpers is not None else None
        if callable(fn):
            try:
                return fn(lines)
            except Exception:
                return lines
        return lines

    def _suggestions(summary: str, core: list[str]) -> list[str]:
        fn = getattr(helpers, "generate_study_suggestions", None) if helpers is not None else None
        if callable(fn):
            try:
                return fn(summary, core)
            except Exception:
                return []
        return []

    def _extract_core(sentences: list[str]) -> list[str]:
        if not sentences:
            return []
        scores = summary_utils.score_sentences(sentences)
        filtered: list[str] = []
        for s in sentences:
            s2 = str(s).strip()
            if not s2:
                continue
            english_chars = sum(1 for c in s2 if ("a" <= c <= "z") or ("A" <= c <= "Z"))
            ratio = english_chars / len(s2) if len(s2) else 0
            if ratio <= 0.3:
                filtered.append(s2)

        if not filtered:
            return []

        ranked = sorted(filtered, key=lambda x: scores[sentences.index(x)], reverse=True)
        import re

        seen = set()
        out: list[str] = []
        for s in ranked:
            norm = re.sub(r"[^\w\s]", "", s).strip().lower()
            if norm and norm not in seen:
                seen.add(norm)
                out.append(s)
            if len(out) >= 10:
                break

        out.sort(key=lambda x: sentences.index(x))
        return out

    def _render_core_box(lines: list[str], title: str) -> None:
        if not lines:
            st.info("暂无有效核心知识点")
            return

        content = ""
        for i, sent in enumerate(lines, 1):
            content += f"<b style='color: #1976d2;'>{i}.</b> {sent}<br><br>"

        html = f"""
        <div style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #f0f8fb 0%, #e8f4f8 100%); border-radius: 10px; border: 1px solid #d1e7dd;">
            <h4 style="margin: 0 0 12px 0; color: #1976d2;">🔑 {title}（共{len(lines)}个）</h4>
            <p style="color: #666; font-size: 13px; margin: 0 0 12px 0;">内容已优化断句和表达，可直接复制使用</p>
            <div style="background-color: white; border-radius: 8px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">{content}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    def _render_suggestions_box(lines: list[str]) -> None:
        if not lines:
            st.info("暂无学习建议")
            return

        content = ""
        for s in lines:
            content += f"- {s}<br><br>"
        html = f"""
        <div style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #fdfbf7 0%, #f8f0e3 100%); border-radius: 10px; border: 1px solid #f5e8d0;">
            <h4 style="margin: 0 0 15px 0; color: #d8703f;">📝 学习建议</h4>
            <div style="background-color: white; border-radius: 8px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">{content}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    if st.button("生成摘要与核心知识点", type="primary", width="stretch"):
        if generate_mode == "按章节生成（每个文件独立分析）" and st.session_state.get("chapter_sentences"):
            st.session_state["campus_generated_results"]["chapter"] = {}
            with st.spinner("正在处理每个章节..."):
                for file_name, sents in st.session_state["chapter_sentences"].items():
                    if not sents:
                        continue

                    summary = summary_utils.generate_summary(sents, summary_length)
                    summary2 = _optimize_summary(summary)

                    raw_core = _extract_core(sents)
                    core2 = _optimize_core(raw_core)
                    sug = _suggestions(summary2, core2)

                    st.session_state["campus_generated_results"]["chapter"][file_name] = {
                        "summary": summary2,
                        "core": core2,
                        "suggestions": sug,
                        "raw_core": raw_core,
                    }

        elif generate_mode == "全局生成（所有文件合并）" and st.session_state.get("sentences"):
            with st.spinner("正在处理全局内容..."):
                sents = st.session_state["sentences"]
                summary = summary_utils.generate_summary(sents, summary_length)
                summary2 = _optimize_summary(summary)

                raw_core = _extract_core(sents)
                core2 = _optimize_core(raw_core)
                sug = _suggestions(summary2, core2)

                st.session_state["campus_generated_results"]["global"] = {
                    "summary": summary2,
                    "core": core2,
                    "suggestions": sug,
                    "raw_core": raw_core,
                }

        else:
            st.warning("⚠️ 所选模式无对应数据，请检查！")

    results = st.session_state.get("campus_generated_results")
    if not isinstance(results, dict):
        return

    st.divider()
    st.subheader("📌 生成结果")

    if generate_mode == "按章节生成（每个文件独立分析）" and results.get("chapter"):
        for idx, (file_name, data) in enumerate(results["chapter"].items(), 1):
            st.subheader(f"📖 章节 {idx}：{file_name}")
            st.markdown("**📋 章节核心摘要（优化后）**")
            st.info(data.get("summary", ""))
            _render_core_box(data.get("core", []), title="优化后核心知识点")

            with st.expander(f"📜 查看 {file_name} 原始核心知识点", expanded=False):
                raw = data.get("raw_core", [])
                if raw:
                    for i, line in enumerate(raw, 1):
                        st.write(f"{i}. {line}")
                else:
                    st.info("暂无原始核心知识点")

            _render_suggestions_box(data.get("suggestions", []))
            st.divider()

    if generate_mode == "全局生成（所有文件合并）" and results.get("global"):
        data = results["global"]
        if data.get("summary") or data.get("core") or data.get("suggestions"):
            st.subheader("📚 全局讲义")
            st.markdown("**📋 全局核心摘要（优化后）**")
            st.info(data.get("summary", ""))
            _render_core_box(data.get("core", []), title="优化后全局核心知识点")

            with st.expander("📜 查看全局原始核心知识点", expanded=False):
                raw = data.get("raw_core", [])
                if raw:
                    for i, line in enumerate(raw, 1):
                        st.write(f"{i}. {line}")
                else:
                    st.info("暂无原始核心知识点")

            _render_suggestions_box(data.get("suggestions", []))
        else:
            st.info("点击「生成摘要与核心知识点」按钮开始处理")