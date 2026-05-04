# -*- coding: utf-8 -*-
"""
Dashboard Académico - Revisión Sistemática: Empleo Juvenil
Optimizado para presentación con proyector (cañón multimedia).
Ejecutar con: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Revisión Sistemática — Empleo Juvenil",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ESTILOS CSS - DISEÑO PROFESIONAL Y CLARO
# ============================================================
st.markdown("""
<style>
/* Tipografía clara y legible */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
    color: #333333;
    background-color: #FFFFFF;
}

/* Centrar título principal */
.main-title {
    text-align: center;
    color: #1F4E79;
    font-weight: 700;
    font-size: 2.5rem;
    margin-bottom: 0px;
    padding-bottom: 0px;
}
.sub-title {
    text-align: center;
    color: #555555;
    font-weight: 400;
    font-size: 1.2rem;
    margin-top: 5px;
    margin-bottom: 30px;
}

/* Encabezados de sección */
h1, h2, h3 {
    color: #1F4E79 !important;
}

/* Métricas */
div[data-testid="stMetric"] {
    background-color: #F8F9FA;
    border-left: 5px solid #1F4E79;
    padding: 15px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
div[data-testid="stMetric"] label {
    color: #555555 !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #1F4E79 !important;
    font-weight: 700 !important;
}

/* Dataframe header */
th {
    background-color: #1F4E79 !important;
    color: white !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    color: #1F4E79 !important;
    background-color: #F0F4F8 !important;
    border-radius: 5px !important;
}

/* Separador */
hr {
    border: 0;
    height: 1px;
    background: #DDDDDD;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS ROBUSTA
# ============================================================
@st.cache_data
def load_data():
    csv_path = "all_articles_scored.csv"
    if not os.path.exists(csv_path):
        st.error(f"❌ Archivo no encontrado: {csv_path}. Verifica que el script de scoring se ejecutó.")
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    return df

df = load_data()

if df.empty:
    st.stop()

top40 = df.head(40).copy()

# ============================================================
# TÍTULO Y ENCABEZADO
# ============================================================
st.markdown('<div class="main-title">📚 Revisión Sistemática: Empleo Juvenil</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Factores asociados al empleo juvenil en Arequipa: un análisis econométrico, 2020–2025</div>', unsafe_allow_html=True)

# ============================================================
# INDICADORES CLAVE
# ============================================================
st.markdown("### 📊 Indicadores Clave")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Artículos", len(top40))
with col2:
    st.metric("Score Promedio", f"{top40['total_score'].mean():.3f}")
with col3:
    st.metric("Total Citaciones", int(top40["Cited by"].sum()))
with col4:
    rango_anios = f"{int(top40['Year'].min())} – {int(top40['Year'].max())}"
    st.metric("Rango de Años", rango_anios)

st.markdown("---")

# ============================================================
# VISUALIZACIONES PRINCIPALES
# ============================================================
COLOR_INSTITUCIONAL = "#1F4E79"

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("### 📅 Distribución Temporal")
    year_data = top40["Year"].value_counts().reset_index()
    year_data.columns = ["Año", "Frecuencia"]
    year_data = year_data.sort_values("Año")
    
    fig_year = px.bar(
        year_data, x="Año", y="Frecuencia", 
        text="Frecuencia",
        color_discrete_sequence=[COLOR_INSTITUCIONAL]
    )
    fig_year.update_traces(textposition='outside')
    fig_year.update_layout(
        plot_bgcolor="white",
        xaxis=dict(dtick=1, showgrid=False, title="Año de Publicación"),
        yaxis=dict(showgrid=True, gridcolor="#E0E0E0", title="Cantidad de Artículos"),
        margin=dict(l=20, r=20, t=30, b=20),
        height=350
    )
    st.plotly_chart(fig_year, use_container_width=True)

with col_graf2:
    st.markdown("### 🔬 Metodologías Predominantes")
    meth_counts = {}
    for m in top40["metodologia"].dropna():
        for item in str(m).split("; "):
            item = item.strip()
            if item and item != "No clasificado":
                meth_counts[item] = meth_counts.get(item, 0) + 1
                
    meth_df = pd.DataFrame(sorted(meth_counts.items(), key=lambda x: -x[1]), columns=["Metodología", "Frecuencia"])
    
    fig_meth = px.bar(
        meth_df.head(6), x="Frecuencia", y="Metodología", 
        orientation='h', text="Frecuencia",
        color_discrete_sequence=[COLOR_INSTITUCIONAL]
    )
    fig_meth.update_traces(textposition='outside')
    fig_meth.update_layout(
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#E0E0E0", title="Cantidad de Artículos"),
        yaxis=dict(showgrid=False, title="", autorange="reversed"),
        margin=dict(l=20, r=20, t=30, b=20),
        height=350
    )
    st.plotly_chart(fig_meth, use_container_width=True)

st.markdown("---")

# ============================================================
# TABLA DE RESULTADOS
# ============================================================
st.markdown("### 🏆 Top 40 Artículos Seleccionados")

# Preparar tabla limpia
display_cols = ["ranking", "Title", "Year", "Cited by", "total_score", "metodologia"]
display_names = {
    "ranking": "Rank",
    "Title": "Título del Artículo",
    "Year": "Año",
    "Cited by": "Citas",
    "total_score": "Score",
    "metodologia": "Metodología"
}

df_display = top40[display_cols].rename(columns=display_names).copy()

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    height=300,
    column_config={
        "Rank": st.column_config.NumberColumn(width="small"),
        "Título del Artículo": st.column_config.TextColumn(width="large"),
        "Año": st.column_config.NumberColumn(width="small", format="%d"),
        "Citas": st.column_config.NumberColumn(width="small"),
        "Score": st.column_config.NumberColumn(width="small", format="%.3f"),
        "Metodología": st.column_config.TextColumn(width="medium")
    }
)

st.markdown("---")

# ============================================================
# DETALLE DE ARTÍCULOS (EXPANDERS)
# ============================================================
st.markdown("### 🔍 Detalle de Artículos")
st.caption("Haz clic en cada artículo para ver información resumida sobre objetivos, metodologías y hallazgos.")

for idx, row in top40.iterrows():
    rank = int(row.get("ranking", 0))
    year = int(row.get("Year", 0))
    title = str(row.get("Title", "Sin título"))
    citas = int(row.get("Cited by", 0))
    score = float(row.get("total_score", 0.0))
    
    expander_title = f"#{rank} | {year} | {title[:90]}..." if len(title) > 90 else f"#{rank} | {year} | {title}"
    
    with st.expander(expander_title):
        st.markdown(f"**Score:** `{score:.3f}` | **Citas:** `{citas}`")
        
        obj = str(row.get("objetivo", "No especificado"))
        met = str(row.get("metodologia", "No especificado"))
        hal = str(row.get("hallazgos", "No especificado"))
        tem = str(row.get("resultados", "No especificado"))
        
        st.markdown(f"**🎯 Objetivo:**")
        st.info(obj)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🔬 Metodología:** {met}")
        with c2:
            st.markdown(f"**📋 Tema Principal:** {tem}")
            
        st.markdown(f"**💡 Hallazgos Principales:**")
        st.success(hal)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#555555; font-size:0.9rem; padding:10px 0;'>"
    "<b>Proyecto de Tesis I</b> | Yomax Ccallocondo Machacca<br>"
    "Desarrollado en Python & Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
