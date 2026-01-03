from pathlib import Path

import streamlit as st

from aid_integrated.gradient_descent.gra_app import run as run_gradient_descent


def render() -> None:
    st.header("📊 梯度下降可视化")

    run_gradient_descent()
