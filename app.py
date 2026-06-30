from __future__ import annotations

from pathlib import Path
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
            label_visibility="collapsed",
        )


def sidebar_footer():
    st.sidebar.markdown(
        '<div class="confidential">🛡️ CONFIDENCIAL<br><span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span></div>',
        unsafe_allow_html=True,
    )


def kpi_card(label, value, note="", icon="📦", color=PRICE_BLUE, badge=""):
    badge_html = f'<div class="kpi-badge" style="background:{color}18;color:{color};">{badge}</div>' if badge else ""
    st.markdown(
        f"""<div class="kpi-card"><div class="kpi-head"><div class="kpi-icon" style="background:{color};">{icon}</div><div class="kpi-label" style="color:{color};">{label}</div></div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div>{badge_html}</div>""",
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


st.set_page_config(page_title="Operaciones Ropa", page_icon="📊", layout="wide")
aplicar_estilos()

rol, is_admin = obtener_rol_sidebar()

st.sidebar.divider()
st.sidebar.header("📁 Fuente de datos")
metadata = obtener_metadata_archivo()

if existe_archivo_persistente():
    st.sidebar.success("Archivo cargado")
    st.sidebar.markdown(
        f"""<div class="sidebar-card"><b>📗 Archivo cargado</b><br>{metadata.get('nombre_original','Sin nombre')}<br><br><span style="color:#6B7280;">Actualizado: {metadata.get('fecha_carga','Sin fecha')}</span></div>""",
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

colf1, colf2, colf3 = st.columns([2, 2, 1])
with colf1:
    f_tienda = st.multiselect("Tienda", tiendas, placeholder="Todas las tiendas")
with colf2:
    st.selectbox("Periodo", ["23 – 29 jun, 2026 (Sem 26)", "Semana actual", "Mes actual"], index=0)
with colf3:
    st.button("Filtros", use_container_width=True)

op = op_all.copy()
co = co_all.copy()

if f_tienda:
    if not op.empty and "Tienda" in op.columns:
        op = op[op["Tienda"].isin(f_tienda)]
    if not co.empty and "Tienda" in co.columns:
        co = co[co["Tienda"].isin(f_tienda)]

resumen = resumen_ejecutivo(op, co)
detalle = resumen_por_tienda(op, co)

if pagina == "📊 Panel Ejecutivo":
    st.markdown('<div class="module-title">Panel Ejecutivo</div><div class="module-subtitle">Resumen general de indicadores</div>', unsafe_allow_html=True)
    render_kpis(resumen)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card-panel"><div class="panel-title">Ingresos por tienda (piezas)</div>', unsafe_allow_html=True)
        if not detalle.empty:
            fig = px.bar(detalle.head(10).sort_values("Total ingresos"), x="Total ingresos", y="Tienda", orientation="h", text="Total ingresos")
            fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card-panel"><div class="panel-title">Detalle por tienda</div>', unsafe_allow_html=True)
        st.dataframe(detalle, width="stretch", hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "📅 Día Anterior":
    st.markdown('<div class="module-title">Día Anterior</div><div class="module-subtitle">Ingresos y pendiente por procesar</div>', unsafe_allow_html=True)
    render_kpis(resumen)
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "📈 Reporte Semanal":
    st.markdown('<div class="module-title">Reporte Semanal</div><div class="module-subtitle">Indicadores por semana ISO</div>', unsafe_allow_html=True)
    render_kpis(resumen)
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "📆 Reporte Mensual":
    st.markdown('<div class="module-title">Reporte Mensual</div><div class="module-subtitle">Indicadores acumulados del mes</div>', unsafe_allow_html=True)
    render_kpis(resumen)
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "🔄 Conversión":
    st.markdown('<div class="module-title">Conversión Semanal Dev → Venta</div><div class="module-subtitle">Cálculo por misma semana ISO</div>', unsafe_allow_html=True)
    st.info("Siguiente fase.")

elif pagina == "💲 Recuperación Económica":
    st.markdown('<div class="module-title">Recuperación Económica</div><div class="module-subtitle">Importe recuperado y pendiente</div>', unsafe_allow_html=True)
    st.info("Siguiente fase.")

elif pagina == "👥 Productividad":
    st.markdown('<div class="module-title">Productividad</div><div class="module-subtitle">Productividad por colaborador y actividad</div>', unsafe_allow_html=True)
    st.info("Siguiente fase.")

elif pagina == "🚶 Recorridos":
    st.markdown('<div class="module-title">Recorridos</div><div class="module-subtitle">Cumplimiento de recorridos</div>', unsafe_allow_html=True)
    st.info("Siguiente fase.")

elif pagina == "🏆 Rankings":
    st.markdown('<div class="module-title">Rankings</div><div class="module-subtitle">Top y bottom tiendas / colaboradores</div>', unsafe_allow_html=True)
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "📊 Macro":
    st.markdown('<div class="module-title">Macro</div><div class="module-subtitle">Últimas 4 semanas y últimos 3 meses</div>', unsafe_allow_html=True)
    st.info("Siguiente fase.")

elif pagina == "🩺 Diagnóstico":
    st.markdown('<div class="module-title">Diagnóstico</div><div class="module-subtitle">Validación de estructura y columnas</div>', unsafe_allow_html=True)
    st.write("Hojas cargadas:", list(excel_actual.keys()))
    st.write("Registros operación:", len(op_all))
    st.write("Registros comercial:", len(co_all))

elif pagina == "⚙️ Configuración":
    st.markdown('<div class="module-title">Configuración</div><div class="module-subtitle">Metas, tiendas del proyecto y parámetros</div>', unsafe_allow_html=True)
    if not is_admin:
        st.warning("Sólo administrador puede modificar configuración.")
    else:
        st.success("Panel de configuración listo para la siguiente fase.")

st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
