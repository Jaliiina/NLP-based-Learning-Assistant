"""文本清洗工具：过滤乱码、去停用词、句子切分等（保留词云所需的分词逻辑）"""
import re
import string
import jieba
from pathlib import Path



def filter_garbage_lines(text):
    """过滤包含大量乱码的行"""
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        valid_count = 0
        total_count = len(line.strip())
        if total_count == 0:
            continue
        for char in line:
            o = ord(char)
            if (0x4E00 <= o <= 0x9FFF) or (ord("a") <= o <= ord("z") or ord("A") <= o <= ord("Z")) or (
                ord("0") <= o <= ord("9")
            ):
                valid_count += 1
        if valid_count / total_count >= 0.5:
            clean_lines.append(line)
    return "\n".join(clean_lines)



def filter_garbage_segments(line):
    """过滤行内的乱码片段"""
    segments = re.split(r"([^\u4e00-\u9fa5a-zA-Z0-9\s。！？；,.])", line)
    clean_segments = []
    for seg in segments:
        valid_count = 0
        total_count = len(seg.strip())
        if total_count == 0:
            continue
        for char in seg:
            o = ord(char)
            if (0x4E00 <= o <= 0x9FFF) or (ord("a") <= o <= ord("z") or ord("A") <= o <= ord("Z")) or (
                ord("0") <= o <= ord("9")
            ):
                valid_count += 1
        if valid_count / total_count >= 0.3:
            clean_segments.append(seg)
    return "".join(clean_segments)



def remove_garbage_chars(text):
    """严格过滤乱码，保留核心字符"""
    text = re.sub(r"[\u25A0-\u25FF\u2610-\u2612]", "", text)
    text = re.sub(r"[⯁-⯿]", "", text)

    chinese_range = range(0x4E00, 0x9FFF + 1)
    english_lower = set(range(ord("a"), ord("z") + 1))
    english_upper = set(range(ord("A"), ord("Z") + 1))
    english_range = english_lower | english_upper
    number_range = set(range(ord("0"), ord("9") + 1))
    core_punct = {" ", "。", "！", "？", "；", ",", "."}

    char_flags = []
    for char in text:
        o = ord(char)
        is_valid = o in chinese_range or o in english_range or o in number_range or char in core_punct
        char_flags.append(is_valid)

    clean_chars = []
    valid_segment = []
    for char, is_valid in zip(text, char_flags):
        if is_valid:
            valid_segment.append(char)
        else:
            if len(valid_segment) >= 2:
                clean_chars.extend(valid_segment)
            valid_segment = []
    if len(valid_segment) >= 2:
        clean_chars.extend(valid_segment)

    clean_text = "".join(clean_chars)
    return clean_text



def load_custom_stopwords():
    """加载停用词集合（中文+自定义英文停用词）"""
    stop_words = set()
    cn_stopwords_path = Path(__file__).parent / "campus\stopwords.txt"
    if cn_stopwords_path.exists():
        with open(cn_stopwords_path, "r", encoding="utf-8") as f:
            cn_stop = set([line.strip() for line in f.readlines() if line.strip()])
            stop_words.update(cn_stop)

    en_stopwords_path = Path(__file__).parent / "en_stopwords.txt"
    if en_stopwords_path.exists():
        with open(en_stopwords_path, "r", encoding="utf-8") as f:
            en_stop = set([line.strip().lower() for line in f.readlines() if line.strip()])
            stop_words.update(en_stop)

    domain_generic_words = {
        "方法",
        "对象",
        "线程",
        "接口",
        "子类",
        "父类",
        "执行",
        "类型",
        "数组",
        "文件",
        "变量",
        "函数",
        "程序",
        "系统",
        "模块",
        "数据",
        "结构",
        "流程",
        "步骤",
        "实现",
        "设计",
        "分析",
        "测试",
        "部署",
        "维护",
        "优化",
        "性能",
        "安全",
        "用户",
        "需求",
    }
    stop_words.update(domain_generic_words)
    return stop_words



def tokenize_mixed(text):
    """中英文混合分词（jieba处理中文 + 正则处理英文）"""
    if not text or text.strip() == "":
        return []

    tokens = []
    pattern = re.compile(r"([\u4e00-\u9fff]+)|([a-zA-Z]+)|(\d+)")
    matches = pattern.findall(text)

    for cn_part, en_part, num_part in matches:
        if cn_part:
            tokens.extend(jieba.lcut(cn_part))
        elif en_part:
            tokens.append(en_part.lower())
        elif num_part:
            tokens.append(num_part)

    return tokens



def process_text_cleaning(
    text,
    lower_case=True,
    remove_formula=True,
    num_process="保留",
    remove_stopwords=True,
    for_wordcloud=False,
):
    """文本清洗主函数（适配词云/章节梳理双场景）"""
    text = filter_garbage_lines(text)
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s。！？；,.%￥]", "", text)
    text = text.replace("　", " ").replace("\n", " ").replace("\r", " ")
    text = remove_garbage_chars(text)

    if lower_case:
        text = text.lower()

    if remove_formula:
        text = re.sub(r"\$.*?\$", "", text)
        text = re.sub(r"\\begin\{.*?\}\\end\{.*?\}", "", text, flags=re.DOTALL)

    if num_process == "去除":
        text = re.sub(r"\d+", "", text)

    if for_wordcloud:
        words = tokenize_mixed(text)
        words = [word.strip() for word in words if word.strip()]
        if remove_stopwords:
            all_stop = load_custom_stopwords()
            all_stop |= set(string.punctuation)
            words = [word for word in words if word not in all_stop and len(word) > 1]
        return " ".join(words)
    else:
        text = re.sub(r"\s+", "", text)
        sentences = re.split(r"[。！？；,.]", text)
        sentences = [s.strip() + "。" for s in sentences if len(s.strip()) >= 5]
        return text, sentences
