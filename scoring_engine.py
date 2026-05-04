# -*- coding: utf-8 -*-
"""
Sistema de Puntuación Multicriterio para Revisión Sistemática
Tema: Factores asociados al empleo juvenil en Arequipa (2020-2025)
"""

import pandas as pd
import numpy as np
import re
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================

INPUT_FILE = "scopus_export_Apr 21-2026_0d932880-ff0c-4d40-a139-8978ed4e0578.xlsx"
OUTPUT_EXCEL = "top40_articulos_relevancia_empleo_juvenil.xlsx"
OUTPUT_CSV_FULL = "all_articles_scored.csv"
TOP_N = 40

# Ponderaciones aprobadas por el usuario
WEIGHT_THEMATIC = 0.50
WEIGHT_RECENCY = 0.20
WEIGHT_CITATIONS = 0.20
WEIGHT_METHODOLOGY = 0.10

# Términos de búsqueda con pesos (inglés y español)
SEARCH_TERMS = {
    # Peso alto (3) - Términos centrales
    "youth employment": 3, "empleo juvenil": 3,
    "youth unemployment": 3, "desempleo juvenil": 3,
    "neet": 3, "nini": 3,
    # Peso medio (2) - Términos contextuales
    "labor market": 2, "mercado laboral": 2, "mercado de trabajo": 2,
    "labour market": 2,
    "determinants": 2, "determinantes": 2,
    "school-to-work transition": 2, "transición escuela-trabajo": 2,
    "transicion escuela-trabajo": 2,
    "employment": 2, "empleo": 2,
    "young workers": 2, "trabajadores jóvenes": 2,
    "juventud": 2, "youth": 2,
    # Peso bajo (1) - Términos metodológicos
    "econometrics": 1, "econometría": 1, "econometria": 1,
    "logit": 1, "probit": 1,
    "panel data": 1, "datos de panel": 1,
    "regression": 1, "regresión": 1, "regresion": 1,
}

# Score de actualidad por año
RECENCY_SCORES = {
    2026: 1.0, 2025: 1.0,
    2024: 0.8, 2023: 0.6,
    2022: 0.4, 2021: 0.2, 2020: 0.1,
}

# Patrones de metodología
METHODOLOGY_PATTERNS = {
    "Econometría": [r"econometr", r"instrumental variable", r"variable instrumental",
                     r"two.stage", r"2sls", r"gmm", r"ols", r"regression analysis"],
    "Logit/Probit": [r"\blogit\b", r"\bprobit\b", r"logistic regression",
                      r"regresión logística", r"binary model", r"multinomial"],
    "Panel Data": [r"panel data", r"datos de panel", r"fixed effect", r"random effect",
                    r"efectos fijos", r"efectos aleatorios", r"longitudinal"],
    "Machine Learning": [r"machine learning", r"random forest", r"neural network",
                          r"deep learning", r"gradient boosting", r"aprendizaje automático"],
    "Revisión Sistemática": [r"systematic review", r"revisión sistemática", r"meta.analysis",
                              r"bibliometric", r"bibliométric", r"scoping review"],
    "Estudio Descriptivo": [r"descriptive", r"descriptivo", r"survey", r"encuesta",
                             r"cross.sectional", r"transversal"],
}

# Patrones de resultados de investigación
RESULTS_PATTERNS = {
    "Factores educativos": [r"educat", r"school", r"escol", r"training", r"capacitación",
                             r"skill", r"habilidad", r"human capital formation"],
    "Desigualdad de género": [r"gender", r"género", r"genero", r"women", r"mujer",
                               r"female", r"femenin", r"sex gap", r"brecha"],
    "Capital humano": [r"human capital", r"capital humano", r"experience", r"experiencia",
                        r"qualification", r"calificación"],
    "Mercado laboral": [r"labor market", r"mercado laboral", r"labour market",
                         r"informal", r"formal employment", r"wage", r"salario"],
    "Políticas públicas": [r"public polic", r"política pública", r"politica publica",
                            r"government", r"gobierno", r"subsid", r"incentiv", r"program"],
    "Transición escuela-trabajo": [r"school.to.work", r"transition", r"transición",
                                    r"first job", r"primer empleo", r"entry"],
}

