from __future__ import annotations

import streamlit as st
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
from core.ui import aplicar_estilos, render_header, render_kpis

st.set_page_config(page_title="ORION Operaciones Ropa", page_icon="🚀", layout="wide")

aplicar_estilos()
render_header()

rol, is_admin = obtener_rol_sidebar()

st.sidebar.divider()
st.sidebar.header("📁 Fuente de datos")

metadata = obtener_metadata_archivo()

if existe_archivo_persistente():
    st.sidebar.success("Archivo cargado")
    st.sidebar.caption(f"Archivo: {metadata.get('nombre_original', 'Sin nombre')}")
    st.sidebar.caption(f"Fecha: {metadata.get('fecha_carga', 'Sin fecha')}")
else:
    st.sidebar.warning("No hay archivo cargado")

if is_admin:
    uploaded_file = st.sidebar.file_uploader("Cargar/Reemplazar Excel", type=["xlsx"], key="excel_uploader")
    if uploaded_file is not None:
        if st.sidebar.button("🚀 Procesar y guardar archivo", type="primary"):
            guardar_archivo_persistente(uploaded_file)
            st.sidebar.success("Archivo guardado correctamente")
            st.rerun()
    if existe_archivo_persistente():
        if st.sidebar.button("🗑️ Borrar archivo persistido"):
            borrar_archivo_persistente()
            st.sidebar.success("Archivo eliminado")
            st.rerun()

excel_actual = cargar_excel_actual()
if excel_actual is None:
    st.warning("Carga un archivo Excel para iniciar ORION.")
    st.stop()

with st.spinner("Normalizando información..."):
    op_all, co_all = detectar_y_normalizar_hojas(excel_actual)

st.sidebar.divider()
st.sidebar.header("🎛️ Filtros")

tiendas = sorted(set(
    (op_all["Tienda"].dropna().astype(str).tolist() if not op_all.empty and "Tienda" in op_all.columns else [])
    + (co_all["Tienda"].dropna().astype(str).tolist() if not co_all.empty and "Tienda" in co_all.columns else [])
))

f_tienda = st.sidebar.multiselect("Tienda", tiendas)

op = op_all.copy()
co = co_all.copy()

if f_tienda:
    if not op.empty and "Tienda" in op.columns:
        op = op[op["Tienda"].isin(f_tienda)]
    if not co.empty and "Tienda" in co.columns:
        co = co[co["Tienda"].isin(f_tienda)]

pagina = st.sidebar.radio(
    "Navegación",
    ["Dashboard", "Día Anterior", "Reporte Semanal", "Reporte Mensual", "Conversión", "Recuperación Económica", "Configuración"],
)

if pagina == "Dashboard":
    st.subheader("Dashboard Ejecutivo")
    resumen = resumen_ejecutivo(op, co)
    render_kpis(resumen)
    st.markdown("### Detalle por tienda")
    detalle = resumen_por_tienda(op, co)
    st.dataframe(detalle, width="stretch", hide_index=True)

elif pagina == "Día Anterior":
    st.subheader("Día Anterior")
    st.info("Fase siguiente: cálculo de día anterior y detalle de registros por tienda.")

elif pagina == "Reporte Semanal":
    st.subheader("Reporte Semanal")
    st.info("Fase siguiente: reporte semanal por tienda.")

elif pagina == "Reporte Mensual":
    st.subheader("Reporte Mensual")
    st.info("Fase siguiente: reporte mensual por tienda.")

elif pagina == "Conversión":
    st.subheader("Conversión Semanal Dev → Venta")
    st.info("Fase siguiente: conversión misma semana ISO por tienda, ID/modelo, color y talla.")

elif pagina == "Recuperación Económica":
    st.subheader("Recuperación Económica")
    st.info("Fase siguiente: recuperación económica y pendiente por convertir.")

elif pagina == "Configuración":
    st.subheader("Configuración")
    if not is_admin:
        st.warning("Sólo administrador puede modificar configuración.")
    else:
        st.success("Panel de configuración listo para la siguiente fase.")

st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
