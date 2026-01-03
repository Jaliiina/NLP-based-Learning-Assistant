import streamlit as st
from .service import register_user, login_user

def render_login_register() -> None:
    st.markdown(
        """
        <style>
        /* 1. 完全移除Tab栏的默认分割线（包括红色/灰色） */
        div[data-testid="stTabs"] > div:first-child {
            border-bottom: none !important; /* 彻底清空底部分割线 */
        }
        /* 2. Tab按钮样式（未选中）- 无边框 + 增大字号 */
        button[data-baseweb="tab"] {
            font-size: 22px !important; /* 增大登录/注册字号（原18px，可按需调整） */
            font-weight: 600 !important;
            color: #333 !important;
            border-bottom: none !important; /* 清空未选中态边框 */
            padding-bottom: 8px !important;
        }
        /* 3. Tab按钮样式（选中）- 仅保留蓝色下划线 */
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #007bff !important;
            background-color: transparent !important;
        }
        /* 4. 去除Tab选中时的高亮阴影 */
        button[data-baseweb="tab"][aria-selected="true"]:focus {
            box-shadow: none !important;
        }
        /* 5. 按钮纯蓝色（强制所有按钮为蓝色，确保登录按钮变蓝） */
        div.stButton > button {
            background-color: #007bff !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 10px 0 !important;
        }
        div.stButton > button:hover {
            background-color: #0056b3 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="max-width: 980px; margin: 0 auto; padding: 10px 0 6px 0;">
          <div style="font-size: 40px; font-weight: 800; letter-spacing: 0.5px; line-height: 1.15;">
            基于 NLP 的讲义助学工具
          </div>
          <div style="margin-top: 8px; color: rgba(49, 51, 63, 0.65); font-size: 15px;">
            Lecture Assistant · NLP-powered Study Helper
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
        

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        try:
            st.image(
                image="auth/image.png",
                width="stretch",
                caption="智能助手 · 高效处理"
            )
        except FileNotFoundError:
            st.markdown(
                """
                <div style="margin-top: 50px; text-align: center; color: #007bff;">
                    <div style="font-size: 40px;">📦</div>
                    <div style="margin-top: 10px; font-size: 18px;">智能助手 · 高效处理</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    with col2:
        tab_login, tab_register = st.tabs(["登录", "注册"])
        
        with tab_login:
            identifier = st.text_input("用户名或邮箱", key="auth_login_identifier")
            password = st.text_input("密码", type="password", key="auth_login_password")
            
            if st.button(
                "登录",
                width="stretch",
                key="login_btn",
                help="点击登录系统"
            ):
                ok, msg = login_user(identifier, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        
        with tab_register:
            username = st.text_input("用户名（3-20位，字母/数字/下划线）", key="auth_reg_username")
            email = st.text_input("邮箱", key="auth_reg_email")
            password = st.text_input("密码（至少6位）", type="password", key="auth_reg_password")
            if st.button(
                "注册",
                width="stretch",
                key="reg_btn"
            ):
                ok, msg = register_user(username, email, password)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)