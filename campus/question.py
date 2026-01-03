import streamlit as st
import random
import re

from aid_integrated.campus import llm_helpers

def extract_topic_from_sentence(sent: str) -> str:
    invalid_starts = {"这些", "这种", "该", "其", "它", "此", "与", "和", "对于", "基于"}

    en_term_pattern = r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*"
    en_terms = re.findall(en_term_pattern, sent)
    for term in en_terms:
        professional_en_terms = {"TF", "IDF", "TF-IDF", "TextRank", "NLP", "LDA", "SVM", "CNN", "RNN"}
        if (len(term) >= 2 and (term.upper() in professional_en_terms or 
            (any(c.isupper() for c in term) and not term.islower()))):
            return term.upper() if term.isupper() else term

    chinese_professional_pattern = r"[\u4e00-\u9fa5]{2,6}[算法|方法|步骤|技术|模型|规则|逻辑|策略|流程|标准]"
    chinese_matches = re.findall(chinese_professional_pattern, sent)
    if chinese_matches:
        for match in chinese_matches:
            if not any(match.startswith(ws) for ws in invalid_starts):
                return match

    core_noun_pattern = r"([\u4e00-\u9fa5]{2,6})"
    core_candidates = re.findall(core_noun_pattern, sent)
    invalid_topics = {"核心目的在于", "报告等结构清晰", "这些预处理", "该方法适用于", "核心在于", "相关内容", "重要作用", "应用价值"}
    for candidate in core_candidates:
        if (len(candidate) >= 2 and candidate not in invalid_topics and
            not any(candidate.startswith(ws) for ws in invalid_starts)):
            if not re.search(r"[的|地|得|在|通过|使用|实现|为了]" + candidate, sent):
                return candidate

    return ""

def generate_questions_from_core(core_sentences: list[str], summary: str, question_types: list[str]) -> list[dict]:
    questions = []
    q_id = 1
    global_used_topics = set()  
    used_core_sents = set()     
    MAX_QUESTIONS = 6  

    for core_sent in core_sentences:
        if len(questions) >= MAX_QUESTIONS:
            break
            
        core_sent_stripped = core_sent.strip()
        if not core_sent_stripped or core_sent_stripped in used_core_sents:
            continue
        
        topic = extract_topic_from_sentence(core_sent_stripped)
        if not topic or topic in global_used_topics:
            continue

        global_used_topics.add(topic)
        used_core_sents.add(core_sent_stripped)

        if "概念解释题" in question_types and len(questions) < MAX_QUESTIONS:
            if re.match(r"^[A-Z]+(?:-[A-Z]+)*$", topic):
                question_content = f"{q_id}. 请解释「{topic}」的含义，并说明它在讲义内容中的核心作用。\n\n"
            else:
                question_content = f"{q_id}. 请简要阐述「{topic}」的定义，以及它在相关知识体系中的价值。\n\n"
            
            questions.append({
                "id": q_id,
                "type": "概念解释题",
                "content": question_content,
                "based_on": core_sent_stripped
            })
            q_id += 1

        if len(questions) >= MAX_QUESTIONS:
            break

        if "关键句理解题" in question_types and len(questions) < MAX_QUESTIONS:
            question_content = f"""{q_id}. 句子理解题：

请结合讲义核心内容，分析下列句子的核心含义及其在知识体系中的作用：

> {core_sent_stripped}

\n\n"""
            questions.append({
                "id": q_id,
                "type": "关键句理解题",
                "content": question_content,
                "based_on": core_sent_stripped
            })
            q_id += 1


        if len(questions) >= MAX_QUESTIONS:
            break

        if "简答题（重点信息提炼）" in question_types and len(questions) < MAX_QUESTIONS:
            if re.match(r"^[A-Z]+(?:-[A-Z]+)*$", topic):
                question_content = f"{q_id}. 简答题：\n\n> 请结合讲义内容，提炼「{topic}」的核心应用场景及关键要点。\n\n"
            else:
                question_content = f"{q_id}. 简答题：\n\n> 请提炼与「{topic}」相关的核心信息，包括其实施流程或应用价值。\n\n"
            
            questions.append({
                "id": q_id,
                "type": "简答题（重点信息提炼）",
                "content": question_content,
                "based_on": core_sent_stripped
            })
            q_id += 1

        if len(questions) >= MAX_QUESTIONS:
            break

    return questions

