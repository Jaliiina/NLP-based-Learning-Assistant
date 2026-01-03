import os
import json
from typing import List

import requests
import streamlit as st


DEEPSEEK_API_BASE = "https://api.deepseek.com/v1/chat/completions"


def _secret_get(key: str, default: str = "") -> str:
    try:
        v = st.secrets.get(key, default)
    except Exception:
        v = default
    if v is None:
        return default
    return str(v).strip()


def _api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    return _secret_get("DEEPSEEK_API_KEY", "")


def _api_base() -> str:
    base = os.getenv("DEEPSEEK_BASE_URL", "").strip()
    if base:
        return base
    base = _secret_get("DEEPSEEK_BASE_URL", "")
    return base or DEEPSEEK_API_BASE


def _model() -> str:
    model = os.getenv("DEEPSEEK_MODEL", "").strip()
    if model:
        return model
    model = _secret_get("DEEPSEEK_MODEL", "")
    return model or "deepseek-chat"


def optimize_core_sentences_with_deepseek(raw_sentences: List[str]) -> List[str]:
    if not raw_sentences:
        return []

    key = _api_key()
    if not key:
        return raw_sentences

    prompt = "\n".join([f"{i+1}. {s}" for i, s in enumerate(raw_sentences)])
    content = f"""
请将以下核心知识点句子优化为更通顺、更专业的表达，要求：
1. 保持原意不变；
2. 每条仍为一句话；
3. 仍输出为编号列表（1. 2. 3. ...）。

原句：
{prompt}
"""

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    data = {
        "model": _model(),
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 500,
    }

    try:
        response = requests.post(_api_base(), headers=headers, json=data, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()
        optimized_text = result["choices"][0]["message"]["content"].strip()
        lines = [l.strip() for l in optimized_text.split("\n") if l.strip()]
        out: List[str] = []
        for line in lines:
            if line[0].isdigit():
                out.append(line.split(".", 1)[-1].strip())
        return out or raw_sentences
    except Exception as e:
        st.warning(f"核心知识点优化失败：{str(e)}")
        return raw_sentences


def optimize_summary(summary_text: str) -> str:
    if not summary_text.strip():
        return "无有效摘要内容"

    key = _api_key()
    if not key:
        return summary_text

    prompt = f"""
请对以下课程摘要进行语言优化，要求：
1. 保持原意不变；
2. 更加通顺、逻辑更清晰；
3. 输出为一段文字，不要分点。

摘要：{summary_text}
"""

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    data = {
        "model": _model(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 200,
    }

    try:
        response = requests.post(_api_base(), headers=headers, json=data, timeout=30, verify=False)
        response.raise_for_status()
        optimized_summary = response.json()["choices"][0]["message"]["content"].strip()
        if optimized_summary and not optimized_summary.endswith(("。", "！", "？", "；")):
            optimized_summary += "。"
        return optimized_summary
    except Exception as e:
        st.warning(f"摘要优化失败：{str(e)}")
        return summary_text


def generate_study_suggestions(summary: str, core_knowledge: List[str]) -> List[str]:
    if not summary or not core_knowledge:
        return ["暂无有效内容生成学习建议"]

    key = _api_key()
    if not key:
        return [
            "1. 先用自己的话复述摘要中的核心结论",
            "2. 围绕核心知识点逐条整理笔记与例题",
            "3. 将关键词与概念画成思维导图进行关联",
        ]

    prompt = f"""
请基于以下课程内容，生成3-5条简洁的学习建议，要求：
1. 每条建议单独一行，用数字序号开头；
2. 结合核心知识点，针对性强；
3. 语言简洁（每条约20字）；
4. 覆盖“理解概念”“重点练习”“关联拓展”等维度。

课程摘要：{summary}
核心知识点：{chr(10).join([f"{i+1}. {sent}" for i, sent in enumerate(core_knowledge)])}
"""

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    data = {
        "model": _model(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 300,
    }

    try:
        response = requests.post(_api_base(), headers=headers, json=data, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()
        suggestions = result["choices"][0]["message"]["content"].strip()
        suggestions_list = [s.strip() for s in suggestions.split(chr(10)) if s.strip() and s.strip()[0].isdigit()]
        return suggestions_list
    except Exception as e:
        st.warning(f"学习建议生成失败：{str(e)}")
        return [
            "1. 优先掌握摘要中的核心内容",
            "2. 逐一梳理核心知识点的逻辑",
            "3. 尝试用自己的话复述关键概念",
        ]


def generate_review_questions(
    summary: str,
    core_knowledge: List[str],
    question_type: str,
    n: int,
    requirements: str = "",
) -> List[dict]:
    if n <= 0:
        return []

    key = _api_key()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not configured")

    core_text = chr(10).join([f"{i+1}. {s}" for i, s in enumerate(core_knowledge or [])])

    type_guidance = {
        "概念解释题": "题目聚焦概念/术语：给出定义、关键要点、作用/意义，答案需包含要点列表。",
        "关键句理解题": "题目给出或引用核心句，要求解释句子含义、隐含假设、在整体知识体系中的作用，答案需逐步说明。",
        "简答题（重点信息提炼）": "题目要求提炼流程/方法/要点/对比/应用场景，答案需条理化（分点）。",
    }
    guidance = type_guidance.get(question_type, "题目需紧扣讲义内容，答案清晰可核对。")

    req_text = requirements.strip() if isinstance(requirements, str) else ""

    prompt = f"""
你是一位严谨的课程助教。请严格基于给定的课程摘要与核心知识点生成复习题。

【课程摘要】
{summary.strip() if isinstance(summary, str) else ""}

【核心知识点】
{core_text}

【题型】{question_type}
【题型要求】{guidance}

【额外出题要求】
{req_text if req_text else "无"}

【生成要求】
1. 生成 {n} 道题。
2. 每道题都必须给出标准答案，答案要可直接用于自测。
3. 不要输出与课程无关的泛泛题。
4. 输出必须是 JSON 数组，且只能输出 JSON，不要输出任何额外文本。

JSON 格式示例：
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]
"""

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    data = {
        "model": _model(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1200,
    }

    response = requests.post(_api_base(), headers=headers, json=data, timeout=60, verify=False)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    try:
        parsed = json.loads(content)
    except Exception:
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(content[start : end + 1])
        else:
            raise

    if not isinstance(parsed, list):
        raise ValueError("DeepSeek returned non-list JSON")

    out: List[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        q = str(item.get("question", "")).strip()
        a = str(item.get("answer", "")).strip()
        if q:
            out.append({"question": q, "answer": a})
    return out


def chat_completion(messages: List[dict], temperature: float = 0.5, max_tokens: int = 800) -> str:
    key = _api_key()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not configured")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    data = {
        "model": _model(),
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }

    response = requests.post(_api_base(), headers=headers, json=data, timeout=60, verify=False)
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()
    return content