# Patrones para extraer objetivos de investigación
OBJECTIVE_PATTERNS = [
    r"(?:this (?:study|paper|article|research|work) (?:aims?|seeks?|intends?|attempts?)(?: to)?[^.]*\.)",
    r"(?:the (?:aim|objective|purpose|goal) of (?:this|the present) (?:study|paper|article|research|work)[^.]*\.)",
    r"(?:(?:we|this paper) (?:examine|analyze|analyse|investigate|explore|assess|evaluate)[s]?[^.]*\.)",
    r"(?:the (?:main|primary|principal|general) (?:aim|objective|purpose|goal)[^.]*\.)",
    r"(?:(?:our|the) (?:objective|aim|purpose) (?:is|was) to[^.]*\.)",
    r"(?:this (?:study|paper) (?:contributes?|provides?|presents?|proposes?)[^.]*\.)",
    r"(?:el (?:objetivo|propósito|fin) de (?:este|la presente) (?:estudio|investigación|trabajo|artículo)[^.]*\.)",
    r"(?:(?:este|el presente) (?:estudio|trabajo|artículo) (?:busca|tiene como objetivo|analiza|examina|investiga)[^.]*\.)",
    r"(?:(?:se|este estudio) (?:analiza|examina|investiga|evalúa|estudia)[^.]*\.)",
]


# ============================================================
# FUNCIONES PRINCIPALES
# ============================================================

def load_data(filepath):
    """Cargar y preparar los datos del archivo Excel."""
    df = pd.read_excel(filepath)
    df["Author Keywords"] = df["Author Keywords"].fillna("")
    df["Abstract"] = df["Abstract"].fillna("")
    df["Title"] = df["Title"].fillna("")
    df["Cited by"] = pd.to_numeric(df["Cited by"], errors="coerce").fillna(0).astype(int)
    # Campo combinado para búsqueda
    df["combined_text"] = (
        df["Title"].str.lower() + " " +
        df["Abstract"].str.lower() + " " +
        df["Author Keywords"].str.lower()
    )
    print(f"✓ Datos cargados: {len(df)} artículos")
    return df


def calc_thematic_score(text):
    """Calcular score temático basado en coincidencia de términos ponderados."""
    score = 0
    max_possible = sum(SEARCH_TERMS.values())
    for term, weight in SEARCH_TERMS.items():
        if term.lower() in text:
            score += weight
    return min(score / max_possible, 1.0)


def calc_recency_score(year):
    """Calcular score de actualidad."""
    return RECENCY_SCORES.get(year, 0.0)


def calc_citation_score(cited_by, max_cited):
    """Calcular score de citaciones con normalización logarítmica."""
    if max_cited == 0:
        return 0.0
    return np.log1p(cited_by) / np.log1p(max_cited)


def classify_text(text, patterns_dict):
    """Clasificar texto según patrones regex. Devuelve lista de categorías."""
    categories = []
    for category, patterns in patterns_dict.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                categories.append(category)
                break
    return categories


def calc_methodology_score(methodologies):
    """Score de ajuste metodológico: premia artículos con métodos cuantitativos relevantes."""
    high_value = {"Econometría", "Logit/Probit", "Panel Data"}
    medium_value = {"Machine Learning", "Revisión Sistemática"}
    score = 0.0
    for m in methodologies:
        if m in high_value:
            score += 0.4
        elif m in medium_value:
            score += 0.2
        else:
            score += 0.1
    return min(score, 1.0)


def extract_objective(abstract):
    """Extraer el objetivo de investigación del abstract."""
    if not abstract or pd.isna(abstract):
        return "No identificado"
    for pattern in OBJECTIVE_PATTERNS:
        match = re.search(pattern, abstract, re.IGNORECASE)
        if match:
            obj = match.group(0).strip()
            # Limpiar y limitar longitud
            obj = obj[0].upper() + obj[1:] if obj else obj
            if len(obj) > 400:
                obj = obj[:397] + "..."
            return obj
    # Fallback: usar las primeras 2 oraciones del abstract
    sentences = re.split(r'(?<=[.!?])\s+', abstract.strip())
    fallback = " ".join(sentences[:2])
    if len(fallback) > 400:
        fallback = fallback[:397] + "..."
    return fallback if fallback else "No identificado"


def extract_key_findings(abstract):
    """Extraer hallazgos principales del abstract."""
    if not abstract or pd.isna(abstract):
        return "No identificado"
    finding_patterns = [
        r"(?:(?:the |our )?results? (?:show|indicate|suggest|reveal|demonstrate|confirm)[s]?[^.]*\.)",
        r"(?:(?:we |the authors? )?(?:find|found|conclude|show) that[^.]*\.)",
        r"(?:(?:the )?findings? (?:show|indicate|suggest|reveal)[s]?[^.]*\.)",
        r"(?:(?:los |nuestros )?resultados (?:muestran|indican|sugieren|revelan)[^.]*\.)",
        r"(?:(?:se |los autores )?(?:encuentra|concluye|demuestra) que[^.]*\.)",
    ]
    findings = []
    for pattern in finding_patterns:
        matches = re.findall(pattern, abstract, re.IGNORECASE)
        findings.extend(matches)
    if findings:
        result = " ".join(findings[:2])
        if len(result) > 500:
            result = result[:497] + "..."
        return result
    # Fallback: últimas 2 oraciones
    sentences = re.split(r'(?<=[.!?])\s+', abstract.strip())
    if len(sentences) >= 2:
        fallback = " ".join(sentences[-2:])
    else:
        fallback = sentences[-1] if sentences else "No identificado"
    if len(fallback) > 500:
        fallback = fallback[:497] + "..."
    return fallback


