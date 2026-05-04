# -*- coding: utf-8 -*-
"""
Dashboard Interactivo - Revisión Sistemática: Empleo Juvenil
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
# ESTILOS CSS PERSONALIZADOS
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141432 0%, #1e1e4a 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown label,
section[data-testid="stSidebar"] .stMarkdown span {
    color: #c8c8e0 !important;
}

/* Headers */
h1 { 
    background: linear-gradient(90deg, #7c5cfc, #00d4ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
}
h2 { color: #b8b8e8 !important; font-weight: 700 !important; }
h3 { color: #9a9ad0 !important; font-weight: 600 !important; }

/* Metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(124,92,252,0.15), rgba(0,212,255,0.08));
    border: 1px solid rgba(124,92,252,0.25);
    border-radius: 16px;
    padding: 20px 24px;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(124,92,252,0.2);
}
div[data-testid="stMetric"] label {
    color: #8888bb !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #8888bb;
    font-weight: 500;
    padding: 10px 20px;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #7c5cfc, #5a3fd4) !important;
    color: white !important;
    font-weight: 600;
}

/* Dataframe */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(124,92,252,0.08) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(124,92,252,0.15) !important;
    color: #c8c8e8 !important;
    font-weight: 500 !important;
}

/* Download button */
.stDownloadButton button {
    background: linear-gradient(135deg, #7c5cfc, #5a3fd4) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton button:hover {
    background: linear-gradient(135deg, #8d6ffd, #6b4fe5) !important;
    box-shadow: 0 4px 20px rgba(124,92,252,0.4) !important;
    transform: translateY(-1px) !important;
}

/* Slider */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #7c5cfc !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# CARGAR DATOS
# ============================================================

@st.cache_data
def load_data():
    """Cargar datos procesados."""
    csv_path = "all_articles_scored.csv"
    excel_path = "top40_articulos_relevancia_empleo_juvenil.xlsx"
    
    if os.path.exists(csv_path):
        df_all = pd.read_csv(csv_path, encoding="utf-8-sig")
    else:
        st.error(f"❌ Archivo no encontrado: `{csv_path}`. Ejecuta primero `python scoring_engine.py`.")
        st.stop()
    
    # Cargar Excel original para datos completos
    input_file = "scopus_export_Apr 21-2026_0d932880-ff0c-4d40-a139-8978ed4e0578.xlsx"
    if os.path.exists(input_file):
        df_orig = pd.read_excel(input_file)
        df_orig["Author Keywords"] = df_orig["Author Keywords"].fillna("")
        # Merge para tener todas las columnas
        df_merged = df_all.merge(
            df_orig[["ID", "Title", "Authors", "Source title", "Abstract",
                      "Author Keywords", "DOI", "Language of Original Document",
                      "Document Type"]],
            on="ID", how="left", suffixes=("", "_orig")
        )
        # Usar columnas del original si faltan
        for col in ["Title", "Authors", "Source title", "Abstract", "Author Keywords", "DOI"]:
            if col not in df_merged.columns and f"{col}_orig" in df_merged.columns:
                df_merged[col] = df_merged[f"{col}_orig"]
        return df_merged
    
    return df_all


df = load_data()
top40 = df.head(40).copy()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎛️ Filtros")
    st.markdown("---")
    
    # Filtro de años
    years = sorted(top40["Year"].unique())
    year_range = st.slider(
        "📅 Rango de años",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years))),
    )
    
    # Filtro de citaciones
    max_cit = int(top40["Cited by"].max())
    cit_range = st.slider(
        "📊 Rango de citaciones",
        min_value=0,
        max_value=max_cit,
        value=(0, max_cit),
    )
    
    # Filtro de score mínimo
    min_score = st.slider(
        "⭐ Score mínimo",
        min_value=0.0,
        max_value=float(top40["total_score"].max()),
        value=0.0,
        step=0.01,
        format="%.2f",
    )
    
    st.markdown("---")
    
    # Filtro de metodología
    all_methods = set()
    if "metodologia" in top40.columns:
        for m in top40["metodologia"].dropna():
            for item in str(m).split("; "):
                if item.strip() and item.strip() != "No clasificado":
                    all_methods.add(item.strip())
    
    if all_methods:
        selected_methods = st.multiselect(
            "🔬 Metodología",
            sorted(all_methods),
            default=[],
        )
    else:
        selected_methods = []
    
    st.markdown("---")
    st.markdown("### 📋 Acerca de")
    st.markdown(
        "Sistema de puntuación multicriterio para "
        "revisión sistemática sobre **empleo juvenil**. "
        "Ponderaciones: Temático 50%, Actualidad 20%, "
        "Citaciones 20%, Metodológico 10%."
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

filtered = top40[
    (top40["Year"] >= year_range[0]) &
    (top40["Year"] <= year_range[1]) &
    (top40["Cited by"] >= cit_range[0]) &
    (top40["Cited by"] <= cit_range[1]) &
    (top40["total_score"] >= min_score)
].copy()

if selected_methods:
    mask = filtered["metodologia"].apply(
        lambda x: any(m in str(x) for m in selected_methods)
    )
    filtered = filtered[mask]


# ============================================================
# HEADER
# ============================================================

st.markdown("# 📚 Revisión Sistemática: Empleo Juvenil")
st.markdown("##### Factores asociados al empleo juvenil en Arequipa — Análisis econométrico 2020-2025")

st.markdown("")

# Métricas clave
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Artículos filtrados", len(filtered))
with col2:
    st.metric("Score promedio", f"{filtered['total_score'].mean():.3f}" if len(filtered) > 0 else "—")
with col3:
    st.metric("Citaciones totales", int(filtered["Cited by"].sum()) if len(filtered) > 0 else 0)
with col4:
    st.metric("Años cubiertos",
              f"{int(filtered['Year'].min())}–{int(filtered['Year'].max())}" if len(filtered) > 0 else "—")

st.markdown("")


# ============================================================
# PESTAÑAS PRINCIPALES
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ranking Top 40",
    "📊 Distribución Temporal",
    "🔬 Metodologías",
    "📋 Temas de Investigación",
    "🔍 Detalle de Artículos",
])

# Paleta de colores
COLOR_PRIMARY = "#7c5cfc"
COLOR_SECONDARY = "#00d4ff"
COLOR_ACCENT = "#ff6b9d"
COLOR_BG = "rgba(0,0,0,0)"
PLOTLY_TEMPLATE = "plotly_dark"
GRADIENT_COLORS = ["#7c5cfc", "#6366f1", "#818cf8", "#00d4ff", "#22d3ee"]


# --- TAB 1: RANKING ---
with tab1:
    st.markdown("### 🏆 Artículos mejor puntuados")
    
    if len(filtered) > 0:
        display_cols = ["ranking", "Title", "Year", "Cited by", "total_score",
                        "metodologia", "resultados"]
        display_names = {
            "ranking": "Rank",
            "total_score": "Score",
            "metodologia": "Metodología",
            "resultados": "Temas",
            "Cited by": "Citas",
        }
        
        display_df = filtered[display_cols].rename(columns=display_names)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            column_config={
                "Rank": st.column_config.NumberColumn(width="small"),
                "Title": st.column_config.TextColumn(width="large"),
                "Year": st.column_config.NumberColumn(width="small", format="%d"),
                "Citas": st.column_config.NumberColumn(width="small"),
                "Score": st.column_config.ProgressColumn(
                    width="medium",
                    min_value=0,
                    max_value=float(top40["total_score"].max()),
                    format="%.3f",
                ),
                "Metodología": st.column_config.TextColumn(width="medium"),
                "Temas": st.column_config.TextColumn(width="medium"),
            },
            hide_index=True,
        )
        
        # Gráfico de barras horizontales de scores
        top15 = filtered.head(15)
        fig_rank = go.Figure()
        fig_rank.add_trace(go.Bar(
            y=top15["Title"].apply(lambda t: t[:50] + "..." if len(str(t)) > 50 else t),
            x=top15["total_score"],
            orientation="h",
            marker=dict(
                color=top15["total_score"],
                colorscale=[[0, "#24243e"], [0.5, "#7c5cfc"], [1, "#00d4ff"]],
                line=dict(width=0),
                cornerradius=4,
            ),
            text=top15["total_score"].apply(lambda x: f"{x:.3f}"),
            textposition="outside",
            textfont=dict(color="#c8c8e0", size=11),
            hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>",
        ))
        fig_rank.update_layout(
            title=dict(text="Top 15 — Score Total", font=dict(color="#b8b8e8", size=16)),
            template=PLOTLY_TEMPLATE,
            paper_bgcolor=COLOR_BG,
            plot_bgcolor=COLOR_BG,
            height=500,
            yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#9a9ad0")),
            xaxis=dict(title="Score Total", gridcolor="rgba(255,255,255,0.04)",
                       tickfont=dict(color="#8888bb")),
            margin=dict(l=20, r=60, t=50, b=40),
        )
        st.plotly_chart(fig_rank, use_container_width=True)
        
        # Botón de descarga
        excel_path = "top40_articulos_relevancia_empleo_juvenil.xlsx"
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.download_button(
                    "⬇️ Descargar Excel completo",
                    data=f,
                    file_name=excel_path,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    else:
        st.warning("⚠️ No hay artículos que coincidan con los filtros seleccionados.")


# --- TAB 2: DISTRIBUCIÓN TEMPORAL ---
with tab2:
    st.markdown("### 📊 Distribución temporal de artículos")
    
    if len(filtered) > 0:
        year_data = filtered.groupby("Year").agg(
            count=("Year", "count"),
            avg_score=("total_score", "mean"),
            avg_cit=("Cited by", "mean"),
        ).reset_index()
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            fig_year = go.Figure()
            fig_year.add_trace(go.Bar(
                x=year_data["Year"],
                y=year_data["count"],
                marker=dict(
                    color=year_data["count"],
                    colorscale=[[0, "#3b3b7a"], [1, "#7c5cfc"]],
                    cornerradius=6,
                    line=dict(width=0),
                ),
                text=year_data["count"],
                textposition="outside",
                textfont=dict(color="#c8c8e0", size=13, family="Inter"),
                hovertemplate="Año: %{x}<br>Artículos: %{y}<extra></extra>",
            ))
            fig_year.update_layout(
                title=dict(text="Artículos por año", font=dict(color="#b8b8e8", size=15)),
                template=PLOTLY_TEMPLATE,
                paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG,
                height=400,
                xaxis=dict(dtick=1, tickfont=dict(color="#8888bb")),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(color="#8888bb")),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_year, use_container_width=True)
        
        with col_b:
            fig_score_year = go.Figure()
            fig_score_year.add_trace(go.Scatter(
                x=year_data["Year"],
                y=year_data["avg_score"],
                mode="lines+markers",
                line=dict(color=COLOR_PRIMARY, width=3),
                marker=dict(size=10, color=COLOR_SECONDARY, line=dict(color=COLOR_PRIMARY, width=2)),
                hovertemplate="Año: %{x}<br>Score promedio: %{y:.3f}<extra></extra>",
                name="Score promedio",
            ))
            fig_score_year.update_layout(
                title=dict(text="Score promedio por año", font=dict(color="#b8b8e8", size=15)),
                template=PLOTLY_TEMPLATE,
                paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG,
                height=400,
                xaxis=dict(dtick=1, tickfont=dict(color="#8888bb")),
                yaxis=dict(title="Score", gridcolor="rgba(255,255,255,0.04)",
                           tickfont=dict(color="#8888bb")),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_score_year, use_container_width=True)


# --- TAB 3: METODOLOGÍAS ---
with tab3:
    st.markdown("### 🔬 Metodologías detectadas")
    
    if len(filtered) > 0:
        meth_counts = {}
        for m in filtered["metodologia"].dropna():
            for item in str(m).split("; "):
                item = item.strip()
                if item and item != "No clasificado":
                    meth_counts[item] = meth_counts.get(item, 0) + 1
        
        if meth_counts:
            meth_df = pd.DataFrame(
                sorted(meth_counts.items(), key=lambda x: -x[1]),
                columns=["Metodología", "Frecuencia"]
            )
            
            fig_meth = go.Figure()
            fig_meth.add_trace(go.Bar(
                y=meth_df["Metodología"],
                x=meth_df["Frecuencia"],
                orientation="h",
                marker=dict(
                    color=meth_df["Frecuencia"],
                    colorscale=[[0, "#3b3b7a"], [0.5, "#6366f1"], [1, "#00d4ff"]],
                    cornerradius=6,
                    line=dict(width=0),
                ),
                text=meth_df["Frecuencia"],
                textposition="outside",
                textfont=dict(color="#c8c8e0", size=13),
                hovertemplate="<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>",
            ))
            fig_meth.update_layout(
                title=dict(text="Frecuencia de metodologías (Top 40)",
                           font=dict(color="#b8b8e8", size=16)),
                template=PLOTLY_TEMPLATE,
                paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG,
                height=400,
                yaxis=dict(autorange="reversed", tickfont=dict(size=12, color="#9a9ad0")),
                xaxis=dict(title="Nº de artículos", gridcolor="rgba(255,255,255,0.04)",
                           tickfont=dict(color="#8888bb")),
                margin=dict(l=20, r=60, t=50, b=40),
            )
            st.plotly_chart(fig_meth, use_container_width=True)
            
            # Tabla de metodologías
            st.dataframe(meth_df, use_container_width=True, hide_index=True)
        else:
            st.info("No se detectaron metodologías con los filtros actuales.")


# --- TAB 4: TEMAS DE INVESTIGACIÓN ---
with tab4:
    st.markdown("### 📋 Temas y resultados de investigación")
    
    if len(filtered) > 0:
        res_counts = {}
        for r in filtered["resultados"].dropna():
            for item in str(r).split("; "):
                item = item.strip()
                if item and item != "No clasificado":
                    res_counts[item] = res_counts.get(item, 0) + 1
        
        if res_counts:
            res_df = pd.DataFrame(
                sorted(res_counts.items(), key=lambda x: -x[1]),
                columns=["Tema", "Frecuencia"]
            )
            
            fig_res = go.Figure()
            fig_res.add_trace(go.Bar(
                y=res_df["Tema"],
                x=res_df["Frecuencia"],
                orientation="h",
                marker=dict(
                    color=res_df["Frecuencia"],
                    colorscale=[[0, "#3b2a5e"], [0.5, "#ff6b9d"], [1, "#ffb86c"]],
                    cornerradius=6,
                    line=dict(width=0),
                ),
                text=res_df["Frecuencia"],
                textposition="outside",
                textfont=dict(color="#c8c8e0", size=13),
                hovertemplate="<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>",
            ))
            fig_res.update_layout(
                title=dict(text="Temas de investigación (Top 40)",
                           font=dict(color="#b8b8e8", size=16)),
                template=PLOTLY_TEMPLATE,
                paper_bgcolor=COLOR_BG, plot_bgcolor=COLOR_BG,
                height=400,
                yaxis=dict(autorange="reversed", tickfont=dict(size=12, color="#9a9ad0")),
                xaxis=dict(title="Nº de artículos", gridcolor="rgba(255,255,255,0.04)",
                           tickfont=dict(color="#8888bb")),
                margin=dict(l=20, r=60, t=50, b=40),
            )
            st.plotly_chart(fig_res, use_container_width=True)
            
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.info("No se detectaron temas con los filtros actuales.")


# --- TAB 5: DETALLE DE ARTÍCULOS ---
with tab5:
    st.markdown("### 🔍 Resumen estructurado por artículo")
    st.markdown("Cada artículo muestra: **Objetivo**, **Metodología** y **Hallazgos principales**.")
    st.markdown("")
    
    if len(filtered) > 0:
        for idx, row in filtered.iterrows():
            rank = int(row.get("ranking", 0))
            title = str(row.get("Title", "Sin título"))
            year = int(row.get("Year", 0))
            cited = int(row.get("Cited by", 0))
            score = float(row.get("total_score", 0))
            
            with st.expander(f"**#{rank}** — {title} ({year}) — Score: {score:.3f}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**📅 Año:** {year}")
                with c2:
                    st.markdown(f"**📊 Citaciones:** {cited}")
                with c3:
                    st.markdown(f"**⭐ Score:** {score:.4f}")
                
                st.markdown("---")
                
                # Autores y fuente
                authors = row.get("Authors", "N/A")
                source = row.get("Source title", "N/A")
                st.markdown(f"**✍️ Autores:** {authors}")
                st.markdown(f"**📰 Fuente:** {source}")
                
                doi = row.get("DOI", "")
                if pd.notna(doi) and doi:
                    st.markdown(f"**🔗 DOI:** [{doi}](https://doi.org/{doi})")
                
                st.markdown("---")
                
                # Resumen estructurado
                objetivo = row.get("objetivo", "No identificado")
                metodologia = row.get("metodologia", "No clasificado")
                hallazgos = row.get("hallazgos", "No identificado")
                
                st.markdown("**🎯 Objetivo de investigación:**")
                st.markdown(f"> {objetivo}")
                
                st.markdown(f"**🔬 Metodología:** `{metodologia}`")
                
                st.markdown("**📌 Hallazgos principales:**")
                st.markdown(f"> {hallazgos}")
                
                # Keywords
                kw = row.get("Author Keywords", "")
                if pd.notna(kw) and str(kw).strip():
                    st.markdown(f"**🏷️ Keywords:** {kw}")
    else:
        st.warning("⚠️ No hay artículos que coincidan con los filtros.")


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#6a6a9a; font-size:0.85rem; padding:16px 0;'>"
    "Sistema de Puntuación Multicriterio — Revisión Sistemática: Empleo Juvenil en Arequipa<br>"
    "Ponderaciones: Temático 50% · Actualidad 20% · Citaciones 20% · Metodológico 10%"
    "</div>",
    unsafe_allow_html=True,
)