def _allocate_question_counts(question_types: list[str]) -> dict[str, int]:
    types = [t for t in question_types if isinstance(t, str) and t.strip()]
    n_types = len(types)
    if n_types <= 0:
        return {}
    per = 6 if n_types == 1 else (3 if n_types == 2 else 2)
    return {t: per for t in types}

def _generate_questions_with_deepseek(
    summary: str,
    core_sentences: list[str],
    question_types: list[str],
    requirements: str,
) -> list[dict]:
    counts = _allocate_question_counts(question_types)
    out: list[dict] = []
    for qtype in question_types:
        n = counts.get(qtype, 0)
        if n <= 0:
            continue
        items = llm_helpers.generate_review_questions(
            summary=summary,
            core_knowledge=core_sentences,
            question_type=qtype,
            n=n,
            requirements=requirements,
        )
        for it in items:
            out.append({"type": qtype, "question": it.get("question", ""), "answer": it.get("answer", "")})
    return out

def render_questions_box(questions: list[dict], title: str):

    if not questions:
        st.info("暂无有效复习题，请检查核心知识点数据是否完整")
        return

    content = ""
    for q in questions:
        content += f"<div style='margin-bottom: 20px; line-height: 1.6;'>{q['content']}</div>"
        based_on_abbr = q['based_on'][:60] + "..." if len(q['based_on']) > 60 else q['based_on']
        content += f"<div style='font-size: 12px; color: #666; margin-bottom: 15px;'>（出题依据：{based_on_abbr}）</div>"

    html = f"""
    <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
        <h4 style="margin: 0 0 15px 0; color: #2563eb;">📘 {title}（共{len(questions)}题）</h4>
        <div>{content}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_llm_questions_box(questions: list[dict], title: str, show_answers: bool) -> None:
    if not questions:
        st.info("暂无有效复习题，请检查核心知识点数据是否完整")
        return

    order = ["概念解释题", "关键句理解题", "简答题（重点信息提炼）"]
    by_type: dict[str, list[dict]] = {t: [] for t in order}
    other: list[dict] = []
    for q in questions:
        t = str(q.get("type", "")).strip()
        if t in by_type:
            by_type[t].append(q)
        else:
            other.append(q)

    tabs: list[str] = [t for t in order if by_type[t]]
    if other:
        tabs.append("其他")

    st.markdown(f"#### 📘 {title}（共{len(questions)}题）")
    if not tabs:
        return

    def _render_items(items: list[dict]) -> None:
        for i, item in enumerate(items, 1):
            q_text = str(item.get("question", "")).strip()
            a_text = str(item.get("answer", "")).strip()
            if q_text:
                st.markdown(f"**{i}. {q_text}**")
            if a_text:
                with st.expander("查看答案", expanded=show_answers):
                    st.markdown(a_text)
            st.divider()

    if len(tabs) == 1:
        t = tabs[0]
        items = other if t == "其他" else by_type.get(t, [])
        _render_items(items)
        return

    tab_objs = st.tabs(tabs)
    for idx, t in enumerate(tabs):
        with tab_objs[idx]:
            items = other if t == "其他" else by_type.get(t, [])
            _render_items(items)

def render_core_based_question_page():
    st.header("📘 多类型习题生成")

    st.markdown(
        """
        <div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
  <div style="font-size:16px;color:#1e293b;line-height:1.75;">
    本页面基于 <b style="color:#2563eb">TF-IDF 重点段落分析结果</b>，自动生成多种复习题型：<br/>
    ①概念解释题<br/>
    ②关键句理解题<br/>
    ③简答题（重点信息提炼）<br/>
  </div>
  <div style="margin-top:12px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
    🧭 <b>使用方式：</b>请先在「📈 文本重点与结构分析」页面完成 TF-IDF 计算。
  </div>
