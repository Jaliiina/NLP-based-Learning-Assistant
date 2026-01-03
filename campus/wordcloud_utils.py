"""词云生成工具：基于TF-IDF/TextRank权重生成词云"""
import warnings
warnings.filterwarnings("ignore", message="The use_column_width parameter has been deprecated")
import numpy as np
import jieba.analyse
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from .text_cleaner import tokenize_mixed, load_custom_stopwords


def filter_duplicate_words(word2weight):
    """过滤包含式重复词"""
    if not word2weight:
        return {}
    sorted_words = sorted(word2weight.items(), key=lambda x: (len(x[0]), x[1]), reverse=True)
    filtered = {}
    reserved_words = set()
    for word, weight in sorted_words:
        if len(word) < 2:
            continue
        is_duplicate = False
        for reserved in reserved_words:
            if word in reserved or reserved in word:
                is_duplicate = True
                break
        if not is_duplicate:
            filtered[word] = weight
            reserved_words.add(word)
    if len(filtered) < 20 and len(word2weight) >= 20:
        top_words = sorted(word2weight.items(), key=lambda x: x[1], reverse=True)[:30]
        top_filtered = {}
        top_reserved = set()
        for word, weight in top_words:
            if len(word) < 2:
                continue
            is_dup = False
            for reserved in top_reserved:
                if word in reserved or reserved in word:
                    is_dup = True
                    break
            if not is_dup:
                top_filtered[word] = weight
                top_reserved.add(word)
                if len(top_filtered) >= 20:
                    break
        filtered = top_filtered
    return filtered



def get_tfidf_weights(text):
    """计算TF-IDF权重"""
    custom_stop = load_custom_stopwords()
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize_mixed,
        stop_words=list(custom_stop),
        ngram_range=(2, 3),
        min_df=2,
        max_df=0.8,
        max_features=500,
    )
    clean_words = [w for w in tokenize_mixed(text) if len(w) >= 2 and w not in custom_stop]
    if len(clean_words) < 5:
        pseudo_docs = [text]
    else:
        pseudo_docs = [" ".join(clean_words[i : i + 8]) for i in range(0, len(clean_words), 8)]
    try:
        tfidf_matrix = vectorizer.fit_transform(pseudo_docs)
        weights = tfidf_matrix.sum(axis=0).A1
        word2weight = dict(zip(vectorizer.get_feature_names_out(), weights))
        word2weight = {k: v for k, v in word2weight.items() if v > 0.001}
        word2weight = filter_duplicate_words(word2weight)
        return word2weight
    except Exception:
        return {}



def get_textrank_weights(text):
    """计算TextRank权重"""
    try:
        textrank_result = jieba.analyse.textrank(
            text,
            topK=200,
            withWeight=True,
            allowPOS=("n", "vn", "adj"),
            withFlag=True,
        )
        custom_stop = load_custom_stopwords()
        word2weight = {}
        for (word, flag), score in textrank_result:
            if 2 <= len(word) <= 4 and word not in custom_stop and score > 0.01:
                word2weight[word] = score
        word2weight = filter_duplicate_words(word2weight)
        return word2weight
    except Exception:
        return {}



def generate_weighted_wordcloud(word2weight, bg_color="#ffffff", max_words=200):
    """基于权重生成词云"""
    if not word2weight:
        return None
    weights = list(word2weight.values())
    max_w = max(weights) if weights else 1
    min_w = min(weights) if weights else 0
    scaled_weights = {}
    for word, w in word2weight.items():
        if max_w == min_w:
            scaled = 500
        else:
            scaled = 100 + 900 * np.sqrt((w - min_w) / (max_w - min_w))
        scaled_weights[word] = scaled
    top_scaled = sorted(scaled_weights.items(), key=lambda x: x[1], reverse=True)[:max_words]
    top_scaled = dict(top_scaled)
    wc = WordCloud(
        background_color=bg_color,
        max_words=len(top_scaled),
        width=800,
        height=600,
        font_path="/home/user/ljl/nlp/aid_integrated/c1218/resources/STKAITI.TTF",
        collocations=False,
        repeat=False,
    )
    wc.generate_from_frequencies(top_scaled)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig
