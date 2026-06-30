from pathlib import Path
import streamlit as st
from config.colors import PRICE_BLUE, PRICE_PINK, PRICE_PURPLE, PRICE_DARK, PRICE_GREEN, PRICE_ORANGE, PRICE_CYAN
from core.utils import formato_numero, formato_porcentaje

def aplicar_estilos():
    st.markdown(f"""
    <style>
    .stApp{{background:#fff;}}
    section[data-testid="stSidebar"]{{background:#F7F8FB;border-right:1px solid #E6EAF2;}}
    .block-container{{padding-top:1.2rem;max-width:1600px;}}
    .main-header{{display:flex;align-items:center;gap:22px;border-bottom:3px solid {PRICE_PINK};padding:8px 0 22px;margin-bottom:28px;}}
    .title-block{{flex:1;border-left:3px solid {PRICE_PINK};padding-left:24px;}}
    .main-title{{font-size:34px;line-height:1.05;font-weight:900;color:{PRICE_DARK};margin:0;}}
    .main-subtitle{{font-size:16px;color:#6B7280;margin-top:6px;font-weight:600;}}
    .date-pill{{min-width:210px;text-align:right;color:{PRICE_DARK};font-weight:800;font-size:16px;}}
    .user-pill{{display:flex;align-items:center;gap:12px;padding-left:18px;border-left:1px solid #D8DEE9;min-width:230px;}}
    .avatar{{width:52px;height:52px;border-radius:50%;background:{PRICE_PINK};color:white;display:flex;align-items:center;justify-content:center;font-size:25px;font-weight:900;}}
    .module-title{{font-size:32px;color:{PRICE_DARK};font-weight:900;margin-bottom:2px;}}
    .module-subtitle{{color:#6B7280;font-size:16px;margin-bottom:20px;}}
    .kpi-card{{border:1px solid #E6EAF2;border-radius:16px;padding:22px 20px;background:white;box-shadow:0 8px 22px rgba(17,24,39,.07);min-height:158px;}}
    .kpi-head{{display:flex;align-items:center;gap:14px;margin-bottom:10px;}}
    .kpi-icon{{width:54px;height:54px;border-radius:50%;color:white;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;}}
    .kpi-label{{font-weight:900;color:{PRICE_DARK};font-size:15px;}}
    .kpi-value{{font-size:30px;font-weight:900;color:{PRICE_DARK};margin-left:68px;line-height:1;}}
    .kpi-note{{margin-left:68px;margin-top:8px;color:#6B7280;font-size:14px;}}
    .kpi-badge{{margin-left:68px;margin-top:14px;padding:8px 12px;border-radius:8px;font-size:13px;font-weight:800;text-align:center;}}
    .card-panel{{border:1px solid #E6EAF2;border-radius:16px;background:white;padding:22px;box-shadow:0 8px 22px rgba(17,24,39,.06);min-height:380px;}}
    .panel-title{{color:{PRICE_DARK};font-weight:900;font-size:18px;margin-bottom:16px;}}
    .sidebar-card{{border:1px solid #E7EBF3;background:white;border-radius:14px;padding:14px;margin:10px 0 18px;box-shadow:0 4px 12px rgba(17,24,39,.04);}}
    .menu-button{{border:1px solid {PRICE_BLUE};color:{PRICE_BLUE};border-radius:12px;padding:12px;text-align:center;font-weight:900;margin:18px 0 10px;background:white;}}
    .confidential{{background:#EEF5FF;border-radius:12px;padding:14px;color:{PRICE_BLUE};font-weight:800;font-size:13px;margin-top:40px;}}
    </style>
    """, unsafe_allow_html=True)

def render_header(is_admin=False):
    c_logo, c_main = st.columns([1, 8])
    with c_logo:
        for name in ["assets/logo_price.png", "assets/logo.png"]:
            if Path(name).exists():
                st.image(name, width=145)
                break
    role = "Administrador" if is_admin else "Consulta"
    avatar = "A" if is_admin else "C"
    with c_main:
        st.markdown(f"""
        <div class="main-header">
            <div class="title-block">
                <div class="main-title">Recuperación Cambios y Muertos</div>
                <div class="main-subtitle">Operaciones Ropa &nbsp; | &nbsp; Indicadores Compañía</div>
            </div>
            <div class="date-pill">📅 30/jun/2026<br><span style="color:#6B7280;font-weight:600;">01:25 p. m.</span></div>
            <div class="user-pill"><div class="avatar">{avatar}</div><div><div style="font-weight:900;color:{PRICE_DARK};font-size:17px;">{role}</div><div style="color:#6B7280;">Rol: {role}</div></div></div>
        </div>
        """, unsafe_allow_html=True)

def sidebar_menu():
    st.sidebar.markdown('<div class="menu-button">☰ Menú</div>', unsafe_allow_html=True)
    with st.sidebar.expander("Abrir navegación", expanded=True):
        return st.radio("Módulo", ["📊 Panel Ejecutivo","📅 Día Anterior","📈 Reporte Semanal","📆 Reporte Mensual","🔄 Conversión","💲 Recuperación Económica","👥 Productividad","🚶 Recorridos","🏆 Rankings","📊 Macro","🩺 Diagnóstico","⚙️ Configuración"], label_visibility="collapsed")

def sidebar_footer():
    st.sidebar.markdown('<div class="confidential">🛡️ CONFIDENCIAL<br><span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span></div>', unsafe_allow_html=True)

def kpi_card(label, value, note="", icon="📦", color=PRICE_BLUE, badge=""):
    badge_html = f'<div class="kpi-badge" style="background:{color}18;color:{color};">{badge}</div>' if badge else ''
    st.markdown(f"""<div class="kpi-card"><div class="kpi-head"><div class="kpi-icon" style="background:{color};">{icon}</div><div class="kpi-label" style="color:{color};">{label}</div></div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div>{badge_html}</div>""", unsafe_allow_html=True)

def render_kpis(resumen):
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi_card("Total ingresos", formato_numero(resumen.get("Piezas Ingresadas",0)), "piezas", "📦", PRICE_BLUE, "+8.6% vs sem anterior")
    with c2: kpi_card("Habilitado", formato_numero(resumen.get("Acondicionado",0)), "piezas", "✓", PRICE_GREEN, formato_porcentaje(resumen.get("% Acondicionado",0))+" del total")
    with c3: kpi_card("Ubicado", formato_numero(resumen.get("Ubicado",0)), "piezas", "📍", PRICE_PURPLE, formato_porcentaje(resumen.get("% Ubicado",0))+" del total")
    with c4: kpi_card("Pendiente", formato_numero(resumen.get("Pendiente Ubicar",0)), "piezas", "⏱", PRICE_ORANGE)
    with c5: kpi_card("% Procesado", formato_porcentaje(resumen.get("% Ubicado",0)), "del total", "↗", PRICE_CYAN)
