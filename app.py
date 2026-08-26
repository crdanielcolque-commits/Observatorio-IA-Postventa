# ============================================================
# OBSERVATORIO IA POSTVENTA — AUTOLUX
# V0.1 — Google Sheets + Streamlit
# ============================================================

import pandas as pd
import numpy as np
import streamlit as st
from urllib.parse import quote

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Observatorio IA Postventa",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_ID = "19bG8rpc4OyInSSlydySRkB0d2kBV7ysiJu4fRDoTNGU"

SHEETS = {
    "noticias": "NOTICIAS",
    "roadmap": "ROADMAP",
    "fuentes": "FUENTES",
    "autolog": "AUTOLOG",
}

# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
        h1, h2, h3 {letter-spacing: -0.02em;}
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 16px;
            padding: 12px 14px;
        }
        .radar-card {
            border: 1px solid rgba(128,128,128,.20);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            background: rgba(255,255,255,.025);
        }
        .small-muted {opacity: .72; font-size: .92rem;}
        .score-pill {
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            font-weight:700;
            border:1px solid rgba(128,128,128,.25);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def sheet_csv_url(sheet_name: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )

@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(sheet_name: str) -> pd.DataFrame:
    url = sheet_csv_url(sheet_name)
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def safe_load(sheet_name: str) -> pd.DataFrame:
    try:
        return load_sheet(sheet_name)
    except Exception as e:
        st.warning(f"No pude leer la hoja «{sheet_name}». Detalle: {e}")
        return pd.DataFrame()

def clean_news(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    # Elimina filas sin ID
    if "ID" in df.columns:
        df = df[df["ID"].notna()]
        df["ID"] = df["ID"].astype(str).str.strip()
        df = df[df["ID"] != ""]

    # Fechas
    for c in ["Fecha Radar", "Fecha Publicación", "Fecha Objetivo"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

    # Numéricos
    numeric_cols = [
        "Impacto Económico (0-25)",
        "Experiencia Cliente (0-20)",
        "Aplicabilidad Autolux (0-20)",
        "Facilidad Implementación (0-15)",
        "Inversión (0-10)",
        "Alineación Estratégica (0-10)",
        "Score Autolux",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Si Google Sheets no exporta el resultado de ARRAYFORMULA por algún motivo,
    # lo reconstruimos con los 6 componentes.
    score_components = [
        "Impacto Económico (0-25)",
        "Experiencia Cliente (0-20)",
        "Aplicabilidad Autolux (0-20)",
        "Facilidad Implementación (0-15)",
        "Inversión (0-10)",
        "Alineación Estratégica (0-10)",
    ]
    if all(c in df.columns for c in score_components):
        calculated = df[score_components].sum(axis=1, min_count=1)
        if "Score Autolux" not in df.columns:
            df["Score Autolux"] = calculated
        else:
            df["Score Autolux"] = df["Score Autolux"].fillna(calculated)

    if "Prioridad" not in df.columns:
        df["Prioridad"] = np.nan

    if "Score Autolux" in df.columns:
        calc_priority = pd.cut(
            df["Score Autolux"],
            bins=[-np.inf, 49.999, 69.999, 84.999, np.inf],
            labels=["Baja", "Media", "Alta", "Crítica"],
        ).astype("object")
        df["Prioridad"] = df["Prioridad"].replace("", np.nan).fillna(calc_priority)

    return df

def fmt_date(v):
    if pd.isna(v):
        return "—"
    return pd.Timestamp(v).strftime("%d/%m/%Y")

def text(v, default="—"):
    if pd.isna(v) or str(v).strip() == "":
        return default
    return str(v).strip()

def priority_icon(p):
    return {
        "Crítica": "🔴",
        "Alta": "🟠",
        "Media": "🟡",
        "Baja": "🟢",
    }.get(text(p, ""), "⚪")

def metric_value(v, decimals=0):
    if pd.isna(v):
        return "—"
    if decimals == 0:
        return f"{v:,.0f}".replace(",", ".")
    return f"{v:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def detail_card(row):
    score = row.get("Score Autolux", np.nan)
    priority = text(row.get("Prioridad", ""))
    title = text(row.get("Título", "Sin título"))
    pub = fmt_date(row.get("Fecha Publicación"))
    category = text(row.get("Categoría", ""))
    region = text(row.get("Región / País", ""))
    source = text(row.get("Fuente", ""))
    url = text(row.get("URL", ""), "")

    st.markdown(
        f"""
        <div class="radar-card">
            <div class="small-muted">{priority_icon(priority)} {priority} · {category} · {region}</div>
            <h3 style="margin:.25rem 0 .45rem 0;">{title}</h3>
            <div class="small-muted">Publicación: {pub} · Fuente: {source}</div>
            <div style="margin-top:.7rem;">
                <span class="score-pill">Score Autolux: {metric_value(score)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Por qué importa**")
        st.write(text(row.get("Por qué importa")))
        st.markdown("**Aplicación Autolux**")
        st.write(text(row.get("Aplicación Autolux")))
    with c2:
        st.markdown("**Próxima acción**")
        st.write(text(row.get("Próxima Acción")))
        st.markdown("**Riesgos / limitaciones**")
        st.write(text(row.get("Riesgos / Limitaciones")))

    if url:
        st.link_button("Abrir fuente original", url)

# ------------------------------------------------------------
# CARGA
# ------------------------------------------------------------
news = clean_news(safe_load(SHEETS["noticias"]))
roadmap = safe_load(SHEETS["roadmap"])
fuentes = safe_load(SHEETS["fuentes"])
autolog = safe_load(SHEETS["autolog"])

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📡 Observatorio IA")
    st.caption("Postventa Autolux · MVP V0.1")
    st.divider()

    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Los datos se refrescan automáticamente cada 5 minutos o al presionar Actualizar.")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("📡 Observatorio IA Postventa")
st.caption("Inteligencia estratégica aplicada a Taller / Servicios, Repuestos y experiencia de cliente.")

if news.empty:
    st.error(
        "La hoja NOTICIAS está vacía o no pudo leerse. "
        "Verifica que el Google Sheet siga compartido como «Cualquier persona con el enlace → Lector»."
    )
    st.stop()

tabs = st.tabs([
    "🎯 Radar del Día",
    "🗂 Histórico",
    "📈 Tendencias",
    "⚡ Quick Wins",
    "🛣 Roadmap Autolux",
    "🏁 Benchmark",
    "🔎 Fuentes",
])

# ------------------------------------------------------------
# TAB 1 — RADAR DEL DÍA
# ------------------------------------------------------------
with tabs[0]:
    valid_dates = news["Fecha Radar"].dropna() if "Fecha Radar" in news.columns else pd.Series(dtype="datetime64[ns]")
    latest_date = valid_dates.max() if not valid_dates.empty else pd.NaT

    if pd.isna(latest_date):
        today_df = news.copy()
        label_date = "Sin fecha"
    else:
        today_df = news[news["Fecha Radar"] == latest_date].copy()
        label_date = fmt_date(latest_date)

    today_df = today_df.sort_values("Score Autolux", ascending=False, na_position="last")

    st.subheader(f"Radar IA Postventa — Edición Ejecutiva {label_date}")

    score_avg = today_df["Score Autolux"].mean() if "Score Autolux" in today_df.columns else np.nan
    critical = (today_df["Prioridad"] == "Crítica").sum() if "Prioridad" in today_df.columns else 0
    quick = (today_df["Quick Win"].astype(str).str.strip().str.lower() == "sí").sum() if "Quick Win" in today_df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Oportunidades detectadas", len(today_df))
    c2.metric("Score promedio", metric_value(score_avg, 1))
    c3.metric("Prioridad crítica", int(critical))
    c4.metric("Quick Wins", int(quick))

    if not today_df.empty:
        top = today_df.iloc[0]
        st.markdown("### 🔥 Oportunidad Nº 1 para Autolux")
        st.success(
            f"{text(top.get('Título'))} · Score {metric_value(top.get('Score Autolux'))} · "
            f"{text(top.get('Prioridad'))}"
        )

    st.markdown("### Novedades del radar")
    for _, row in today_df.iterrows():
        detail_card(row)
        st.divider()

# ------------------------------------------------------------
# TAB 2 — HISTÓRICO
# ------------------------------------------------------------
with tabs[1]:
    st.subheader("Histórico completo")

    f1, f2, f3, f4 = st.columns(4)

    categories = sorted(news["Categoría"].dropna().astype(str).unique()) if "Categoría" in news.columns else []
    priorities = ["Crítica", "Alta", "Media", "Baja"]
    regions = sorted(news["Región / País"].dropna().astype(str).unique()) if "Región / País" in news.columns else []
    types = sorted(news["Tipo Hallazgo"].dropna().astype(str).unique()) if "Tipo Hallazgo" in news.columns else []

    with f1:
        sel_cat = st.multiselect("Categoría", categories)
    with f2:
        sel_priority = st.multiselect("Prioridad", priorities)
    with f3:
        sel_region = st.multiselect("Región / País", regions)
    with f4:
        sel_type = st.multiselect("Tipo de hallazgo", types)

    f5, f6 = st.columns([2, 1])
    with f5:
        search = st.text_input("Buscar", placeholder="Ej.: Video MPI, eCommerce, IA, ADAS...")
    with f6:
        min_score = st.slider("Score mínimo", 0, 100, 0)

    hist = news.copy()
    if sel_cat:
        hist = hist[hist["Categoría"].isin(sel_cat)]
    if sel_priority:
        hist = hist[hist["Prioridad"].isin(sel_priority)]
    if sel_region:
        hist = hist[hist["Región / País"].isin(sel_region)]
    if sel_type:
        hist = hist[hist["Tipo Hallazgo"].isin(sel_type)]
    if "Score Autolux" in hist.columns:
        hist = hist[hist["Score Autolux"].fillna(0) >= min_score]

    if search.strip():
        needle = search.strip().lower()
        search_cols = [c for c in ["Título","Resumen Ejecutivo","Por qué importa","Aplicación Autolux","Tema Normalizado"] if c in hist.columns]
        mask = pd.Series(False, index=hist.index)
        for c in search_cols:
            mask = mask | hist[c].fillna("").astype(str).str.lower().str.contains(needle, regex=False)
        hist = hist[mask]

    hist = hist.sort_values(["Fecha Radar","Score Autolux"], ascending=[False, False], na_position="last")

    cols = [c for c in [
        "Fecha Radar","Fecha Publicación","Título","Categoría","Región / País",
        "Score Autolux","Prioridad","Quick Win","Estado","Fuente","URL"
    ] if c in hist.columns]

    st.caption(f"{len(hist)} registros")
    st.dataframe(
        hist[cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fecha Radar": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Fecha Publicación": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Score Autolux": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            "URL": st.column_config.LinkColumn("Fuente"),
        },
    )

# ------------------------------------------------------------
# TAB 3 — TENDENCIAS
# ------------------------------------------------------------
with tabs[2]:
    st.subheader("Tendencias detectadas")

    theme_col = "Tema Normalizado" if "Tema Normalizado" in news.columns else "Categoría"

    trends = (
        news.assign(**{theme_col: news[theme_col].fillna("").astype(str).str.strip()})
        .query(f'`{theme_col}` != ""')
        .groupby(theme_col, dropna=False)
        .agg(
            Apariciones=("ID","count"),
            Score_Promedio=("Score Autolux","mean"),
            Score_Max=("Score Autolux","max"),
            Ultima_Aparicion=("Fecha Radar","max"),
        )
        .reset_index()
        .sort_values(["Apariciones","Score_Promedio"], ascending=[False,False])
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Temas más recurrentes")
        st.bar_chart(trends.set_index(theme_col)["Apariciones"])
    with c2:
        st.markdown("#### Score promedio por tema")
        st.bar_chart(trends.set_index(theme_col)["Score_Promedio"])

    trends["Ultima_Aparicion"] = pd.to_datetime(trends["Ultima_Aparicion"], errors="coerce")
    st.dataframe(
        trends,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score_Promedio": st.column_config.NumberColumn(format="%.1f"),
            "Score_Max": st.column_config.NumberColumn(format="%.0f"),
            "Ultima_Aparicion": st.column_config.DateColumn(format="DD/MM/YYYY"),
        }
    )

# ------------------------------------------------------------
# TAB 4 — QUICK WINS
# ------------------------------------------------------------
with tabs[3]:
    st.subheader("Quick Wins")

    if "Quick Win" in news.columns:
        qw = news[news["Quick Win"].fillna("").astype(str).str.strip().str.lower() == "sí"].copy()
    else:
        qw = news.iloc[0:0].copy()

    qw = qw.sort_values("Score Autolux", ascending=False, na_position="last")

    if qw.empty:
        st.info("Todavía no hay iniciativas marcadas como Quick Win.")
    else:
        for _, row in qw.iterrows():
            detail_card(row)
            st.divider()

# ------------------------------------------------------------
# TAB 5 — ROADMAP
# ------------------------------------------------------------
with tabs[4]:
    st.subheader("Roadmap Autolux")

    if roadmap.empty:
        st.info("La hoja ROADMAP todavía no tiene iniciativas.")
    else:
        roadmap = roadmap.copy()
        for c in ["Score Autolux"]:
            if c in roadmap.columns:
                roadmap[c] = pd.to_numeric(roadmap[c], errors="coerce")
        for c in ["Fecha Inicio","Fecha Objetivo"]:
            if c in roadmap.columns:
                roadmap[c] = pd.to_datetime(roadmap[c], errors="coerce", dayfirst=True)

        if "Estado" in roadmap.columns:
            states = ["Detectada","En análisis","Aprobada","Piloto","Implementada","Descartada"]
            counts = roadmap["Estado"].fillna("Sin estado").value_counts().reindex(states, fill_value=0)
            st.bar_chart(counts)

        roadmap_cols = [c for c in [
            "ID Iniciativa","Iniciativa","Categoría","Score Autolux","Prioridad","Estado",
            "Horizonte","Responsable","Fecha Objetivo","KPI Meta","Próximo Hito","Resultado / Aprendizaje"
        ] if c in roadmap.columns]

        st.dataframe(
            roadmap[roadmap_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score Autolux": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                "Fecha Objetivo": st.column_config.DateColumn(format="DD/MM/YYYY"),
            }
        )

# ------------------------------------------------------------
# TAB 6 — BENCHMARK
# ------------------------------------------------------------
with tabs[5]:
    st.subheader("Benchmark")

    if "Tipo Hallazgo" in news.columns:
        bench = news[news["Tipo Hallazgo"].fillna("").astype(str).str.lower() == "benchmark"].copy()
    else:
        bench = news.iloc[0:0].copy()

    region_filter = st.multiselect(
        "Región",
        sorted(bench["Región / País"].dropna().astype(str).unique()) if "Región / País" in bench.columns else []
    )
    if region_filter:
        bench = bench[bench["Región / País"].isin(region_filter)]

    bench = bench.sort_values("Score Autolux", ascending=False, na_position="last")

    if bench.empty:
        st.info("Todavía no hay benchmarks cargados.")
    else:
        for _, row in bench.iterrows():
            detail_card(row)
            st.divider()

# ------------------------------------------------------------
# TAB 7 — FUENTES
# ------------------------------------------------------------
with tabs[6]:
    st.subheader("Fuentes del Observatorio")

    if fuentes.empty:
        st.info("La hoja FUENTES todavía está vacía.")
    else:
        f = fuentes.copy()
        if "Última Revisión" in f.columns:
            f["Última Revisión"] = pd.to_datetime(f["Última Revisión"], errors="coerce", dayfirst=True)

        cols = [c for c in [
            "Fuente / Medio","Tipo","Región","Especialidad","URL Base",
            "Confiabilidad","Frecuencia Recomendada","Última Revisión","Activa","Notas"
        ] if c in f.columns]

        st.dataframe(
            f[cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL Base": st.column_config.LinkColumn("Sitio"),
                "Última Revisión": st.column_config.DateColumn(format="DD/MM/YYYY"),
            }
        )

st.divider()
st.caption(
    "Observatorio IA Postventa · V0.1 · Fuente: Google Sheets · "
    "El dashboard no modifica la planilla; solo la consulta."
)
