import streamlit as st
import pandas as pd

from aid_integrated.auth.service import list_users, update_user_role, update_user_email, reset_user_password


def render():
    st.title("用户管理")
    st.caption("仅管理员可见：查看用户、修改角色、更新邮箱、重置密码")

    users = list_users()
    if not users:
        st.info("暂无用户")
        return

    df = pd.DataFrame(users)
    st.dataframe(df, width="stretch", hide_index=True)

    st.divider()
    st.subheader("编辑用户")

    user_id = st.selectbox("选择用户 ID", [u["id"] for u in users])
    user = next(u for u in users if u["id"] == user_id)

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"用户名：**{user['username']}**")
        st.write(f"当前角色：**{user['role']}**")
        new_role = st.selectbox("设置角色", ["user", "admin"], index=0 if user["role"] == "user" else 1)
        if st.button("更新角色"):
            update_user_role(user_id, new_role)
            st.success("角色已更新")
            st.rerun()

    with col2:
        st.write(f"邮箱：**{user['email']}**")
        new_email = st.text_input("更新邮箱", value=user["email"], key="admin_update_email")
        if st.button("更新邮箱"):
            ok, msg = update_user_email(user_id, new_email)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    st.divider()
    st.subheader("重置密码（管理员操作）")
    new_pw = st.text_input("新密码（至少6位）", type="password", key="admin_reset_pw")
    if st.button("重置该用户密码"):
        ok, msg = reset_user_password(user_id, new_pw)
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()
