import os
import tempfile

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import matplotlib
import matplotlib.pyplot as plt
import re

from matplotlib import font_manager

# ===== 强制使用指定字体文件（不改任何业务功能）=====
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

if os.path.exists(FONT_PATH):
    try:
        # 注册字体到 matplotlib
        font_manager.fontManager.addfont(FONT_PATH)

        # 获取字体名，并设为全局默认字体
        _font_name = font_manager.FontProperties(fname=FONT_PATH).get_name()
        matplotlib.rcParams["font.family"] = _font_name

        # 负号正常显示
        matplotlib.rcParams["axes.unicode_minus"] = False
    except Exception:
        # 兜底：即使注册失败，也别让程序崩
        matplotlib.rcParams["axes.unicode_minus"] = False
else:
    # 字体文件不存在就别硬设，避免运行时报错
    matplotlib.rcParams["axes.unicode_minus"] = False

try:
    import jieba  

    JIEBA_AVAILABLE = True
except Exception:
    jieba = None
    JIEBA_AVAILABLE = False

try:
    from gensim.models import KeyedVectors, Word2Vec  

    GENSIM_AVAILABLE = True
except Exception:
    KeyedVectors = None
    Word2Vec = None
    GENSIM_AVAILABLE = False


def load_stopwords():
    stopwords_path = os.path.join(os.path.dirname(__file__), "stopwords.txt")
    stopwords = set()
    if os.path.exists(stopwords_path):
        try:
            with open(stopwords_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:
                        stopwords.add(word)
        except Exception:
            pass
    return stopwords


def split_paragraphs(text: str):
    if not text:
        return []
    raw_paras = text.replace("\r\n", "\n").split("\n\n")
    paras = [p.strip() for p in raw_paras if p.strip()]
    return paras


def tokenize_for_tfidf(paragraphs, use_jieba: bool, stopwords):
    processed = []
    for p in paragraphs:
        if use_jieba and JIEBA_AVAILABLE and jieba is not None:
            tokens = jieba.lcut(p)
        else:
            tokens = p.split()
        tokens = [t for t in tokens if t not in stopwords]
        processed.append(" ".join(tokens))
    return processed


def tokenize_sentences_for_w2v(text: str, use_jieba: bool, stopwords):
    sentences = []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        if use_jieba and JIEBA_AVAILABLE and jieba is not None:
            tokens = jieba.lcut(line)
        else:
            tokens = line.split()
        tokens = [t for t in tokens if t not in stopwords]
        if tokens:
            sentences.append(tokens)
    return sentences


def tfidf_page():
    st.header("📈 段落关键词分析")

    st.markdown(
        """
<div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
  <div style="font-size:16px;color:#1e293b;line-height:1.75;">
    这个页面用来做两件事：<br/>
    <span style="color:#2563eb;font-weight:700;">① 给每个段落提取关键词</span>（看完就知道这一段在讲什么）<br/>
    <span style="color:#2563eb;font-weight:700;">② 找出最“信息密度高”的重点段落</span>（优先复习/做笔记）
  </div>
  <div style="margin-top:16px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
    🧭 <b>你会做什么：</b>粘贴讲义（空行分段）→ 选择一个段落 → 看关键词条形图 → 看重点段落排行<br/>
    <span style="opacity:0.9;">（内部用的是 TF-IDF 权重：用来衡量“这个词对当前段落有多重要”。）</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if "shared_text" not in st.session_state:
        st.session_state["shared_text"] = ""

    raw_text = st.text_area(
        "📄 输入讲义文本（建议用空行分段）",
        height=260,
        key="shared_text",
        help=(
            "提示：用空行（\n\n）分隔段落效果最好。你在这里的编辑只影响本页计算，不会影响其他页面。"
        ),
    )

    st.subheader("⚙️ 可选设置")
    col1, col2, col3 = st.columns(3)

    with col1:
        ngram_max = st.slider(
            "最大 n-gram 长度",
            min_value=1,
            max_value=3,
            value=1,
            step=1,
            help="n-gram=2/3 会把相邻词拼成短语特征（更像“关键短语”）。",
        )
    with col2:
        max_features = st.slider(
            "特征数量上限 max_features",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
            help="特征越多越细致，但计算也更慢；1000 通常够用。",
        )
    with col3:
        use_jieba = st.checkbox("中文分词（jieba）", value=False, help="中文建议开启；英文或已分词文本可关闭。")

    paragraphs = split_paragraphs(raw_text)
    if not paragraphs:
        st.info("请在上方输入至少一个段落（建议用空行分隔段落）。")
        return

    stopwords = load_stopwords()
    processed_paragraphs = tokenize_for_tfidf(paragraphs, use_jieba, stopwords)

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, ngram_max),
            max_features=max_features,
        )
        tfidf_matrix = vectorizer.fit_transform(processed_paragraphs)
        feature_names = vectorizer.get_feature_names_out()
        st.session_state["tfidf_paragraphs"] = paragraphs
        st.session_state["tfidf_matrix"] = tfidf_matrix
        st.session_state["tfidf_features"] = feature_names
        st.session_state["tfidf_scores"] = tfidf_matrix.sum(axis=1).A1
    except Exception as e:
        st.error(f"TF-IDF 计算出错：{e}")
        return

    st.subheader("📦 段落切分结果")
    st.write(f"已识别 **{len(paragraphs)}** 个段落（按空行切分）。")
    st.caption(f"当前特征数：{len(feature_names)}（用于计算关键词；无需刻意追求越大越好）")

    st.markdown("### 🔎 1) 选中一个段落 → 自动提取关键词")
    st.caption("你会得到：关键词表格 + 彩色条形图（越长越重要）。")

    para_index = st.selectbox(
        "选择一个段落：",
        options=list(range(len(paragraphs))),
        format_func=lambda i: f"第 {i + 1} 段：" + (paragraphs[i][:40] + ("..." if len(paragraphs[i]) > 40 else "")),
    )

    top_k = st.slider("显示权重最高的前 K 个词/短语", min_value=5, max_value=30, value=10, step=1)

    row = tfidf_matrix[para_index].toarray().flatten()
    if row.sum() == 0:
        st.info("所选段落的 TF-IDF 权重全为 0，可能是因为分词或停用词过滤导致。")
    else:
        top_indices = row.argsort()[::-1][:top_k]
        data = [(feature_names[i], float(row[i])) for i in top_indices if row[i] > 0]
        if not data:
            st.info("未找到权重大于 0 的特征词。")
        else:
            df_top = pd.DataFrame(data, columns=["词/短语", "TF-IDF 权重"])
            st.table(df_top)

            fig, ax = plt.subplots(figsize=(9.5, 4.8))
            labels = list(reversed(df_top["词/短语"].tolist()))
            values = list(reversed(df_top["TF-IDF 权重"].tolist()))
            colors = plt.cm.viridis(np.linspace(0.2, 0.95, len(values)))
            ax.barh(labels, values, color=colors, edgecolor="none")
            ax.set_title("段落关键词条形图（TF-IDF）", pad=10)
            ax.set_xlabel("TF-IDF 权重")
            ax.grid(axis="x", linestyle="--", alpha=0.25)
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)

    st.markdown("---")
    st.markdown("### 🏆 2) 找重点段落（优先复习/做笔记）")
    st.caption("段落总分越高，通常代表：信息更密、术语更集中。可以把它们当作“重点段”。")

    doc_scores = tfidf_matrix.sum(axis=1).A1

    if len(paragraphs) == 1:
        st.info("当前只有 1 个段落，无法进行段落间对比。")
    else:
        max_top_n = min(10, len(paragraphs))
        top_n = st.slider(
            "显示前 N 个重难点段落",
            min_value=1,
            max_value=max_top_n,
            value=min(3, max_top_n),
            step=1,
        )

        top_idx = doc_scores.argsort()[::-1][:top_n]
        df_rank = pd.DataFrame(
            [(int(i) + 1, float(doc_scores[i]), paragraphs[i][:80]) for i in top_idx],
            columns=["段落编号", "TF-IDF 总分", "段落预览"],
        )
        st.table(df_rank)

        fig2, ax2 = plt.subplots(figsize=(9.5, 4.2))
        y = [str(int(i) + 1) for i in top_idx[::-1]]
        x = [float(doc_scores[i]) for i in top_idx[::-1]]
        colors2 = plt.cm.plasma(np.linspace(0.15, 0.9, len(x)))
        ax2.barh(y, x, color=colors2, edgecolor="none")
        ax2.set_title("重点段落排行（按 TF-IDF 总分）", pad=10)
        ax2.set_xlabel("段落 TF-IDF 总分")
        ax2.set_ylabel("段落编号")
        ax2.grid(axis="x", linestyle="--", alpha=0.25)
        for spine in ["top", "right"]:
            ax2.spines[spine].set_visible(False)
        fig2.tight_layout()
        st.pyplot(fig2)

    st.markdown("---")
    st.info("✅ 已完成：关键词提取 + 重点段落排序。你可以回到上方换段落，或调整参数重新观察变化。")


def load_pretrained_w2v(uploaded_file):
    if not GENSIM_AVAILABLE or KeyedVectors is None:
        return None

    suffix = os.path.splitext(uploaded_file.name)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        if suffix == ".model" and Word2Vec is not None:
            model = Word2Vec.load(tmp_path)
        else:
            model = KeyedVectors.load_word2vec_format(tmp_path, binary=True)
        return model
    except Exception as e:
        st.error(f"加载预训练模型失败：{e}")
        return None
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def train_w2v_from_text(text: str, use_jieba: bool, vector_size: int, window: int, min_count: int, epochs: int):
    if not GENSIM_AVAILABLE or Word2Vec is None:
        return None

    stopwords = load_stopwords()
    sentences = tokenize_sentences_for_w2v(text, use_jieba, stopwords)

    if not sentences:
        st.warning("语料为空，无法训练模型。")
        return None

    model = Word2Vec(
        sentences=sentences,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=2,
        epochs=epochs,
    )
    return model


def visualize_embeddings(model, method: str, n_words: int):
    words = model.wv.index_to_key[:n_words]
    vectors = np.array([model.wv[w] for w in words])

    if vectors.shape[0] < 3:
        st.warning("词表太小，无法可视化。")
        return

    if method == "PCA":
        reducer = PCA(n_components=2)
        coords = reducer.fit_transform(vectors)
    else:
        perplexity = min(30, max(5, vectors.shape[0] // 3))
        reducer = TSNE(
            n_components=2,
            perplexity=perplexity,
            learning_rate=200.0,
            init="random",
            max_iter=1000,
        )
        coords = reducer.fit_transform(vectors)

    t = np.linspace(0, 1, len(words))
    sizes = 20 + 220 * (1 - t) ** 0.8

    fig, ax = plt.subplots(figsize=(9.5, 6))
    sc = ax.scatter(
        coords[:, 0],
        coords[:, 1],
        c=t,
        cmap="Spectral",
        s=sizes,
        alpha=0.88,
        edgecolors="white",
        linewidths=0.6,
    )

    for i, word in enumerate(words):
        ax.annotate(
            word,
            (coords[i, 0], coords[i, 1]),
            fontsize=8,
            alpha=0.9,
            color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.5),
        )

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"Word2Vec 术语语义空间（{method} 降维；颜色=词频排名）", pad=12)
    ax.grid(True, linestyle="--", alpha=0.18)
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(False)
    cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label("词频排名（归一化）")
    fig.tight_layout()
    st.pyplot(fig)


def word2vec_page():
    st.header("🧠 语义理解与概念关联")

    st.markdown(
        """
<div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
  <div style="font-size:16px;color:#1e293b;line-height:1.75;">
    这个页面用来做三件事：<br/>
    <span style="color:#2563eb;font-weight:700;">① 准备一个词向量模型</span>（加载预训练 or 用你的讲义训练一个）<br/>
    <span style="color:#2563eb;font-weight:700;">② 输入术语，查看“它最像谁”</span>（快速找相关概念）<br/>
    <span style="color:#2563eb;font-weight:700;">③ 画一张术语地图</span>（看看概念是否会自动聚成簇）
  </div>
  <div style="margin-top:16px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
    🧭 <b>你会做什么：</b>加载/训练模型 → 输入词查询相似词 → 一键可视化（PCA/t-SNE）
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not GENSIM_AVAILABLE:
        st.error("当前环境未安装 gensim，无法进行 Word2Vec 实验。")
        return

    st.subheader("🧩 第一步：准备模型")
    st.caption("如果你只是想体验：用一个小语料自训就够了；如果你有现成模型文件，也可以直接加载。")

    mode = st.radio(
        "模型来源",
        ["使用预训练模型", "从文本自训模型"],
        help="预训练模型：适合直接查询；自训模型：适合用你的讲义探索课程术语关系。",
    )
    use_jieba = st.checkbox("中文分词（jieba）", value=False, help="中文训练/查询建议开启。")

    model = st.session_state.get("w2v_model", None)

    if mode == "使用预训练模型":
        st.subheader("📦 加载预训练模型")
        uploaded = st.file_uploader(
            "上传 Word2Vec 预训练模型文件（支持 gensim .model 或 word2vec .bin）",
            type=["bin", "model"],
        )
        if uploaded is not None and st.button("📦 加载模型", type="primary"):
            with st.spinner("正在加载预训练模型..."):
                model = load_pretrained_w2v(uploaded)
                if model is not None:
                    st.session_state["w2v_model"] = model
                    st.success("预训练模型加载成功！")
    else:
        st.subheader("🧪 用课程语料训练一个小模型")

        demo_corpus = (
            "自然语言处理 是 人工智能 的 重要 分支 。\n"
            "词向量 模型 可以 将 单词 映射 到 连续 向量 空间 。\n"
            "学生 可以 通过 交互式 实验 加深 对 NLP 概念 的 理解 。"
        )

        if "w2v_corpus_text" not in st.session_state:
            seed = st.session_state.get("shared_text", "")
            st.session_state["w2v_corpus_text"] = seed if isinstance(seed, str) and seed.strip() else demo_corpus

        raw_text = st.text_area(
            "训练语料（建议：每行一句；若已分词则以空格分隔）",
            height=200,
            key="w2v_corpus_text",
            help="Word2Vec 的训练单元是“句子”。每行一句更稳定；段落也可以，但建议先断句。",
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            vector_size = st.slider("向量维度", 50, 300, 100, step=50)
        with col2:
            window = st.slider("窗口大小 window", 2, 10, 5, step=1)
        with col3:
            min_count = st.slider("最小词频 min_count", 1, 5, 1, step=1)
        with col4:
            epochs = st.slider("训练轮数 epochs", 5, 50, 10, step=5)

        if st.button("🧪 开始训练模型", type="primary"):
            with st.spinner("正在训练 Word2Vec 模型，请稍候..."):
                model = train_w2v_from_text(
                    text=raw_text,
                    use_jieba=use_jieba,
                    vector_size=vector_size,
                    window=window,
                    min_count=min_count,
                    epochs=epochs,
                )
                if model is not None:
                    st.session_state["w2v_model"] = model
                    st.success("模型训练完成！")

    if model is None:
        st.info("请先在上方加载或训练一个 Word2Vec 模型。")
        return

    st.markdown("---")
    st.subheader("🔎 第二步：查相似术语")
    st.caption("输入一个词，模型会返回它最接近的 Top-N 词（可以当作“相关概念推荐”）。")

    query_word = st.text_input("输入一个术语/词汇：", help="会返回最相似的 Top-N 术语及相似度。")
    topn = st.slider("显示前 N 个相似术语", min_value=5, max_value=30, value=10, step=1)

    if query_word:
        try:
            similar = model.wv.most_similar(query_word, topn=topn)
            df_sim = pd.DataFrame(similar, columns=["相似术语", "相似度"])
            st.table(df_sim)
        except KeyError:
            st.warning("该术语不在当前模型的词表中，请尝试其他词或重新训练模型。")
        except Exception as e:
            st.error(f"计算相似术语时出错：{e}")

    st.markdown("---")
    st.subheader("🎨 第三步：画一张术语地图")
    st.caption("每个点是一个词：越近越像。颜色表示词频排名（越常见颜色越靠前）。")

    vocab_size = len(model.wv.index_to_key)
    if vocab_size == 0:
        st.info("当前模型词表为空，无法进行可视化。")
        return

    max_words = min(200, vocab_size)
    n_words = st.slider(
        "选择要可视化的术语数量（按频率排名前 N 个）",
        min_value=10,
        max_value=max_words,
        value=min(50, max_words),
        step=10,
    )

    method = st.radio("降维方法", ["PCA", "t-SNE"], horizontal=True)

    if st.button("🎨 开始可视化", type="primary"):
        with st.spinner("正在计算降维坐标并绘图..."):
            visualize_embeddings(model, method, n_words)