def process_articles(df):
    """Procesar todos los artículos y calcular scores."""
    max_cited = df["Cited by"].max()

    # Scores individuales
    df["score_tematico"] = df["combined_text"].apply(calc_thematic_score)
    df["score_actualidad"] = df["Year"].apply(calc_recency_score)
    df["score_citaciones"] = df["Cited by"].apply(lambda x: calc_citation_score(x, max_cited))

    # Clasificaciones
    df["metodologia_list"] = df["combined_text"].apply(lambda t: classify_text(t, METHODOLOGY_PATTERNS))
    df["resultados_list"] = df["combined_text"].apply(lambda t: classify_text(t, RESULTS_PATTERNS))

    # Score metodológico
    df["score_metodologico"] = df["metodologia_list"].apply(calc_methodology_score)

    # Score total ponderado
    df["total_score"] = (
        WEIGHT_THEMATIC * df["score_tematico"] +
        WEIGHT_RECENCY * df["score_actualidad"] +
        WEIGHT_CITATIONS * df["score_citaciones"] +
        WEIGHT_METHODOLOGY * df["score_metodologico"]
    )

    # Convertir listas a strings para Excel
    df["metodologia"] = df["metodologia_list"].apply(lambda x: "; ".join(x) if x else "No clasificado")
    df["resultados"] = df["resultados_list"].apply(lambda x: "; ".join(x) if x else "No clasificado")

    # Extraer objetivos y hallazgos
    df["objetivo"] = df["Abstract"].apply(extract_objective)
    df["hallazgos"] = df["Abstract"].apply(extract_key_findings)

    # Ordenar por score total descendente
    df = df.sort_values("total_score", ascending=False).reset_index(drop=True)
    df["ranking"] = range(1, len(df) + 1)

    print(f"✓ Scores calculados para {len(df)} artículos")
    print(f"  Score total - min: {df['total_score'].min():.4f}, max: {df['total_score'].max():.4f}, "
          f"mean: {df['total_score'].mean():.4f}")
    return df


def create_methodology_summary():
    """Crear tabla con el resumen metodológico del sistema de puntuación."""
    data = [
        ["Coincidencia temática", "50%",
         "Σ(peso_i × match_i) / max_posible",
         "Busca términos clave en Title+Abstract+Keywords (EN/ES). "
         "Peso alto (3): youth employment, NEET. "
         "Peso medio (2): labor market, determinants. "
         "Peso bajo (1): econometrics, logit, probit."],
        ["Actualidad", "20%",
         "Mapeo por año: 2025-2026→1.0, 2024→0.8, ..., 2020→0.1",
         "Premia artículos más recientes para garantizar vigencia del marco teórico."],
        ["Impacto académico", "20%",
         "log(1 + cited_by) / log(1 + max_cited_by)",
         "Normalización logarítmica de citaciones para suavizar outliers "
         "y evitar sesgo hacia artículos de alto impacto."],
        ["Ajuste metodológico", "10%",
         "Σ puntos por método detectado (máx 1.0)",
         "Premia artículos con métodos cuantitativos relevantes: "
         "Econometría/Logit/Probit (+0.4), ML/Rev.Sist. (+0.2), Descriptivo (+0.1)."],
    ]
    return pd.DataFrame(data, columns=["Criterio", "Peso", "Fórmula", "Justificación"])


