"""摘要与章节梳理工具"""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .text_cleaner import load_custom_stopwords, tokenize_mixed, process_text_cleaning


def get_content_keywords(sentences):
    """动态挖掘文本核心关键词（纯通用，不绑定主题）"""
    common_stopwords = set(load_custom_stopwords()) | {"的", "了", "是", "在", "有", "和", "就", "也", "都", "要", "能", "会"}
    full_text = "".join(sentences)
    full_text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", full_text)
    words = tokenize_mixed(full_text)
    words = [w for w in words if w not in common_stopwords and len(w) >= 2]
    if not words:
        return []
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([" ".join(words)])
        word_scores = dict(zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0]))
        return sorted(word_scores.keys(), key=lambda x: word_scores[x], reverse=True)[:15]
    except Exception:
        return list(set(words))[:15]



def score_sentences(sentences):
    """改进版句子评分，自动过滤英文句子"""
    content_words = get_content_keywords(sentences)
    scores = []

    for sent in sentences:
        english_chars = sum(1 for c in sent if "a" <= c <= "z" or "A" <= c <= "Z")
        total_chars = len(sent.strip())
        english_ratio = english_chars / total_chars if total_chars > 0 else 0

        english_penalty = 1.0
        if english_ratio > 0.4:
            english_penalty = 0.3
        elif english_ratio > 0.2:
            english_penalty = 0.7
        elif english_ratio > 0.1:
            english_penalty = 0.9

        sent_words = tokenize_mixed(sent)

        core_count = sum(1 for w in sent_words if w in content_words)
        core_score = core_count / max(len(sent_words), 1)

        sent_len = len(sent)
        if 10 <= sent_len <= 200:
            len_score = 1
        else:
            len_score = 0.3

        struct_words = {
            "定义",
            "包括",
            "分为",
            "作用",
            "原理",
            "特点",
            "含义",
            "本质",
            "步骤",
            "结论",
            "关键",
            "核心",
            "主要",
            "重要",
            "总结",
            "概述",
        }
        struct_score = 0.2 if any(w in sent for w in struct_words) else 0

        has_complete_punctuation = sent.endswith(("。", "！", "？", "；"))
        completeness_score = 0.1 if has_complete_punctuation else 0

        total_score = ((core_score * 0.6) + (len_score * 0.2) + struct_score + completeness_score) * english_penalty

        example_words = {"例如", "比如", "举例", "比如", "如"}
        if any(w in sent for w in example_words):
            total_score *= 0.7

        scores.append(total_score)

    return scores



def extract_chapter_full_sentences(text):
    """章节结构自动梳理（无空格+完整句子）"""
    clean_text, all_sentences = process_text_cleaning(text, for_wordcloud=False)
    if not all_sentences:
        return "未检测到有效句子内容"

    chapter_marks = {"第一章", "第二章", "第三章", "第一节", "第二节", "第三节", "第四节", "第一部分", "第二部分", "第三部分"}

    chapter_content = {}
    current_chapter = None

    for sentence in all_sentences:
        for mark in chapter_marks:
            if mark in sentence:
                current_chapter = mark
                if current_chapter not in chapter_content:
                    chapter_content[current_chapter] = []
                break
        if current_chapter is not None:
            chapter_content[current_chapter].append(sentence)

    chapter_content = {k: v for k, v in chapter_content.items() if len(v) >= 1}
    if not chapter_content:
        return "未检测到章节结构标志"

    def chapter_sort_key(chapter):
        num_match = re.search(r"(\d+)", chapter)
        if num_match:
            return int(num_match.group())
        chinese_num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
        for cn, num in chinese_num.items():
            if cn in chapter:
                return num
        return 0

    sorted_chapters = sorted(chapter_content.keys(), key=chapter_sort_key)

    result = "【章节结构与完整内容梳理】\n"
    for chapter in sorted_chapters:
        result += f"\n{chapter}：\n"
        full_content = "".join(chapter_content[chapter])
        result += full_content[:500] + ("..." if len(full_content) > 500 else "") + "\n"

    return result



def generate_summary(sentences, summary_length=100, tolerance=30):
    """通用课程摘要生成"""
    if not sentences:
        return "无法生成有效摘要，请检查文本内容。"

    sentence_scores = score_sentences(sentences)
    scored_sents = list(zip(sentences, sentence_scores))
    top_sents = sorted(scored_sents, key=lambda x: x[1], reverse=True)[:8]
    top_sents = sorted(top_sents, key=lambda x: sentences.index(x[0]))

    summary = ""
    current_length = 0
    connect_words = ["本课程核心内容为：", "主要涵盖", "重点讲解", "核心知识点包括", "同时涉及"]
    conn_idx = 0

    incomplete_patterns = re.compile(r"^[也叫|包括|例如|比如|是|为|涵盖|讲解|涉及]")
    example_patterns = re.compile(r"例如|比如|如")
    category_patterns = re.compile(r"([、，；]){3,}")
    meta_words = {"课程", "教材", "团队", "教师", "开设", "历史", "荣誉", "大学"}

    for sent, _ in top_sents:
        sent_clean = sent.strip()

        if incomplete_patterns.match(sent_clean):
            continue

        if category_patterns.search(sent_clean):
            split_cats = re.split(r"[、，；]", sent_clean)
            split_cats = [cat.strip() for cat in split_cats if cat.strip()]
            if len(split_cats) > 4:
                sent_clean = "、".join(split_cats[:4]) + "等"

        if example_patterns.search(sent_clean) and not sent_clean.endswith(("等", "。", "；", "）")):
            sent_clean += "等"

        for mw in meta_words:
            sent_clean = sent_clean.replace(mw, "")
        sent_clean = re.sub(r"\s+", "", sent_clean).rstrip("。，；")

        if not sent_clean or len(sent_clean) < 5:
            continue

        if conn_idx == 0:
            conn = connect_words[0]
        else:
            prev_end = summary[-1] if summary else ""
            if prev_end in ("类", "型", "分"):
                conn = "其中"
            elif prev_end in ("例", "等"):
                conn = "而"
            else:
                conn = connect_words[conn_idx % len(connect_words)]
        conn_idx += 1

        total_len = len(conn) + len(sent_clean) + 1
        if current_length + total_len <= summary_length + tolerance:
            summary += conn + sent_clean + "；"
            current_length += total_len
        else:
            break

    end_puncts = ["。", "；", "！", "？", "，", "、"]
    candidates = []
    start = max(0, summary_length - tolerance)
    end = min(len(summary), summary_length + tolerance)

    for i in range(start, end):
        if summary[i] in end_puncts:
            priority = end_puncts.index(summary[i])
            candidates.append((i, priority))

    if candidates:
        candidates.sort(key=lambda x: (x[1], abs(x[0] - summary_length)))
        cut_pos = candidates[0][0] + 1
        summary = summary[:cut_pos]
    else:
        cut_pos = min(summary_length + tolerance, len(summary))
        while cut_pos < len(summary) and "\u4e00" <= summary[cut_pos] <= "\u9fff":
            cut_pos += 1
        summary = summary[:cut_pos]

    summary = summary.strip().rstrip("；，、")
    summary = re.sub(r"；+", "；", summary)
    summary = re.sub(r"等；", "等。", summary)
    summary = re.sub(r"([。；])+", r"\1", summary)

    if not summary.endswith(("。", "！", "？", "；")):
        summary += "…" if len(summary) >= summary_length else "。"

    return summary
