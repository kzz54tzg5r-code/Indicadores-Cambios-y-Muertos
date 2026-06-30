from __future__ import annotations
import streamlit as st
import plotly.express as px
from core.auth import obtener_rol_sidebar
from core.indicadores import resumen_ejecutivo, resumen_por_tienda
from core.loader import cargar_excel_actual
from core.normalizador import detectar_y_normalizar_hojas
from core.storage import borrar_archivo_persistente, existe_archivo_persistente, guardar_archivo_persistente, obtener_metadata_archivo
from core.ui import aplicar_estilos, render_header, render_kpis, sidebar_menu, sidebar_footer

st.set_page_config(page_title="Operaciones Ropa", page_icon="📊", layout="wide")
aplicar_estilos()
rol, is_admin = obtener_rol_sidebar()

st.sidebar.divider()
st.sidebar.header("📁 Fuente de datos")
metadata = obtener_metadata_archivo()
if existe_archivo_persistente():
    st.sidebar.success("Archivo cargado")
    st.sidebar.markdown(f"""<div class="sidebar-card"><b>📗 Archivo cargado</b><br>{metadata.get('nombre_original','Sin nombre')}<br><br><span style="color:#6B7280;">Actualizado: {metadata.get('fecha_carga','Sin fecha')}</span></div>""", unsafe_allow_html=True)
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

tiendas = sorted(set((op_all["Tienda"].dropna().astype(str).tolist() if not op_all.empty and "Tienda" in op_all.columns else []) + (co_all["Tienda"].dropna().astype(str).tolist() if not co_all.empty and "Tienda" in co_all.columns else [])))
colf1, colf2, colf3 = st.columns([2,2,1])
with colf1:
    f_tienda = st.multiselect("Tienda", tiendas, placeholder="Todas las tiendas")
with colf2:
    st.selectbox("Periodo", ["23 – 29 jun, 2026 (Sem 26)", "Semana actual", "Mes actual"], index=0)
with colf3:
    st.button("Filtros", use_container_width=True)

op, co = op_all.copy(), co_all.copy()
if f_tienda:
    if not op.empty and "Tienda" in op.columns: op = op[op["Tienda"].isin(f_tienda)]
    if not co.empty and "Tienda" in co.columns: co = co[co["Tienda"].isin(f_tienda)]

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
            fig.update_layout(height=340, margin=dict(l=10,r=10,t=10,b=10), showlegend=False)
            st.plotly_chart(fig, width="stretch")
        else: st.info("Sin información.")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card-panel"><div class="panel-title">Detalle por tienda</div>', unsafe_allow_html=True)
        st.dataframe(detalle, width="stretch", hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
elif pagina == "📅 Día Anterior":
    st.markdown('<div class="module-title">Día Anterior</div><div class="module-subtitle">Ingresos y pendiente por procesar</div>', unsafe_allow_html=True)
    render_kpis(resumen)
    st.dataframe(detalle, width="stretch", hide_index=True)
elif pagina == "📈 Reporte Semanal":
    st.markdown('<div class="module-title">Reporte Semanal</div><div class="module-subtitle">Indicadores por semana ISO</div>', unsafe_allow_html=True)
    render_kpis(resumen); st.dataframe(detalle, width="stretch", hide_index=True)
elif pagina == "📆 Reporte Mensual":
    st.markdown('<div class="module-title">Reporte Mensual</div><div class="module-subtitle">Indicadores acumulados del mes</div>', unsafe_allow_html=True)
    render_kpis(resumen); st.dataframe(detalle, width="stretch", hide_index=True)
elif pagina == "🔄 Conversión":
    st.markdown('<div class="module-title">Conversión Semanal Dev → Venta</div><div class="module-subtitle">Cálculo por misma semana ISO</div>', unsafe_allow_html=True); st.info("Siguiente fase.")
elif pagina == "💲 Recuperación Económica":
    st.markdown('<div class="module-title">Recuperación Económica</div><div class="module-subtitle">Importe recuperado y pendiente</div>', unsafe_allow_html=True); st.info("Siguiente fase.")
elif pagina == "👥 Productividad":
    st.markdown('<div class="module-title">Productividad</div><div class="module-subtitle">Productividad por colaborador y actividad</div>', unsafe_allow_html=True); st.info("Siguiente fase.")
elif pagina == "🚶 Recorridos":
    st.markdown('<div class="module-title">Recorridos</div><div class="module-subtitle">Cumplimiento de recorridos</div>', unsafe_allow_html=True); st.info("Siguiente fase.")
elif pagina == "🏆 Rankings":
    st.markdown('<div class="module-title">Rankings</div><div class="module-subtitle">Top y bottom tiendas / colaboradores</div>', unsafe_allow_html=True); st.dataframe(detalle, width="stretch", hide_index=True)
elif pagina == "📊 Macro":
    st.markdown('<div class="module-title">Macro</div><div class="module-subtitle">Últimas 4 semanas y últimos 3 meses</div>', unsafe_allow_html=True); st.info("Siguiente fase.")
elif pagina == "🩺 Diagnóstico":
    st.markdown('<div class="module-title">Diagnóstico</div><div class="module-subtitle">Validación de estructura y columnas</div>', unsafe_allow_html=True)
    st.write("Hojas cargadas:", list(excel_actual.keys())); st.write("Registros operación:", len(op_all)); st.write("Registros comercial:", len(co_all))
elif pagina == "⚙️ Configuración":
    st.markdown('<div class="module-title">Configuración</div><div class="module-subtitle">Metas, tiendas del proyecto y parámetros</div>', unsafe_allow_html=True)
    st.success("Panel de configuración listo para la siguiente fase.") if is_admin else st.warning("Sólo administrador puede modificar configuración.")
st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