def export_results(df, output_excel):
    """Exportar resultados a Excel con múltiples hojas."""
    top = df.head(TOP_N).copy()

    # Columnas para el Excel principal
    export_cols = [
        "ranking", "Title", "Authors", "Year", "Source title",
        "Cited by", "DOI", "Abstract", "Author Keywords",
        "objetivo", "metodologia", "hallazgos",
        "score_tematico", "score_actualidad", "score_citaciones",
        "score_metodologico", "total_score",
        "resultados", "Language of Original Document", "Document Type"
    ]

    col_names = {
        "ranking": "Ranking",
        "score_tematico": "Score Temático",
        "score_actualidad": "Score Actualidad",
        "score_citaciones": "Score Citaciones",
        "score_metodologico": "Score Metodológico",
        "total_score": "Score Total",
        "metodologia": "Metodología",
        "resultados": "Temas de Investigación",
        "objetivo": "Objetivo de Investigación",
        "hallazgos": "Hallazgos Principales",
    }

    top_export = top[export_cols].rename(columns=col_names)

    # Distribución temporal
    dist_year = top.groupby("Year").agg(
        Artículos=("Year", "count"),
        Score_Promedio=("total_score", "mean"),
        Citaciones_Promedio=("Cited by", "mean")
    ).reset_index()

    # Frecuencia de metodologías
    meth_counts = {}
    for methods in top["metodologia_list"]:
        for m in methods:
            meth_counts[m] = meth_counts.get(m, 0) + 1
    dist_meth = pd.DataFrame(
        sorted(meth_counts.items(), key=lambda x: -x[1]),
        columns=["Metodología", "Frecuencia"]
    )

    # Frecuencia de resultados
    res_counts = {}
    for results in top["resultados_list"]:
        for r in results:
            res_counts[r] = res_counts.get(r, 0) + 1
    dist_res = pd.DataFrame(
        sorted(res_counts.items(), key=lambda x: -x[1]),
        columns=["Tema de Investigación", "Frecuencia"]
    )

    # Resumen metodológico
    summary = create_methodology_summary()

    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        top_export.to_excel(writer, sheet_name="Top 40 Artículos", index=False)
        summary.to_excel(writer, sheet_name="Resumen Metodológico", index=False)
        dist_year.to_excel(writer, sheet_name="Distribución Temporal", index=False)
        dist_meth.to_excel(writer, sheet_name="Metodologías", index=False)
        dist_res.to_excel(writer, sheet_name="Temas Investigación", index=False)

        # Formatear anchos de columna
        workbook = writer.book
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column("A:A", 8)
            if sheet_name == "Top 40 Artículos":
                worksheet.set_column("B:B", 60)  # Title
                worksheet.set_column("C:C", 30)  # Authors
                worksheet.set_column("H:H", 80)  # Abstract
                worksheet.set_column("J:J", 60)  # Objetivo
                worksheet.set_column("L:L", 60)  # Hallazgos

    print(f"✓ Excel exportado: {output_excel}")
    print(f"  Hojas: Top 40 Artículos, Resumen Metodológico, "
          f"Distribución Temporal, Metodologías, Temas Investigación")


def print_summary(df):
    """Imprimir resumen en consola."""
    top = df.head(TOP_N)
    print("\n" + "=" * 80)
    print(f"  TOP {TOP_N} ARTÍCULOS - RESUMEN")
    print("=" * 80)
    print(f"\n{'Rank':<6}{'Score':<8}{'Year':<6}{'Citas':<7}{'Título':<60}")
    print("-" * 87)
    for _, row in top.head(15).iterrows():
        title = row["Title"][:57] + "..." if len(str(row["Title"])) > 57 else row["Title"]
        print(f"{row['ranking']:<6}{row['total_score']:<8.4f}{row['Year']:<6}"
              f"{row['Cited by']:<7}{title}")

    print(f"\n... y {TOP_N - 15} artículos más.")

    print(f"\n📊 Distribución por año (Top {TOP_N}):")
    for year, count in top["Year"].value_counts().sort_index().items():
        print(f"  {year}: {'█' * count} ({count})")

    print(f"\n🔬 Metodologías detectadas (Top {TOP_N}):")
    meth_counts = {}
    for methods in top["metodologia_list"]:
        for m in methods:
            meth_counts[m] = meth_counts.get(m, 0) + 1
    for m, c in sorted(meth_counts.items(), key=lambda x: -x[1]):
        print(f"  {m}: {c}")


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  SISTEMA DE PUNTUACIÓN MULTICRITERIO")
    print("  Revisión Sistemática: Empleo Juvenil en Arequipa")
    print("=" * 80)
    print(f"\nPonderaciones: Temático={WEIGHT_THEMATIC:.0%}, "
          f"Actualidad={WEIGHT_RECENCY:.0%}, "
          f"Citaciones={WEIGHT_CITATIONS:.0%}, "
          f"Metodológico={WEIGHT_METHODOLOGY:.0%}\n")

    # 1. Cargar datos
    df = load_data(INPUT_FILE)

    # 2. Procesar y calcular scores
    df = process_articles(df)

    # 3. Exportar resultados
    export_results(df, OUTPUT_EXCEL)

    # 4. Exportar CSV completo
    csv_cols = ["ranking", "ID", "Title", "Year", "Cited by", "DOI",
                "score_tematico", "score_actualidad", "score_citaciones",
                "score_metodologico", "total_score",
                "metodologia", "resultados", "objetivo", "hallazgos"]
    df[csv_cols].to_csv(OUTPUT_CSV_FULL, index=False, encoding="utf-8-sig")
    print(f"✓ CSV completo exportado: {OUTPUT_CSV_FULL}")

    # 5. Resumen
    print_summary(df)

    print(f"\n✅ Proceso completado. Ejecuta el dashboard con:")
    print(f"   streamlit run dashboard.py")
