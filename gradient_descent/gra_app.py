import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

gradient_css = """
div[data-testid="stSlider"] div[data-baseweb="slider"] {
    background: transparent !important;
}
div[data-testid="stSlider"] div[data-baseweb="slider"] *,
div[data-testid="stSlider"] div[data-baseweb="slider"] *::before,
div[data-testid="stSlider"] div[data-baseweb="slider"] *::after {
    background: transparent !important;
    box-shadow: none !important;
}
div[data-testid="stSlider"] div[data-baseweb="slider"] > div {
    background: transparent !important;
    border-radius: 999px;
    height: 2px !important;
    min-height: 2px !important;
    box-shadow: none !important;
}
div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div {
    background: #3b82f6 !important;
    border-radius: 999px;
    height: 2px !important;
    min-height: 2px !important;
    box-shadow: none !important;
}
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {
    background: #ffffff !important;
    border-radius: 999px;
    outline: none !important;
    box-shadow:
        0 1px 4px rgba(2, 6, 23, 0.18),
        inset 0 0 0 2px #3b82f6 !important;
}
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]:hover,
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]:active,
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]:focus,
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]:focus-visible {
    box-shadow:
        0 1px 4px rgba(2, 6, 23, 0.18),
        inset 0 0 0 2px #3b82f6 !important;
}

div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="presentation"] {
    background: transparent !important;
    box-shadow: none !important;
}

div[data-testid="stSlider"] div[data-baseweb="tooltip"],
div[data-testid="stSlider"] div[role="tooltip"] {
    display: none !important;
}

div[data-testid="stSlider"] input {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    background: #ffffff !important;
}
div[data-testid="stSlider"] input:focus {
    outline: none !important;
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.22) !important;
}
"""