</div>
        """,
        unsafe_allow_html=True
    )

    has_campus_results = isinstance(st.session_state.get("campus_generated_results"), dict)
    if not has_campus_results:
        st.warning("⚠️ 未检测到核心知识点数据，请先前往「📋 讲义摘要与核心知识点提取」页面生成核心内容！")
        return

    campus_results = st.session_state["campus_generated_results"]
    has_chapter_data = bool(campus_results.get("chapter"))
    has_global_data = bool(campus_results.get("global") and (campus_results["global"]["core"] or campus_results["global"]["summary"]))

    if not has_chapter_data and not has_global_data:
        st.warning("⚠️ 核心知识点数据为空，请先生成有效核心内容！")
        return

    scope_options: list[str] = []
    if has_global_data:
        scope_options.append("全局")
    if has_chapter_data:
        scope_options.append("按章节")
    scope = st.radio("出题范围", scope_options, index=0, horizontal=True, key="question_scope")
    use_chapter_data = scope == "按章节"

    st.markdown("<h5 style='margin: 15px 0 8px 0; color: #1e40af;'>题型选择</h5>", unsafe_allow_html=True)
    selected_question_types = st.multiselect(
        "请选择要生成的题型",
        options=["概念解释题", "关键句理解题", "简答题（重点信息提炼）"],
        default=["概念解释题", "关键句理解题", "简答题（重点信息提炼）"],
        key="selected_q_types"
    )

    if not selected_question_types:
        st.warning("⚠️ 请至少选择一种题型！")
        return

    requirements = st.text_area(
        "出题要求（可选）",
        value=st.session_state.get("question_requirements", ""),
        placeholder="例如：覆盖定义/流程/对比；题干尽量结合课堂例子；答案分点；难度中等。",
        height=100,
        key="question_requirements",
    )

    show_answers = st.checkbox("默认展开显示答案", value=False, key="show_answers")

    if st.button("生成复习题", type="primary", width="stretch"):
        with st.spinner("正在基于核心知识点生成精准复习题..."):
            generated_questions = {}
            try:
                if use_chapter_data:
                    for file_name, data in campus_results["chapter"].items():
                        core_sentences = data.get("core", [])
                        summary = data.get("summary", "")
                        questions = _generate_questions_with_deepseek(
                            summary=summary,
                            core_sentences=core_sentences,
                            question_types=selected_question_types,
                            requirements=requirements,
                        )
                        generated_questions[file_name] = questions
                else:
                    global_data = campus_results["global"]
                    core_sentences = global_data.get("core", [])
                    summary = global_data.get("summary", "")
                    questions = _generate_questions_with_deepseek(
                        summary=summary,
                        core_sentences=core_sentences,
                        question_types=selected_question_types,
                        requirements=requirements,
                    )
                    generated_questions["global"] = questions

                st.session_state["core_based_generated_questions"] = generated_questions
                total = sum(len(v) for v in generated_questions.values())
                st.success(f"✅ 复习题生成完成！共{total}道题！")
            except RuntimeError as e:
                st.error(
                    "❌ DeepSeek 未配置或不可用。请在项目目录的 `.streamlit/secrets.toml` 配置 `DEEPSEEK_API_KEY`，"
                    "或设置环境变量 `DEEPSEEK_API_KEY` 后重试。"
                )
                st.caption(str(e))
                return
            except Exception as e:
                st.error(f"❌ DeepSeek 出题失败：{str(e)}")
                return

    st.divider()
    st.subheader("📝 复习题")

    cached_questions = st.session_state.get("core_based_generated_questions", {})

    if not cached_questions:
        st.markdown(
            """
            <div style="
                margin: 10px 0; 
                border: 1px solid #E5E6EB;
                border-radius: 4px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            ">
                <div style="
                    background-color: #F5F9FF;
                    padding: 12px 16px;
                    border-bottom: 1px solid #E5E6EB;
                    border-radius: 4px 4px 0 0;
                    font-size: 15px;
                    font-weight: 600;
                    color: #165DFF;
                ">
                    <span style="margin-right: 8px;">ℹ️</span> 提示
                </div>
                <div style="
                    background-color: #FFFFFF;
                    padding: 16px;
                    border-radius: 0 0 4px 4px;
                    font-size: 14px;
                    color: #666;
                ">
                    点击「生成复习题」按钮，即可基于核心知识点生成最多6道无重复题目
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    if "global" in cached_questions:
        global_questions = cached_questions.get("global", [])
        render_llm_questions_box(global_questions, title="全局核心知识点复习题", show_answers=show_answers)
    else:
        for idx, (file_name, questions) in enumerate(cached_questions.items(), 1):
            render_llm_questions_box(questions, title=f"章节 {idx}：{file_name} 核心知识点复习题", show_answers=show_answers)
            st.divider()