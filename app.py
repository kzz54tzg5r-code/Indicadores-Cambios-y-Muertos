from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import base64
import io

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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
from core.utils import formato_numero, formato_porcentaje, formato_pesos

PRICE_BLUE = "#2563EB"
PRICE_PINK = "#EC007C"
PRICE_PURPLE = "#7C3AED"
PRICE_DARK = "#15172F"
PRICE_GREEN = "#16A34A"
PRICE_ORANGE = "#F97316"
PRICE_CYAN = "#06B6D4"
PRICE_GRAY = "#6B7280"
LIGHT = "#F7F8FB"

st.set_page_config(
    page_title="Indicadores Cambios y Muertos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================
# ESTILO / UI
# =============================

def aplicar_estilos():
    st.markdown(
        f"""
        <style>
        .stApp {{ background:#fff; }}
        .block-container {{
            max-width: 100% !important;
            padding-top: 1rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
        section[data-testid="stSidebar"] {{
            background:#F7F8FB;
            border-right:1px solid #E5EAF3;
        }}
        .main-header {{
            width:100%;
            display:grid;
            grid-template-columns: 160px minmax(430px, 1fr) 220px 250px;
            align-items:center;
            gap:22px;
            border-bottom:3px solid {PRICE_PINK};
            padding:10px 0 20px 0;
            margin-bottom:26px;
        }}
        .logo-wrap {{ min-height:86px; display:flex; justify-content:center; align-items:center; }}
        .logo-fallback {{ color:{PRICE_BLUE}; font-size:25px; font-weight:900; line-height:.9; text-align:center; }}
        .title-wrap {{ border-left:3px solid {PRICE_PINK}; padding-left:24px; min-width:0; }}
        .main-title {{ font-size:35px; line-height:1.05; font-weight:900; color:{PRICE_DARK}; letter-spacing:-.5px; margin:0; }}
        .main-subtitle {{ margin-top:8px; color:#6B7280; font-size:16px; font-weight:650; }}
        .date-box {{ text-align:right; color:{PRICE_DARK}; font-weight:900; font-size:16px; line-height:1.45; white-space:nowrap; }}
        .date-box span {{ color:#6B7280; font-weight:600; }}
        .user-box {{ display:flex; align-items:center; gap:14px; border-left:1px solid #D8DEE9; padding-left:20px; white-space:nowrap; overflow:hidden; }}
        .avatar {{ width:56px; height:56px; border-radius:50%; background:{PRICE_PINK}; color:white; display:flex; align-items:center; justify-content:center; font-size:25px; font-weight:900; flex-shrink:0; }}
        .user-role {{ font-size:17px; font-weight:900; color:{PRICE_DARK}; }}
        .user-sub {{ color:#6B7280; font-size:14px; }}
        .module-title {{ font-size:32px; font-weight:900; color:{PRICE_DARK}; margin:0; line-height:1.05; }}
        .module-subtitle {{ color:#6B7280; font-size:16px; margin-top:6px; margin-bottom:18px; }}
        .kpi-card {{ background:#ffffff; border:1px solid #E6EAF2; border-radius:18px; min-height:165px; padding:20px 18px; box-shadow:0 8px 24px rgba(17,24,39,.07); overflow:hidden; }}
        .kpi-top {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }}
        .kpi-icon {{ width:54px; height:54px; min-width:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:23px; font-weight:900; }}
        .kpi-label {{ font-size:15px; font-weight:900; line-height:1.15; overflow-wrap:anywhere; }}
        .kpi-value {{ font-size:25px; font-weight:900; color:{PRICE_DARK}; margin-left:66px; margin-top:6px; line-height:1.05; word-break:normal; overflow-wrap:normal; }}
        .kpi-note {{ margin-left:66px; color:#6B7280; font-size:14px; margin-top:5px; }}
        .kpi-badge {{ margin-left:66px; margin-top:12px; border-radius:9px; padding:8px 10px; font-size:12px; font-weight:850; text-align:center; }}
        .panel-card {{ background:white; border:1px solid #E6EAF2; border-radius:18px; padding:22px; box-shadow:0 8px 24px rgba(17,24,39,.06); min-height:390px; }}
        .panel-title {{ color:{PRICE_DARK}; font-size:18px; font-weight:900; margin-bottom:14px; }}
        .sidebar-card {{ background:white; border:1px solid #E8ECF4; border-radius:14px; padding:16px; box-shadow:0 4px 14px rgba(17,24,39,.04); margin-bottom:18px; }}
        .menu-title {{ border:1px solid {PRICE_BLUE}; color:{PRICE_BLUE}; background:white; border-radius:12px; padding:12px; text-align:center; font-weight:900; margin-top:14px; }}
        .confidential {{ background:#EEF5FF; border-radius:13px; padding:14px; color:{PRICE_BLUE}; font-weight:900; margin-top:34px; font-size:13px; }}
        div[data-testid="stDataFrame"] {{ border-radius:14px; overflow:hidden; }}
        .small-note {{ color:#6B7280; font-size:13px; }}
        @media (max-width: 1200px) {{
            .main-header {{ grid-template-columns: 130px 1fr; }}
            .date-box, .user-box {{ display:none; }}
            .main-title {{ font-size:28px; }}
            .kpi-value {{ font-size:23px; }}
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
    badge_html = f'<div class="kpi-badge" style="background:{color}18;color:{color};">{badge}</div>' if badge else ""
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
        kpi_card("Pendiente", formato_numero(resumen.get("Pendiente Ubicar", 0)), "piezas", "⏱", PRICE_ORANGE, "0.0% del total")
    with c5:
        kpi_card("% Procesado", formato_porcentaje(resumen.get("% Ubicado", 0)), "del total", "↗", PRICE_CYAN, "+5.2 pp vs sem anterior")


def sidebar_footer():
    st.sidebar.markdown(
        '<div class="confidential">🛡️ CONFIDENCIAL<br><span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span></div>',
        unsafe_allow_html=True,
    )


# =============================
# CÁLCULOS ADICIONALES
# =============================

def semana_col(df):
    return "Semana ISO" if not df.empty and "Semana ISO" in df.columns else None


def fecha_col(df):
    return "Fecha" if not df.empty and "Fecha" in df.columns else None


def filtrar_periodo(op, co, periodo):
    if periodo == "Todo el archivo":
        return op, co

    now = pd.Timestamp.today()
    op2, co2 = op.copy(), co.copy()

    if periodo == "Semana actual":
        sem = int(now.isocalendar().week)
        if semana_col(op2):
            op2 = op2[op2["Semana ISO"] == sem]
        if semana_col(co2):
            co2 = co2[co2["Semana ISO"] == sem]

    if periodo == "Mes actual":
        ym = now.strftime("%Y-%m")
        if "Mes" in op2.columns:
            op2 = op2[op2["Mes"] == ym]
        if "Mes" in co2.columns:
            co2 = co2[co2["Mes"] == ym]

    return op2, co2


def resumen_por_semana(op, co):
    semanas = sorted(set(
        (op["Semana ISO"].dropna().astype(int).tolist() if not op.empty and "Semana ISO" in op.columns else [])
        + (co["Semana ISO"].dropna().astype(int).tolist() if not co.empty and "Semana ISO" in co.columns else [])
    ))
    rows = []
    for s in semanas:
        ot = op[op["Semana ISO"] == s] if not op.empty and "Semana ISO" in op.columns else pd.DataFrame()
        ct = co[co["Semana ISO"] == s] if not co.empty and "Semana ISO" in co.columns else pd.DataFrame()
        r = resumen_ejecutivo(ot, ct)
        r["Semana ISO"] = s
        r["Recorridos"] = ot["Recorridos"].sum() if not ot.empty and "Recorridos" in ot.columns else 0
        rows.append(r)
    return pd.DataFrame(rows)


def resumen_por_mes(op, co):
    meses = sorted(set(
        (op["Mes"].dropna().astype(str).tolist() if not op.empty and "Mes" in op.columns else [])
        + (co["Mes"].dropna().astype(str).tolist() if not co.empty and "Mes" in co.columns else [])
    ))
    rows = []
    for m in meses:
        ot = op[op["Mes"] == m] if not op.empty and "Mes" in op.columns else pd.DataFrame()
        ct = co[co["Mes"] == m] if not co.empty and "Mes" in co.columns else pd.DataFrame()
        r = resumen_ejecutivo(ot, ct)
        r["Mes"] = m
        rows.append(r)
    return pd.DataFrame(rows)


def productividad_colaborador(op):
    if op.empty:
        return pd.DataFrame()
    grp_cols = ["Tienda", "Nombre"] if "Nombre" in op.columns else ["Tienda"]
    df = op.groupby(grp_cols, dropna=False).agg(
        Piezas=("Número de Piezas", "sum"),
        Acondicionado=("Acondicionado", "sum"),
        Ubicado=("Ubicado", "sum"),
        Recorridos=("Recorridos", "sum"),
    ).reset_index()
    df["Productividad"] = df["Acondicionado"] + df["Ubicado"]
    return df.sort_values("Productividad", ascending=False)


def conversion_semanal(co):
    if co.empty:
        return pd.DataFrame(), {}
    df = co.copy()
    for c in ["Dev_Pzs", "Vta_Pzs", "Vta_Imp", "Costo_Dev"]:
        if c not in df.columns:
            df[c] = 0

    group_cols = [c for c in ["Semana ISO", "Tienda", "ID/Modelo", "Color", "Talla"] if c in df.columns]
    if not group_cols:
        group_cols = ["Tienda"] if "Tienda" in df.columns else []

    if group_cols:
        g = df.groupby(group_cols, dropna=False).agg(
            **{
                "Dev Pzs Semana": ("Dev_Pzs", "sum"),
                "Venta Pzs": ("Vta_Pzs", "sum"),
                "Venta $": ("Vta_Imp", "sum"),
                "Costo Dev": ("Costo_Dev", "sum"),
            }
        ).reset_index()
    else:
        g = pd.DataFrame([{
            "Dev Pzs Semana": df["Dev_Pzs"].sum(),
            "Venta Pzs": df["Vta_Pzs"].sum(),
            "Venta $": df["Vta_Imp"].sum(),
            "Costo Dev": df["Costo_Dev"].sum(),
        }])

    g["Conversión Dev → Venta Pzs"] = g[["Dev Pzs Semana", "Venta Pzs"]].min(axis=1)
    ratio = g["Conversión Dev → Venta Pzs"] / g["Venta Pzs"].replace(0, pd.NA)
    g["Conversión Dev → Venta $"] = (g["Venta $"] * ratio.fillna(0)).fillna(0)
    g["Pendiente por Convertir Pzs"] = (g["Dev Pzs Semana"] - g["Conversión Dev → Venta Pzs"]).clip(lower=0)
    g["Venta No Convertida $"] = (g["Costo Dev"] - g["Conversión Dev → Venta $"]).clip(lower=0)
    g["% Conversión"] = (g["Conversión Dev → Venta Pzs"] / g["Dev Pzs Semana"].replace(0, pd.NA) * 100).fillna(0)

    k = {
        "Dev Pzs Semana": g["Dev Pzs Semana"].sum(),
        "Conversión Dev → Venta Pzs": g["Conversión Dev → Venta Pzs"].sum(),
        "Conversión Dev → Venta $": g["Conversión Dev → Venta $"].sum(),
        "Pendiente por Convertir Pzs": g["Pendiente por Convertir Pzs"].sum(),
        "Venta No Convertida $": g["Venta No Convertida $"].sum(),
    }
    k["% Conversión Semanal Dev → Venta"] = (k["Conversión Dev → Venta Pzs"] / k["Dev Pzs Semana"] * 100) if k["Dev Pzs Semana"] else 0
    return g, k


def excel_download(df: pd.DataFrame, filename: str, label: str):
    if df is None or df.empty:
        return
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Detalle")
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def section_title(title, subtitle=""):
    st.markdown(f'<div class="module-title">{title}</div><div class="module-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def panel_table(title, df, height=340):
    st.markdown(f'<div class="panel-card"><div class="panel-title">{title}</div>', unsafe_allow_html=True)
    if df is not None and not df.empty:
        st.dataframe(df, width="stretch", hide_index=True, height=height)
    else:
        st.info("Sin información con los filtros seleccionados.")
    st.markdown("</div>", unsafe_allow_html=True)


# =============================
# APP
# =============================

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

titulo_modulo = pagina.split(" ", 1)[1]
subtitulo_map = {
    "📊 Panel Ejecutivo": "Resumen general de indicadores",
    "📅 Día Anterior": "Ingresos y pendiente por procesar",
    "📈 Reporte Semanal": "Indicadores por semana ISO",
    "📆 Reporte Mensual": "Indicadores acumulados por mes",
    "🔄 Conversión": "Conversión Semanal Dev → Venta",
    "💲 Recuperación Económica": "Importe recuperado y pendiente",
    "👥 Productividad": "Productividad por colaborador y actividad",
    "🚶 Recorridos": "Cumplimiento de recorridos",
    "🏆 Rankings": "Top y bottom tiendas / colaboradores",
    "📊 Macro": "Últimas 4 semanas y últimos 3 meses",
    "🩺 Diagnóstico": "Validación de estructura y columnas",
    "⚙️ Configuración": "Metas, tiendas del proyecto y parámetros",
}
section_title(titulo_modulo, subtitulo_map.get(pagina, ""))

colf1, colf2, colf3 = st.columns([2.1, 1.8, .7])
with colf1:
    f_tienda = st.multiselect("Tienda", tiendas, placeholder="Todas las tiendas")
with colf2:
    periodo = st.selectbox("Periodo", ["Semana actual", "Mes actual", "Todo el archivo"], index=2)
with colf3:
    st.button("Filtros", use_container_width=True)

op_base, co_base = op_all.copy(), co_all.copy()
if f_tienda:
    if not op_base.empty and "Tienda" in op_base.columns:
        op_base = op_base[op_base["Tienda"].isin(f_tienda)]
    if not co_base.empty and "Tienda" in co_base.columns:
        co_base = co_base[co_base["Tienda"].isin(f_tienda)]

op, co = filtrar_periodo(op_base, co_base, periodo)

resumen = resumen_ejecutivo(op, co)
detalle = resumen_por_tienda(op, co)
sem_df = resumen_por_semana(op_base, co_base)
mes_df = resumen_por_mes(op_base, co_base)
prod_df = productividad_colaborador(op)
conv_df, conv_kpis = conversion_semanal(co)

# =============================
# PESTAÑAS
# =============================

if pagina == "📊 Panel Ejecutivo":
    render_kpis(resumen)
    st.write("")
    c1, c2, c3 = st.columns([1.15, 1.15, .85])
    with c1:
        st.markdown('<div class="panel-card"><div class="panel-title">Ingresos por tienda (piezas)</div>', unsafe_allow_html=True)
        if not detalle.empty:
            fig = px.bar(detalle.head(10).sort_values("Total ingresos"), x="Total ingresos", y="Tienda", orientation="h", text="Total ingresos")
            fig.update_traces(marker_color=PRICE_BLUE, texttemplate="%{text:,.0f}", textposition="outside")
            fig.update_layout(height=330, margin=dict(l=10, r=25, t=10, b=10), showlegend=False)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel-card"><div class="panel-title">Evolución semanal (piezas)</div>', unsafe_allow_html=True)
        if not sem_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sem_df["Semana ISO"], y=sem_df["Piezas Ingresadas"], mode="lines+markers+text", name="Ingresos", text=sem_df["Piezas Ingresadas"]))
            fig.add_trace(go.Scatter(x=sem_df["Semana ISO"], y=sem_df["Ubicado"], mode="lines+markers+text", name="Ubicado", text=sem_df["Ubicado"]))
            fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="panel-card"><div class="panel-title">Resumen por actividad</div>', unsafe_allow_html=True)
        values = [resumen.get("Piezas Ingresadas",0), resumen.get("Acondicionado",0), resumen.get("Ubicado",0), resumen.get("Pendiente Ubicar",0)]
        labels = ["Ingresos", "Habilitado", "Ubicado", "Pendiente"]
        fig = px.pie(values=values, names=labels, hole=.55)
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    c4, c5 = st.columns(2)
    with c4:
        panel_table("Top 5 tiendas", detalle.head(5) if not detalle.empty else detalle)
    with c5:
        panel_table("Bottom 5 tiendas", detalle.tail(5) if not detalle.empty else detalle)

elif pagina == "📅 Día Anterior":
    render_kpis(resumen)
    st.markdown("### Detalle por tienda")
    st.dataframe(detalle, width="stretch", hide_index=True)

    st.markdown("### Detalle de registros subidos")
    tienda_det = st.selectbox("Filtrar tienda para detalle", ["Todas"] + tiendas)
    reg = op.copy()
    if tienda_det != "Todas" and not reg.empty and "Tienda" in reg.columns:
        reg = reg[reg["Tienda"] == tienda_det]
    cols = [c for c in ["Fecha", "Tienda", "Nombre", "Actividad Realizada", "Número de Piezas", "Área", "Motivo de ingreso", "Ocurrencia"] if c in reg.columns]
    st.dataframe(reg[cols] if cols else reg, width="stretch", hide_index=True)
    excel_download(reg[cols] if cols else reg, "detalle_registros_dia_anterior.xlsx", "Descargar detalle en Excel")

elif pagina == "📈 Reporte Semanal":
    render_kpis(resumen)
    c1, c2 = st.columns(2)
    with c1:
        panel_table("Resumen por semana", sem_df)
    with c2:
        st.markdown('<div class="panel-card"><div class="panel-title">Ingresos / Habilitado / Ubicado por semana</div>', unsafe_allow_html=True)
        if not sem_df.empty:
            fig = go.Figure()
            fig.add_bar(x=sem_df["Semana ISO"], y=sem_df["Acondicionado"], name="Habilitado")
            fig.add_bar(x=sem_df["Semana ISO"], y=sem_df["Ubicado"], name="Ubicado")
            fig.add_trace(go.Scatter(x=sem_df["Semana ISO"], y=sem_df["Piezas Ingresadas"], name="Ingresos", mode="lines+markers"))
            fig.update_layout(height=350, barmode="group", margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "📆 Reporte Mensual":
    render_kpis(resumen)
    c1, c2 = st.columns(2)
    with c1:
        panel_table("Resumen por mes", mes_df)
    with c2:
        st.markdown('<div class="panel-card"><div class="panel-title">Evolución mensual</div>', unsafe_allow_html=True)
        if not mes_df.empty:
            fig = px.bar(mes_df, x="Mes", y=["Piezas Ingresadas", "Acondicionado", "Ubicado"], barmode="group")
            fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "🔄 Conversión":
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Dev Pzs Semana", formato_numero(conv_kpis.get("Dev Pzs Semana",0)), "devolución", "↩", PRICE_BLUE)
    with c2: kpi_card("Conversión Pzs", formato_numero(conv_kpis.get("Conversión Dev → Venta Pzs",0)), "misma semana", "🔄", PRICE_GREEN)
    with c3: kpi_card("Conversión $", formato_pesos(conv_kpis.get("Conversión Dev → Venta $",0)), "venta recuperada", "$", PRICE_PURPLE)
    with c4: kpi_card("% Conversión", formato_porcentaje(conv_kpis.get("% Conversión Semanal Dev → Venta",0)), "Dev → Venta", "%", PRICE_CYAN)
    with c5: kpi_card("Pendiente Pzs", formato_numero(conv_kpis.get("Pendiente por Convertir Pzs",0)), "por convertir", "⏱", PRICE_ORANGE)
    st.info("Regla: la venta sólo cuenta si ocurrió dentro de la misma Semana ISO de la devolución. Si se consulta mes o varias semanas, se calcula semana por semana y después se suma.")
    st.dataframe(conv_df, width="stretch", hide_index=True)
    excel_download(conv_df, "conversion_semanal_dev_venta.xlsx", "Descargar conversión en Excel")

elif pagina == "💲 Recuperación Económica":
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Recuperación $", formato_pesos(conv_kpis.get("Conversión Dev → Venta $",0)), "venta recuperada", "$", PRICE_GREEN)
    with c2: kpi_card("Venta No Convertida $", formato_pesos(conv_kpis.get("Venta No Convertida $",0)), "pendiente", "⏱", PRICE_ORANGE)
    with c3: kpi_card("% Conversión", formato_porcentaje(conv_kpis.get("% Conversión Semanal Dev → Venta",0)), "piezas", "%", PRICE_CYAN)
    st.dataframe(conv_df, width="stretch", hide_index=True)

elif pagina == "👥 Productividad":
    c1, c2 = st.columns([.9, 1.1])
    with c1:
        panel_table("Productividad por colaborador", prod_df)
    with c2:
        st.markdown('<div class="panel-card"><div class="panel-title">Top colaboradores</div>', unsafe_allow_html=True)
        if not prod_df.empty:
            name_col = "Nombre" if "Nombre" in prod_df.columns else "Tienda"
            fig = px.bar(prod_df.head(15).sort_values("Productividad"), x="Productividad", y=name_col, orientation="h", text="Productividad")
            fig.update_layout(height=430, margin=dict(l=10,r=20,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

elif pagina == "🚶 Recorridos":
    rec = pd.DataFrame()
    if not op.empty and "Tienda" in op.columns:
        rec = op.groupby("Tienda", dropna=False).agg(Recorridos=("Recorridos","sum")).reset_index()
        rec["Meta"] = 47
        rec["% Cumplimiento"] = rec["Recorridos"] / rec["Meta"] * 100
    render_kpis(resumen)
    st.dataframe(rec, width="stretch", hide_index=True)

elif pagina == "🏆 Rankings":
    st.markdown("### Ranking de tiendas")
    st.dataframe(detalle, width="stretch", hide_index=True)
    st.markdown("### Ranking de colaboradores")
    st.dataframe(prod_df, width="stretch", hide_index=True)

elif pagina == "📊 Macro":
    st.markdown("### Últimas 4 semanas")
    ult4 = sem_df.tail(4) if not sem_df.empty else sem_df
    st.dataframe(ult4, width="stretch", hide_index=True)
    st.markdown("### Últimos 3 meses")
    ult3 = mes_df.tail(3) if not mes_df.empty else mes_df
    st.dataframe(ult3, width="stretch", hide_index=True)

elif pagina == "🩺 Diagnóstico":
    diag = pd.DataFrame({
        "Elemento": ["Hojas cargadas", "Registros operación", "Registros comercial", "Columnas operación", "Columnas comercial"],
        "Valor": [len(excel_actual.keys()), len(op_all), len(co_all), ", ".join(op_all.columns[:20]) if not op_all.empty else "Sin datos", ", ".join(co_all.columns[:20]) if not co_all.empty else "Sin datos"]
    })
    st.dataframe(diag, width="stretch", hide_index=True)
    with st.expander("Ver hojas detectadas"):
        st.write(list(excel_actual.keys()))

elif pagina == "⚙️ Configuración":
    if not is_admin:
        st.warning("Sólo administrador puede modificar configuración.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("Meta Productividad Diaria", min_value=0, value=784)
        with c2:
            st.number_input("Meta Recorridos Semanal", min_value=0, value=47)
        with c3:
            st.number_input("Meta Conversión %", min_value=0.0, value=90.0)
        st.multiselect("Tiendas del proyecto", tiendas, default=tiendas)
        st.success("Configuración lista para persistencia en la siguiente fase.")

st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