def run() -> None:
    
    st.markdown(f"<style>{gradient_css}</style>", unsafe_allow_html=True)

    st.markdown(
        """
<div style="background-color:#f8fafc;padding:20px;border-radius:16px;border:1px solid #e2e8f0;
box-shadow:0 4px 16px rgba(0,0,0,0.06);margin:16px 0 24px 0;">
  <div style="font-size:16px;color:#1e293b;line-height:1.8;">
    <b style="font-size:18px;color:#1e40af;">基于梯度下降的函数优化工具</b><br/>
    <span style="color:#64748b;display:block;margin:8px 0 16px 0;font-size:14px;">
    通过梯度下降算法实现函数最小值求解，直观理解函数优化核心逻辑
    </span>
    <span style="color:#2563eb;font-weight:700;">📊 经典函数案例</span>：内置凸函数、非凸函数、鞍点函数等，展示不同函数优化特性<br/>
    <span style="color:#2563eb;font-weight:700;">✏️ 自定义函数探索</span>：输入任意单/多变量函数，自动计算梯度并完成优化<br/>
    <span style="color:#2563eb;font-weight:700;">🔍 动态过程可视化</span>：实时追踪迭代路径、函数曲线/等高线、收敛趋势<br/>
    <span style="color:#2563eb;font-weight:700;">⚙️ 参数自由调节</span>：调整学习率、迭代次数、初始点，观察参数对收敛的影响
  </div>
  <div style="margin-top:16px;background:#eff6ff;padding:12px;border-radius:10px;color:#1e40af;">
    💡 <b>提示</b>：选择函数类型→调整梯度下降参数→点击「开始优化」，即可完整体验全过程！
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["mathtext.fontset"] = "cm"
    matplotlib.rcParams["mathtext.default"] = "it"

    functions = {
        "单变量凸二次函数": {
            "expr": r"x^2 + 2x + 1",
            "dim": 2,
            "desc": "收敛平稳，步长影响显著",
            "latex_expr": r"x^2 + 2x + 1",
        },
        "单变量非凸函数": {
            "expr": r"x^3 - 3x",
            "dim": 2,
            "desc": "初始点决定收敛到局部/全局最优",
            "latex_expr": r"x^3 - 3x",
        },
        "多变量凸椭圆函数": {
            "expr": r"x^2 + 4y^2",
            "dim": 3,
            "desc": "不同维度梯度幅度不同，步长适配难",
            "latex_expr": r"x^2 + 4y^2",
        },
        "多变量鞍点函数": {
            "expr": r"x^2 - y^2",
            "dim": 3,
            "desc": "鞍点处梯度为0，但不是最优解",
            "latex_expr": r"x^2 - y^2",
        },
        "非光滑绝对值函数": {
            "expr": r"abs(x)",
            "dim": 2,
            "desc": "不可导点无定义，使用数值微分近似",
            "latex_expr": r"|x|",
        },
        "震荡函数": {
            "expr": r"sin(x) + 0.1*x^2",
            "dim": 2,
            "desc": "梯度方向频繁变化，下降路径震荡",
            "latex_expr": r"\sin(x) + 0.1x^2",
        },
    }

    def safe_eval(expr, variables):
        allowed_names = {
            "x": 0,
            "y": 0,
            "np": np,
            "sin": np.sin,
            "cos": np.cos,
            "tan": np.tan,
            "exp": np.exp,
            "log": np.log,
            "abs": np.abs,
            "sqrt": np.sqrt,
            "pow": np.power,
        }
        allowed_names.update(variables)

        try:
            expr_py = expr.replace("，", ",").replace("（", "(").replace("）", ")").strip()
            expr_py = re.sub(r"(\w+)\^(\d+)", r"\1**\2", expr_py)
            expr_py = re.sub(r"(\d+)([xy])", r"\1*\2", expr_py)
            expr_py = re.sub(r"(\))([xy])", r"\1*\2", expr_py)
            expr_py = re.sub(r"([xy])(\()", r"\1*\2", expr_py)
            expr_py = re.sub(r"\s+", "", expr_py)

            result = eval(expr_py, {"__builtins__": None}, allowed_names)
            return float(result)
        except SyntaxError as e:
            st.error(f"表达式语法错误: {str(e)} | 原始表达式: {expr}")
            return np.nan
        except Exception as e:
            st.error(f"表达式计算错误: {str(e)} | 原始表达式: {expr}")
            return np.nan

    def format_latex_expr(expr, is_custom=False):
        if not is_custom and expr in [f["latex_expr"] for f in functions.values()]:
            return expr

        formatted = expr.strip()
        formatted = re.sub(r"([a-zA-Z0-9]+)\^(\d+)", r"\1^{\2}", formatted)

        func_map = {
            "sin": r"\\sin",
            "cos": r"\\cos",
            "tan": r"\\tan",
            "exp": r"\\exp",
            "log": r"\\log",
            "abs": r"\\vert",
        }

        for func, latex_func in func_map.items():
            pattern = re.escape(func) + r"\("
            formatted = re.sub(pattern, latex_func + "(", formatted)

        formatted = formatted.replace("abs", "|").replace("||", "|")
        formatted = formatted.replace("*", "")
        formatted = re.sub(r"([+\-*/()])", r" \1 ", formatted)
        formatted = re.sub(r"\s+", " ", formatted).strip()
        formatted = re.sub(r"(\w+)\^(\w+)", r"\1^{\2}", formatted)
        return formatted

    def numerical_gradient(f, x, y=0, h=1e-5):
        try:
            fx1 = f(x + h, y)
            fx2 = f(x - h, y)
            dx = (fx1 - fx2) / (2 * h)
        except Exception:
            dx = 0.0

        try:
            if np.isnan(y):
                dy = 0.0
            else:
                fy1 = f(x, y + h)
                fy2 = f(x, y - h)
                dy = (fy1 - fy2) / (2 * h)
        except Exception:
            dy = 0.0

        dx = np.clip(dx, -1e3, 1e3)
        dy = np.clip(dy, -1e3, 1e3)

        dx = 0.0 if np.isnan(dx) or np.isinf(dx) else dx
        dy = 0.0 if np.isnan(dy) or np.isinf(dy) else dy

        return np.array([dx, dy])

    st.subheader("🧰 控制面板")

    func_mode_options = ["经典函数案例", "自定义函数"]
    if "gd_func_mode" not in st.session_state:
        st.session_state["gd_func_mode"] = func_mode_options[0]

    func_mode = st.radio(
        "选择功能模式",
        func_mode_options,
        index=func_mode_options.index(st.session_state["gd_func_mode"]),
        key="gd_func_mode",
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown(f"<h4 style='color:#334155;'>当前模式：{func_mode}</h4>", unsafe_allow_html=True)

    if func_mode == "经典函数案例":
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### 📚 案例选择")
            function_names = list(functions.keys())
            if "gd_selected_function" not in st.session_state:
                st.session_state["gd_selected_function"] = function_names[0]

            selected_function = st.selectbox(
                "选择函数案例",
                function_names,
                index=function_names.index(st.session_state["gd_selected_function"]),
                key="gd_selected_function",
                label_visibility="collapsed"
            )
        with col2:
            func_info = functions[selected_function]
            st.markdown("### 📝 函数描述")
            st.markdown(
                f"""
                <div style="background-color:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
                    <p style="color:#475569;margin:0;">{func_info['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        col3, col4 = st.columns([1, 1])
        with col3:
            st.markdown("### 📐 函数公式")
            latex_expr = func_info["latex_expr"]
            st.latex(f"f(x{'，y' if func_info['dim'] == 3 else ''}) = {latex_expr}")
            st.markdown("> 💡 梯度由系统自动计算")
        with col4:
            st.markdown("### 🎯 梯度公式")
            grad_descs = {
                "单变量凸二次函数": r"\nabla f = 2x + 2",
                "单变量非凸函数": r"\nabla f = 3x^2 - 3",
                "多变量凸椭圆函数": r"\nabla f = (2x, 8y)",
                "多变量鞍点函数": r"\nabla f = (2x, -2y)",
                "非光滑绝对值函数": r"\nabla f = 1 (x>0), -1 (x<0)（数值近似）",
                "震荡函数": r"\nabla f = \cos(x) + 0.2x",
            }
            st.latex(grad_descs.get(selected_function, r"\nabla f = \text{数值近似}"))

    else:
        st.markdown("### ✏️ 自定义函数设置")
        custom_dim = st.radio(
            "函数维度",
            ["单变量(x)", "多变量(x,y)"],
            index=0,
            horizontal=True  
        )        
        custom_dim_num = 2 if custom_dim == "单变量(x)" else 3
        

        st.markdown("### 目标函数表达式（如x^2 + y^2）")
        default_expr = r"x^2 + y^2" if custom_dim_num == 3 else r"x^2 - 4x + 4"
        st.markdown("📌 示例：单变量 `x^2 - 4x + 4`、多变量 `x^2 + y^2`")
        st.markdown("📌 注意：指数以x^n形式输入，括号在英文状态下输入")
        custom_func_expr = st.text_input("f(x) 或 f(x,y)", value=default_expr, 
                                        help="支持sin(x)、cos(x)、exp(x)、abs(x)等")
        
        custom_desc = st.text_input("函数描述", value="用户自定义函数", 
                                   help="简要描述该函数的特点")
        
        st.markdown("### 绘图范围设置")
        x_min = st.number_input("x最小值", value=-4.0, step=0.5)
        x_max = st.number_input("x最大值", value=4.0, step=0.5)
        if custom_dim_num == 3:
            y_min = st.number_input("y最小值", value=-4.0, step=0.5)
            y_max = st.number_input("y最大值", value=4.0, step=0.5)
        else:
            y_min, y_max = -4.0, 4.0
        
        func_info = {
            "expr": custom_func_expr,
            "dim": custom_dim_num,
            "desc": custom_desc,
            "x_range": (x_min, x_max),
            "y_range": (y_min, y_max) if custom_dim_num == 3 else None,
            "latex_expr": format_latex_expr(custom_func_expr, is_custom=True)
        }
        selected_function = "自定义函数"

    st.subheader("⚙️ 参数设置")

    st.markdown(
        "<div style='color:#64748b;font-size:14px;margin-bottom:12px;'>调整梯度下降核心参数，观察优化效果变化</div>",
        unsafe_allow_html=True
    )

    if func_info["dim"] == 3:
        col1, col2, col3, col4 = st.columns(4)
    else:
        col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<p style='margin-bottom:6px;color:#334155;'>学习率（步长）</p>", unsafe_allow_html=True)
        lr = st.slider("学习率", 0.001, 1.0, 0.1, 0.001, key="gd_lr", label_visibility="collapsed")
        st.caption("📌 建议0.01~0.1")

    with col2:
        st.markdown("<p style='margin-bottom:6px;color:#334155;'>迭代次数</p>", unsafe_allow_html=True)
        iterations = st.slider("迭代次数", 1, 200, 50, 1, key="gd_iterations", label_visibility="collapsed")
        st.caption("📌 凸函数50~100次足够")

    with col3:
        st.markdown("<p style='margin-bottom:6px;color:#334155;'>初始x坐标</p>", unsafe_allow_html=True)
        x0 = st.slider("初始 x", -4.0, 4.0, 3.0, 0.1, key="gd_x0", label_visibility="collapsed")
        st.caption("📌 函数初始取值点")

    if func_info["dim"] == 3:
        with col4:
            st.markdown("<p style='margin-bottom:6px;color:#334155;'>初始y坐标</p>", unsafe_allow_html=True)
            y0 = st.slider("初始 y", -4.0, 4.0, 3.0, 0.1, key="gd_y0", label_visibility="collapsed")
            st.caption("📌 多变量函数专属")
    else:
        y0 = 0.0

    st.markdown("<br/>", unsafe_allow_html=True)  
    try:
        run_button = st.button("🚀 开始梯度下降", width="stretch")
    except TypeError:
        run_button = st.button("🚀 开始梯度下降")

    def get_target_function(func_name):
        if func_name != "自定义函数":
            info = functions[func_name]
            expr = info["expr"]

            def f(x, y=0):
                variables = {"x": float(x), "y": float(y)}
                return safe_eval(expr, variables)

        else:
            info = func_info
            expr = info["expr"]

            def f(x, y=0):
                variables = {"x": float(x), "y": float(y)}
                return safe_eval(expr, variables)

        return f

    def gradient_descent(f, x0, y0, lr, iterations, dim):
        x, y = float(x0), float(y0)
        points = [(x, y)]

        for _ in range(iterations):
            if dim == 2:
                grad = numerical_gradient(f, x, np.nan)
            else:
                grad = numerical_gradient(f, x, y)

            x = x - lr * grad[0]
            y = y - lr * grad[1]

            x = np.clip(x, -1e4, 1e4)
            y = np.clip(y, -1e4, 1e4)

            points.append((x, y))

        return np.array(points), grad


    if "gd_points" not in st.session_state:
        st.session_state["gd_points"] = np.array([[x0, y0]])
        st.session_state["gd_last_params"] = None
        st.session_state["gd_final_grad"] = np.array([0.0, 0.0])
        st.session_state["gd_f"] = lambda x, y=0: 0.0
        st.session_state["gd_max_step"] = 0  

    
    current_params = (
        selected_function,
        func_mode,
        func_info.get("expr"),
        int(func_info.get("dim", 2)),
        func_info.get("x_range"),
        func_info.get("y_range"),
        float(lr),
        int(iterations),
        float(x0),
        float(y0),
    )


    need_recompute = run_button or (st.session_state.get("gd_last_params") != current_params)
    if need_recompute:
        f = get_target_function(selected_function)
        points, final_grad = gradient_descent(f, x0, y0, lr, iterations, func_info["dim"])
        st.session_state["gd_points"] = points
        st.session_state["gd_last_params"] = current_params
        st.session_state["gd_final_grad"] = final_grad
        st.session_state["gd_f"] = f
        st.session_state["gd_max_step"] = len(points) - 1  

 
    points = st.session_state["gd_points"]
    f = st.session_state.get("gd_f", lambda x, y=0: 0.0)
    final_grad = st.session_state["gd_final_grad"]
    max_step = st.session_state["gd_max_step"]

    st.subheader("📊 下降过程")

    if max_step <= 0:
        frame = 0
        st.info("请先点击「开始梯度下降」生成迭代路径")
    else:
        st.markdown("<p style='margin-bottom:6px;color:#334155;'>拖动滑块查看不同迭代步数的下降状态</p>", unsafe_allow_html=True)
        frame = st.slider(
            "查看迭代步数",
            min_value=0,
            max_value=max_step,
            value=0,
            key="gd_frame_slider",
            label_visibility="collapsed"
        )
        st.caption(f"当前查看：第 {frame} 步 / 共 {max_step} 步")

    if func_info["dim"] == 2:
        fig = plt.figure(figsize=(12, 6))
        gs = fig.add_gridspec(1, 3, width_ratios=[2, 1, 0.1])

        ax1 = fig.add_subplot(gs[0])
        if func_mode == "自定义函数":
            x_min, x_max = func_info["x_range"]
        else:
            x_min, x_max = -4, 4
        x_vals = np.linspace(x_min, x_max, 400)
        y_vals = np.array([f(x) for x in x_vals])
        y_vals = np.nan_to_num(y_vals, nan=0, posinf=1e6, neginf=-1e6)

        ax1.plot(x_vals, y_vals, "b-", linewidth=3, alpha=0.8, label="目标函数")

        if max_step > 0:
            path_x = points[: frame + 1, 0]
            path_y = np.array([f(x) for x in path_x])
            path_y = np.nan_to_num(path_y, nan=0, posinf=1e6, neginf=-1e6)
            ax1.plot(
                path_x,
                path_y,
                "r.-",
                linewidth=2.5,
                markersize=10,
                label="下降路径",
                markerfacecolor="red",
                markeredgecolor="darkred",
            )

            colors = plt.cm.Reds(np.linspace(0.4, 1, len(path_x)))
            for i in range(len(path_x) - 1):
                ax1.plot(
                    [path_x[i], path_x[i + 1]],
                    [path_y[i], path_y[i + 1]],
                    color=colors[i],
                    linewidth=2.5,
                )

        current_x = points[frame, 0] if max_step > 0 else x0
        current_y = f(current_x)
        current_y = np.nan_to_num(current_y, nan=0, posinf=1e6, neginf=-1e6)
        ax1.plot(
            current_x,
            current_y,
            "go",
            markersize=16,
            label="当前点",
            markerfacecolor="gold",
            markeredgecolor="darkgreen",
            markeredgewidth=2,
        )
        
        ax1.fill_between(x_vals, y_vals, min(y_vals), alpha=0.1, color="blue")
        ax1.set_xlabel("x", fontsize=14, fontweight="bold")
        ax1.set_ylabel("f(x)", fontsize=14, fontweight="bold")
        if selected_function == "自定义函数":
            title_expr = func_info["latex_expr"]
        else:
            title_expr = functions[selected_function]["latex_expr"]
        ax1.set_title(f"函数: $f(x) = {title_expr}$", fontsize=16, fontweight="bold", pad=20)
        ax1.legend(loc="upper left", fontsize=12)
        ax1.grid(True, alpha=0.3, linestyle="--")
        ax1.set_facecolor("#f8f9fa")
        if func_mode == "自定义函数":
            ax1.set_xlim(func_info["x_range"])
       
        ax2 = fig.add_subplot(gs[1])
        if max_step > 0:
            func_values = np.array([f(x) for x, _ in points[: frame + 1]])
            func_values = np.nan_to_num(func_values, nan=0, posinf=1e6, neginf=-1e6)
            iterations_range = list(range(len(func_values)))

            ax2.plot(iterations_range, func_values, "m.-", linewidth=2.5, markersize=8, label="函数值")
            ax2.plot(
                len(func_values) - 1,
                func_values[-1],
                "go",
                markersize=12,
                label="当前值",
                markerfacecolor="gold",
                markeredgecolor="darkgreen",
            )

            ax2.set_xlabel("迭代次数", fontsize=12, fontweight="bold")
            ax2.set_ylabel("f(x)", fontsize=12, fontweight="bold")
            ax2.set_title("收敛过程", fontsize=14, fontweight="bold")
            ax2.legend(fontsize=10)
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.set_facecolor("#f8f9fa")
          
            min_val = np.min(func_values) * 0.9 if np.min(func_values) != 0 else -1
            max_val = np.max(func_values) * 1.1 if np.max(func_values) != 0 else 1
            ax2.set_ylim(min_val, max_val)
        
        if max_step > 0:
            ax3 = fig.add_subplot(gs[2])
            cmap = plt.cm.Reds
            norm = plt.Normalize(vmin=0, vmax=max_step)
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, cax=ax3, orientation="vertical", label="迭代步数")
        
        try:
            plt.tight_layout()
        except Exception:
            plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
        st.pyplot(fig)

    else:
        fig = plt.figure(figsize=(18, 7))
        gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.05])

        ax1 = fig.add_subplot(gs[0])

        if func_mode == "自定义函数":
            X = np.linspace(func_info["x_range"][0], func_info["x_range"][1], 100)
            Y = np.linspace(func_info["y_range"][0], func_info["y_range"][1], 100)
        else:
            X = np.linspace(-4, 4, 100)
            Y = np.linspace(-4, 4, 100)
        X_grid, Y_grid = np.meshgrid(X, Y)
       
        Z = np.array([[f(x, y) for x, y in zip(row_x, row_y)] for row_x, row_y in zip(X_grid, Y_grid)])
        Z = np.nan_to_num(Z, nan=0, posinf=1e6, neginf=-1e6)
       
        contour = ax1.contour(X_grid, Y_grid, Z, levels=25, cmap="viridis", linewidths=1.5, alpha=0.8)
        ax1.clabel(contour, inline=True, fontsize=8)
        ax1.contourf(X_grid, Y_grid, Z, levels=25, cmap="viridis", alpha=0.3)
        
        if max_step > 0:
            colors = plt.cm.Reds(np.linspace(0.4, 1, frame + 1))
            for i in range(frame):
                ax1.plot(points[i : i + 2, 0], points[i : i + 2, 1], color=colors[i], linewidth=3, alpha=0.8)
            ax1.plot(points[: frame + 1, 0], points[: frame + 1, 1], "r.-", linewidth=2, markersize=8, label="下降路径")
        
        current_x = points[frame, 0] if max_step > 0 else x0
        current_y = points[frame, 1] if max_step > 0 else y0
        ax1.plot(
            current_x,
            current_y,
            "go",
            markersize=16,
            label="当前点",
            markerfacecolor="gold",
            markeredgecolor="darkgreen",
        )
        ax1.plot(x0, y0, "bs", markersize=10, label="起始点")
        
        ax1.set_xlabel("x", fontsize=14, fontweight="bold")
        ax1.set_ylabel("y", fontsize=14, fontweight="bold")
        if selected_function == "自定义函数":
            title_expr = func_info["latex_expr"]
        else:
            title_expr = functions[selected_function]["latex_expr"]
        ax1.set_title(f"等高线图: $f(x,y) = {title_expr}$", fontsize=16, fontweight="bold", pad=20)
        ax1.legend(loc="upper right", fontsize=11)
        ax1.grid(True, alpha=0.3, linestyle="--")
        ax1.set_aspect("equal")
        ax1.set_facecolor("#f8f9fa")
        if func_mode == "自定义函数":
            ax1.set_xlim(func_info["x_range"])
            ax1.set_ylim(func_info["y_range"])

        ax2 = fig.add_subplot(gs[1], projection="3d")
        surf = ax2.plot_surface(X_grid, Y_grid, Z, cmap="viridis", alpha=0.7, linewidth=0, antialiased=True)
        
        if max_step > 0:
            Z_points = np.array([f(x, y) for x, y in points[: frame + 1]])
            Z_points = np.nan_to_num(Z_points, nan=0, posinf=1e6, neginf=-1e6)

            colors = plt.cm.Reds(np.linspace(0.4, 1, frame + 1))
            for i in range(frame):
                ax2.plot(
                    points[i : i + 2, 0],
                    points[i : i + 2, 1],
                    Z_points[i : i + 2],
                    color=colors[i],
                    linewidth=3,
                    alpha=0.8,
                )
            ax2.plot(
                points[: frame + 1, 0],
                points[: frame + 1, 1],
                Z_points[: frame + 1],
                "r.-",
                linewidth=2,
                markersize=8,
                label="下降路径",
            )

        current_z = f(current_x, current_y)
        current_z = np.nan_to_num(current_z, nan=0, posinf=1e6, neginf=-1e6)
        ax2.plot(
            [current_x],
            [current_y],
            [current_z],
            "go",
            markersize=16,
            label="当前点",
            markerfacecolor="gold",
            markeredgecolor="darkgreen",
        )
        
        ax2.set_xlabel("x", fontsize=12, fontweight="bold")
        ax2.set_ylabel("y", fontsize=12, fontweight="bold")
        ax2.set_zlabel("f(x,y)", fontsize=12, fontweight="bold")
        ax2.set_title("三维曲面图", fontsize=16, fontweight="bold", pad=20)
        ax2.view_init(elev=30, azim=45)
        
        ax3 = fig.add_subplot(gs[2])
        plt.colorbar(surf, cax=ax3, orientation="vertical", label="函数值")
        
        try:
            plt.tight_layout()
        except Exception:
            plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
        st.pyplot(fig)

    st.subheader("📈 下降过程状态")
    st.markdown("<br/>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        current_iter = frame
        total_iter = max_step
        st.markdown(
            f"""
    <div style='background-color: #f0fdf4; padding: 18px; border-radius: 12px; text-align: center; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
        <h3 style='color: #166534; margin: 0; font-size:14px;'>迭代步数</h3>
        <h1 style='color: #16a34a; margin: 10px 0;font-size: 28px;'>{current_iter}/{total_iter}</h1>
    </div>
    """,
            unsafe_allow_html=True,
        )

    with col2:
        current_x_val = current_x
        current_y_val = current_y
        coord_text = f"({current_x_val:.3f}, {current_y_val:.3f})" if func_info["dim"] == 3 else f"{current_x_val:.3f}"
        st.markdown(
            f"""
    <div style='background-color: #eff6ff; padding: 18px; border-radius: 12px; text-align: center; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
        <h3 style='color: #1e40af; margin: 0; font-size:14px;'>当前点坐标</h3>
        <h1 style='color: #3b82f6; margin: 10px 0;font-size: 28px;'>{coord_text}</h1>
    </div>
    """,
            unsafe_allow_html=True,
        )

    with col3:
        current_func_val = f(current_x_val, current_y_val)
        current_func_val = np.nan_to_num(current_func_val, nan=0, posinf=1e6, neginf=-1e6)
        st.markdown(
            f"""
    <div style='background-color: #fffbeb; padding: 18px; border-radius: 12px; text-align: center; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
        <h3 style='color: #92400e; margin: 0; font-size:14px;'>当前函数值</h3>
        <h1 style='color: #f97316; margin: 10px 0;font-size: 28px;'>{current_func_val:.3f}</h1>
    </div>
    """,
            unsafe_allow_html=True,
        )

    with col4:
        if func_info["dim"] == 2:
            current_grad = numerical_gradient(f, current_x_val, np.nan)
        else:
            current_grad = numerical_gradient(f, current_x_val, current_y_val)
        grad_norm = np.linalg.norm(current_grad)
        grad_norm = np.nan_to_num(grad_norm, nan=0, posinf=1e6, neginf=-1e6)
        st.markdown(
            f"""
    <div style='background-color: #fef2f2; padding: 18px; border-radius: 12px; text-align: center; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
        <h3 style='color: #9f1239; margin: 0; font-size:14px;'>当前梯度范数</h3>
        <h1 style='color: #ec4899; margin: 10px 0;font-size: 28px;'>{grad_norm:.3f}</h1>
    </div>
    """,
            unsafe_allow_html=True,
        )

    if max_step > 0:
        st.subheader("🎯 收敛结果")
        st.markdown("<br/>", unsafe_allow_html=True)  

        final_point = points[-1]
        final_value = f(final_point[0], final_point[1])
        final_value = np.nan_to_num(final_value, nan=0, posinf=1e6, neginf=-1e6)
        final_grad_norm = np.linalg.norm(final_grad)
        final_grad_norm = np.nan_to_num(final_grad_norm, nan=0, posinf=1e6, neginf=-1e6)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
        <div style='background-color: #f0fdf4; padding: 20px; border-radius: 12px; border-left: 5px solid #22c55e; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
            <h4 style='color: #166534; margin: 0 0 12px 0; font-size:16px;'>最终状态</h4>
            <p style='margin:6px 0;color:#166534;'><strong>最终点坐标:</strong> ({:.2f}, {:.2f})</p>
            <p style='margin:6px 0;color:#166534;'><strong>最终函数值:</strong> {:.2f}</p>
        </div>
        """.format(final_point[0], final_point[1], final_value),
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
        <div style='background-color: #eff6ff; padding: 20px; border-radius: 12px; border-left: 5px solid #3b82f6; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
            <h4 style='color: #1e40af; margin: 0 0 12px 0; font-size:16px;'>梯度信息</h4>
            <p style='margin:6px 0;color:#1e40af;'><strong>最终梯度:</strong> ({:.2f}, {:.2f})</p>
            <p style='margin:6px 0;color:#1e40af;'><strong>梯度范数:</strong> {:.2f}</p>
        </div>
        """.format(final_grad[0], final_grad[1], final_grad_norm),
                unsafe_allow_html=True,
            )

        st.markdown("")

        if final_grad_norm < 1e-3:
            st.markdown(
                """
        <div style='text-align: center; padding: 20px; background-color: #d4edda; border-radius: 12px; border: 1px solid #c3e6cb; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
            <h3 style='color: #155724; margin: 0; font-size:18px;'>✅ 已收敛</h3>
            <p style='color: #155724; margin: 10px 0 0 0; font-size:14px;'>梯度范数 < 1e-3，达到收敛标准</p>
        </div>
        """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
        <div style='text-align: center; padding: 20px; background-color: #fff3cd; border-radius: 12px; border: 1px solid #ffeaa7; box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
            <h3 style='color: #856404; margin: 0; font-size:18px;'>⚠️ 未完全收敛</h3>
            <p style='color: #856404; margin: 10px 0 0 0; font-size:14px;'>建议：增大迭代次数/调整学习率</p>
        </div>
        """,
                unsafe_allow_html=True,
            )
        st.markdown("<br/>", unsafe_allow_html=True)

    with st.expander("📖 梯度下降算法原理详解", expanded=False):
        st.markdown(
            """
    ### 🔍 核心思想
    梯度下降是一阶优化算法，通过沿梯度反方向迭代更新参数，寻找函数局部最小值：
    $$\\mathbf{x}_{t+1} = \\mathbf{x}_t - \\alpha \\cdot \\nabla f(\\mathbf{x}_t)$$
    其中：$\\alpha$=学习率，$\\nabla f$=函数梯度

    ### 🚀 自动求梯度原理（数值微分法）
    系统采用**中心差分法**自动计算梯度，无需手动输入：
    - 单变量：$f'(x) \\approx \\frac{f(x+h) - f(x-h)}{2h}$
    - 多变量：$\\frac{\\partial f}{\\partial x} \\approx \\frac{f(x+h,y) - f(x-h,y)}{2h}$，$\\frac{\\partial f}{\\partial y} \\approx \\frac{f(x,y+h) - f(x,y-h)}{2h}$
    - $h$=固定为1e-5（平衡精度和稳定性）

    ### ⚡ 关键参数说明
    1. **学习率**：
       - 过小：收敛极慢，需要更多迭代
       - 过大：可能越过最优解，甚至发散
       - 建议范围：0.01 ~ 0.1（根据函数调整）
    2. **迭代次数**：
       - 凸函数：50~100次即可收敛
       - 非凸函数：可能需要更多次数，或陷入局部最优

    ### 📌 自定义函数使用规范
    1. 支持的数学函数：
       - 三角函数：sin(x)、cos(x)、tan(x)
       - 指数/对数：exp(x)、log(x)（自然对数）
       - 其他：abs(x)（绝对值）、sqrt(x)（平方根）、pow(x,2)（幂次）
    2. 表达式格式：
       - 幂次：x² → x^2，x³+y² → x^3 + y^2
       - 乘法：2x → 2x（自动解析为2*x），3*sin(x)
       - 多变量：x^2 + y^2（无需输入梯度）
    3. 注意事项：
       - 避免使用全角符号（如：（）、，）
       - 避免极端值（如1e10），防止数值溢出
       - 非光滑函数（如|x|）：梯度为数值近似值
    """
        )


if __name__ == "__main__":
    run()