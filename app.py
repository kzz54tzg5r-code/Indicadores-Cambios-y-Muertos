from __future__ import annotations

from pathlib import Path
from datetime import datetime
import base64

import streamlit as st
import plotly.express as px

from core.auth import obtener_rol_sidebar
from core.indicadores import resumen_ejecutivo, resumen_por_tienda
from core.loader import cargar_excel_actual
from core.normalizador import detectar_y_normalizar_hojas
from core.storage import (
    borrar_archivo_persistente,
    existe_archivo_persistente,
    guardar_archivo_persistente,
    obtener_metadata_archivo,
)
from core.utils import formato_numero, formato_porcentaje

PRICE_BLUE = "#2563EB"
PRICE_PINK = "#EC007C"
PRICE_PURPLE = "#7C3AED"
PRICE_DARK = "#15172F"
PRICE_GREEN = "#16A34A"
PRICE_ORANGE = "#F97316"
PRICE_CYAN = "#06B6D4"


st.set_page_config(
    page_title="Recuperación Cambios y Muertos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def aplicar_estilos():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:#ffffff;
        }}

        .block-container {{
            max-width: 100% !important;
            padding-top: 1rem !important;
            padding-left: 2.5rem !important;
            padding-right: 2.5rem !important;
        }}

        section[data-testid="stSidebar"] {{
            background:#F7F8FB;
            border-right:1px solid #E5EAF3;
        }}

        section[data-testid="stSidebar"] > div {{
            padding-top: 1.1rem;
        }}

        .top-shell {{
            width:100%;
            border-bottom:3px solid {PRICE_PINK};
            margin-bottom:26px;
            padding-bottom:18px;
        }}

        .main-header {{
            width:100%;
            display:grid;
            grid-template-columns: 160px minmax(360px, 1fr) 220px 250px;
            align-items:center;
            gap:22px;
        }}

        .logo-wrap {{
            min-height:86px;
            display:flex;
            justify-content:center;
            align-items:center;
        }}

        .logo-fallback {{
            color:{PRICE_BLUE};
            font-size:25px;
            font-weight:900;
            line-height:0.9;
            text-align:center;
        }}

        .title-wrap {{
            border-left:3px solid {PRICE_PINK};
            padding-left:24px;
            min-width:0;
        }}

        .main-title {{
            font-size:34px;
            line-height:1.05;
            font-weight:900;
            color:{PRICE_DARK};
            letter-spacing:-0.6px;
            margin:0;
            white-space:normal;
        }}

        .main-subtitle {{
            margin-top:8px;
            color:#6B7280;
            font-size:16px;
            font-weight:650;
        }}

        .date-box {{
            text-align:right;
            color:{PRICE_DARK};
            font-weight:900;
            font-size:16px;
            line-height:1.45;
            white-space:nowrap;
        }}

        .date-box span {{
            color:#6B7280;
            font-weight:600;
        }}

        .user-box {{
            display:flex;
            align-items:center;
            gap:14px;
            border-left:1px solid #D8DEE9;
            padding-left:20px;
            white-space:nowrap;
        }}

        .avatar {{
            width:56px;
            height:56px;
            border-radius:50%;
            background:{PRICE_PINK};
            color:white;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:25px;
            font-weight:900;
            flex-shrink:0;
        }}

        .user-role {{
            font-size:17px;
            font-weight:900;
            color:{PRICE_DARK};
        }}

        .user-sub {{
            color:#6B7280;
            font-size:14px;
        }}

        .module-title {{
            font-size:32px;
            font-weight:900;
            color:{PRICE_DARK};
            margin:0;
            line-height:1.05;
        }}

        .module-subtitle {{
            color:#6B7280;
            font-size:16px;
            margin-top:6px;
            margin-bottom:18px;
        }}

        .kpi-card {{
            background:#ffffff;
            border:1px solid #E6EAF2;
            border-radius:18px;
            min-height:170px;
            padding:20px 18px;
            box-shadow:0 8px 24px rgba(17,24,39,.07);
            overflow:hidden;
        }}

        .kpi-top {{
            display:flex;
            align-items:center;
            gap:12px;
            margin-bottom:10px;
        }}

        .kpi-icon {{
            width:54px;
            height:54px;
            min-width:54px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:23px;
            font-weight:900;
        }}

        .kpi-label {{
            font-size:15px;
            font-weight:900;
            line-height:1.15;
            overflow-wrap:anywhere;
        }}

        .kpi-value {{
            font-size:26px;
            font-weight:900;
            color:{PRICE_DARK};
            margin-left:66px;
            margin-top:6px;
            line-height:1.05;
            word-break:normal;
            overflow-wrap:normal;
        }}

        .kpi-note {{
            margin-left:66px;
            color:#6B7280;
            font-size:14px;
            margin-top:5px;
        }}

        .kpi-badge {{
            margin-left:66px;
            margin-top:12px;
            border-radius:9px;
            padding:8px 10px;
            font-size:12px;
            font-weight:850;
            text-align:center;
        }}

        .panel-card {{
            background:white;
            border:1px solid #E6EAF2;
            border-radius:18px;
            padding:22px;
            box-shadow:0 8px 24px rgba(17,24,39,.06);
            min-height:390px;
        }}

        .panel-title {{
            color:{PRICE_DARK};
            font-size:18px;
            font-weight:900;
            margin-bottom:14px;
        }}

        .side-section {{
            font-size:22px;
            color:{PRICE_DARK};
            font-weight:900;
            margin:8px 0 12px 0;
        }}

        .sidebar-card {{
            background:white;
            border:1px solid #E8ECF4;
            border-radius:14px;
            padding:16px;
            box-shadow:0 4px 14px rgba(17,24,39,.04);
            margin-bottom:18px;
        }}

        .menu-title {{
            border:1px solid {PRICE_BLUE};
            color:{PRICE_BLUE};
            background:white;
            border-radius:12px;
            padding:12px;
            text-align:center;
            font-weight:900;
            margin-top:14px;
        }}

        .confidential {{
            background:#EEF5FF;
            border-radius:13px;
            padding:14px;
            color:{PRICE_BLUE};
            font-weight:900;
            margin-top:34px;
            font-size:13px;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius:14px;
            overflow:hidden;
        }}

        @media (max-width: 1200px) {{
            .main-header {{
                grid-template-columns: 130px 1fr;
            }}
            .date-box, .user-box {{
                display:none;
            }}
            .main-title {{
                font-size:28px;
            }}
            .kpi-value {{
                font-size:23px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def logo_html():
    for logo_name in ["assets/logo_price.png", "assets/logo.png"]:
        logo = Path(logo_name)
        if logo.exists():
            ext = logo.suffix.replace(".", "") or "png"
            data = base64.b64encode(logo.read_bytes()).decode()
            return f'<img src="data:image/{ext};base64,{data}" style="max-width:145px;max-height:86px;">'
    return '<div class="logo-fallback">Price<br>Shoes</div>'


def render_header(is_admin: bool):
    now = datetime.now()
    fecha = now.strftime("%d/%m/%Y")
    hora = now.strftime("%I:%M %p").lower().replace("am", "a. m.").replace("pm", "p. m.")
    role = "Administrador" if is_admin else "Consulta"
    avatar = "A" if is_admin else "C"

    st.markdown(
        f"""
        <div class="top-shell">
            <div class="main-header">
                <div class="logo-wrap">{logo_html()}</div>
                <div class="title-wrap">
                    <div class="main-title">Recuperación Cambios y Muertos</div>
                    <div class="main-subtitle">Operaciones Ropa &nbsp; | &nbsp; Indicadores Compañía</div>
                </div>
                <div class="date-box">📅 {fecha}<br><span>{hora}</span></div>
                <div class="user-box">
                    <div class="avatar">{avatar}</div>
                    <div>
                        <div class="user-role">{role}</div>
                        <div class="user-sub">Rol: {role}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_menu():
    st.sidebar.markdown('<div class="menu-title">☰ Menú</div>', unsafe_allow_html=True)
    with st.sidebar.expander("Abrir navegación", expanded=True):
        return st.radio(
            "Módulo",
            [
                "📊 Panel Ejecutivo",
                "📅 Día Anterior",
                "📈 Reporte Semanal",
                "📆 Reporte Mensual",
                "🔄 Conversión",
                "💲 Recuperación Económica",
                "👥 Productividad",
                "🚶 Recorridos",
                "🏆 Rankings",
                "📊 Macro",
                "🩺 Diagnóstico",
                "⚙️ Configuración",
            ],
            index=0,
            label_visibility="collapsed",
        )


def kpi_card(label, value, note="", icon="📦", color=PRICE_BLUE, badge=""):
    badge_html = ""
    if badge:
        badge_html = f'<div class="kpi-badge" style="background:{color}18;color:{color};">{badge}</div>'

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-icon" style="background:{color};">{icon}</div>
                <div class="kpi-label" style="color:{color};">{label}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(resumen):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total ingresos", formato_numero(resumen.get("Piezas Ingresadas", 0)), "piezas", "📦", PRICE_BLUE, "+8.6% vs sem anterior")
    with c2:
        kpi_card("Habilitado", formato_numero(resumen.get("Acondicionado", 0)), "piezas", "✓", PRICE_GREEN, formato_porcentaje(resumen.get("% Acondicionado", 0)) + " del total")
    with c3:
        kpi_card("Ubicado", formato_numero(resumen.get("Ubicado", 0)), "piezas", "📍", PRICE_PURPLE, formato_porcentaje(resumen.get("% Ubicado", 0)) + " del total")
    with c4:
        kpi_card("Pendiente", formato_numero(resumen.get("Pendiente Ubicar", 0)), "piezas", "⏱", PRICE_ORANGE)
    with c5:
        kpi_card("% Procesado", formato_porcentaje(resumen.get("% Ubicado", 0)), "del total", "↗", PRICE_CYAN)


def sidebar_footer():
    st.sidebar.markdown(
        '<div class="confidential">🛡️ CONFIDENCIAL<br><span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span></div>',
        unsafe_allow_html=True,
    )


aplicar_estilos()

rol, is_admin = obtener_rol_sidebar()

st.sidebar.divider()
st.sidebar.markdown('<div class="side-section">📁 Fuente de datos</div>', unsafe_allow_html=True)
metadata = obtener_metadata_archivo()

if existe_archivo_persistente():
    st.sidebar.success("Archivo cargado")
    st.sidebar.markdown(
        f"""
        <div class="sidebar-card">
            <b>📗 Archivo cargado</b><br>
            {metadata.get('nombre_original', 'Sin nombre')}<br><br>
            <span style="color:#6B7280;">Actualizado: {metadata.get('fecha_carga', 'Sin fecha')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.sidebar.warning("No hay archivo cargado")

if is_admin:
    uploaded_file = st.sidebar.file_uploader("Cargar/Reemplazar Excel", type=["xlsx"], key="excel_uploader")
    if uploaded_file is not None and st.sidebar.button("Procesar y guardar archivo", type="primary"):
        guardar_archivo_persistente(uploaded_file)
        st.sidebar.success("Archivo guardado correctamente")
        st.rerun()

    if existe_archivo_persistente() and st.sidebar.button("Borrar archivo persistido"):
        borrar_archivo_persistente()
        st.sidebar.success("Archivo eliminado")
        st.rerun()

pagina = sidebar_menu()
sidebar_footer()

render_header(is_admin=is_admin)

excel_actual = cargar_excel_actual()
if excel_actual is None:
    st.warning("Carga un archivo Excel para iniciar la plataforma.")
    st.stop()

with st.spinner("Normalizando información..."):
    op_all, co_all = detectar_y_normalizar_hojas(excel_actual)

tiendas = sorted(set(
    (op_all["Tienda"].dropna().astype(str).tolist() if not op_all.empty and "Tienda" in op_all.columns else [])
    + (co_all["Tienda"].dropna().astype(str).tolist() if not co_all.empty and "Tienda" in co_all.columns else [])
))

op = op_all.copy()
co = co_all.copy()

titulo_modulo = pagina.split(" ", 1)[1]
subtitulo = "Resumen general de indicadores" if pagina == "📊 Panel Ejecutivo" else "Indicadores de operación"
st.markdown(f'<div class="module-title">{titulo_modulo}</div><div class="module-subtitle">{subtitulo}</div>', unsafe_allow_html=True)

colf1, colf2, colf3 = st.columns([2.1, 1.8, .7])
with colf1:
    f_tienda = st.multiselect("Tienda", tiendas, placeholder="Todas las tiendas")
with colf2:
    periodo = st.selectbox("Periodo", ["Semana actual", "Mes actual", "Todo el archivo"], index=0)
with colf3:
    st.button("Filtros", use_container_width=True)

if f_tienda:
    if not op.empty and "Tienda" in op.columns:
        op = op[op["Tienda"].isin(f_tienda)]
    if not co.empty and "Tienda" in co.columns:
        co = co[co["Tienda"].isin(f_tienda)]

resumen = resumen_ejecutivo(op, co)
detalle = resumen_por_tienda(op, co)

if pagina == "📊 Panel Ejecutivo":
    render_kpis(resumen)
    st.write("")
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="panel-card"><div class="panel-title">Ingresos por tienda (piezas)</div>', unsafe_allow_html=True)
        if not detalle.empty:
            fig = px.bar(
                detalle.head(10).sort_values("Total ingresos"),
                x="Total ingresos",
                y="Tienda",
                orientation="h",
                text="Total ingresos",
            )
            fig.update_traces(marker_color=PRICE_BLUE, texttemplate="%{text:,.0f}", textposition="outside")
            fig.update_layout(height=340, margin=dict(l=10, r=20, t=10, b=10), showlegend=False)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel-card"><div class="panel-title">Detalle por tienda</div>', unsafe_allow_html=True)
        st.dataframe(detalle, width="stretch", hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "📅 Día Anterior":
    render_kpis(resumen)
    st.markdown("### Detalle por tienda")
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina in ["📈 Reporte Semanal", "📆 Reporte Mensual"]:
    render_kpis(resumen)
    st.markdown("### Detalle por tienda")
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "🔄 Conversión":
    st.info("Siguiente fase: conversión semanal Dev → Venta.")

elif pagina == "💲 Recuperación Económica":
    st.info("Siguiente fase: recuperación económica.")

elif pagina == "👥 Productividad":
    st.info("Siguiente fase: productividad por colaborador.")

elif pagina == "🚶 Recorridos":
    st.info("Siguiente fase: cumplimiento de recorridos.")

elif pagina == "🏆 Rankings":
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "📊 Macro":
    st.info("Siguiente fase: últimas 4 semanas y últimos 3 meses.")

elif pagina == "🩺 Diagnóstico":
    st.write("Hojas cargadas:", list(excel_actual.keys()))
    st.write("Registros operación:", len(op_all))
    st.write("Registros comercial:", len(co_all))

elif pagina == "⚙️ Configuración":
    if not is_admin:
        st.warning("Sólo administrador puede modificar configuración.")
    else:
        st.success("Panel de configuración listo para metas, tiendas del proyecto y parámetros.")

st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
