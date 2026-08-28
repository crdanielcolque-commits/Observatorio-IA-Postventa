# ============================================================
# OBSERVATORIO IA POSTVENTA — AUTOLUX
# V0.2 — Inteligencia + Decisión + Ejecución
# Google Sheets + Streamlit
# ============================================================

import html
from urllib.parse import quote

import numpy as np
import pandas as pd
import streamlit as st

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

PRIORITY_ORDER = ["Crítica", "Alta", "Media", "Baja"]

MACRO_ICONS = {
    "Digitalización del Taller": "🧰",
    "Digitalización de Repuestos": "📦",
    "IA Operativa": "🤖",
    "Experiencia Cliente": "✨",
    "Fidelización y Retención": "🤝",
    "Productividad Taller": "⚙️",
    "Logística Inteligente": "🚚",
    "Nuevos Modelos de Servicio": "🚗",
    "Diagnóstico Avanzado / ADAS": "🧠",
    "Mercado / Aftermarket": "📊",
}

st.markdown(
    """
    <style>
      .block-container {padding-top:1.2rem; padding-bottom:3rem; max-width:1500px;}
      h1,h2,h3 {letter-spacing:-0.025em;}
      [data-testid="stMetric"] {
          border:1px solid rgba(128,128,128,.18);
          border-radius:16px;
          padding:13px 15px;
          background:rgba(255,255,255,.025);
      }
      .hero,.radar-card,.initiative-card {
          border:1px solid rgba(128,128,128,.18);
          border-radius:18px;
          padding:18px 20px;
          background:rgba(255,255,255,.025);
          margin-bottom:12px;
      }
      .pill,.score-pill {
          display:inline-block;
          padding:4px 10px;
          border-radius:999px;
          border:1px solid rgba(128,128,128,.28);
          margin-right:6px;
          margin-bottom:4px;
          font-size:.86rem;
          font-weight:700;
      }
      .score-pill {font-weight:800;}
      .muted {opacity:.68; font-size:.9rem;}
      .section-kicker {
          opacity:.68; text-transform:uppercase; letter-spacing:.08em;
          font-size:.76rem; font-weight:700;
      }
      .alert-soft {
          border-left:4px solid #f59e0b;
          background:rgba(245,158,11,.08);
          padding:10px 12px;
          border-radius:8px;
          margin:6px 0;
      }
      .success-soft {
          border-left:4px solid #22c55e;
          background:rgba(34,197,94,.08);
          padding:10px 12px;
          border-radius:8px;
          margin:6px 0;
      }
      .pipeline-box {
          border:1px solid rgba(128,128,128,.18);
          border-radius:14px;
          padding:12px;
          text-align:center;
          min-height:88px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

def esc(v):
    if pd.isna(v):
        return ""
    return html.escape(str(v))

def text(v, default="—"):
    if pd.isna(v) or str(v).strip() == "":
        return default
    return str(v).strip()

def fmt_date(v):
    if pd.isna(v):
        return "—"
    try:
        return pd.Timestamp(v).strftime("%d/%m/%Y")
    except Exception:
        return text(v)

def fmt_num(v, decimals=0):
    if pd.isna(v):
        return "—"
    if decimals == 0:
        return f"{float(v):,.0f}".replace(",", ".")
    return (
        f"{float(v):,.{decimals}f}"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

def priority_icon(p):
    return {
        "Crítica":"🔴",
        "Alta":"🟠",
        "Media":"🟡",
        "Baja":"🟢"
    }.get(text(p, ""), "⚪")

def sheet_csv_url(sheet_name):
    return (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )

@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(sheet_name):
    df = pd.read_csv(sheet_csv_url(sheet_name))
    df.columns = [str(c).strip() for c in df.columns]
    return df

def safe_load(sheet_name):
    try:
        return load_sheet(sheet_name)
    except Exception as e:
        st.warning(f"No pude leer la hoja «{sheet_name}». Detalle: {e}")
        return pd.DataFrame()

def clean_news(df):
    if df.empty:
        return df

    df = df.copy()
    if "ID" in df.columns:
        df = df[df["ID"].notna()]
        df["ID"] = df["ID"].astype(str).str.strip()
        df = df[df["ID"] != ""]

    for c in ["Fecha Radar","Fecha Publicación","Fecha Objetivo","Última Actualización"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

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

    comps = [
        "Impacto Económico (0-25)",
        "Experiencia Cliente (0-20)",
        "Aplicabilidad Autolux (0-20)",
        "Facilidad Implementación (0-15)",
        "Inversión (0-10)",
        "Alineación Estratégica (0-10)",
    ]
    if all(c in df.columns for c in comps):
        calc = df[comps].sum(axis=1, min_count=1)
        if "Score Autolux" not in df.columns:
            df["Score Autolux"] = calc
        else:
            df["Score Autolux"] = df["Score Autolux"].fillna(calc)

    if "Prioridad" not in df.columns:
        df["Prioridad"] = np.nan

    calc_priority = pd.cut(
        df["Score Autolux"],
        bins=[-np.inf, 49.999, 69.999, 84.999, np.inf],
        labels=["Baja","Media","Alta","Crítica"]
    ).astype("object")
    df["Prioridad"] = df["Prioridad"].replace("", np.nan).fillna(calc_priority)

    req = [
        "Score Autolux",
        "Aplicabilidad Autolux (0-20)",
        "Facilidad Implementación (0-15)",
        "Inversión (0-10)",
    ]
    if all(c in df.columns for c in req):
        df["Quick Win Sugerido"] = np.where(
            (df["Score Autolux"] >= 80)
            & (df["Aplicabilidad Autolux (0-20)"] >= 16)
            & (df["Facilidad Implementación (0-15)"] >= 11)
            & (df["Inversión (0-10)"] >= 7),
            "Sí",
            "No",
        )
    else:
        df["Quick Win Sugerido"] = "No"

    if "Macrotendencia" not in df.columns:
        df["Macrotendencia"] = df.get("Tema Normalizado", df.get("Categoría", "Otro"))
    if "Señal Estratégica" not in df.columns:
        df["Señal Estratégica"] = "Aislada"
    if "Tipo Benchmark" not in df.columns:
        df["Tipo Benchmark"] = "No aplica"
    if "Acción Benchmark" not in df.columns:
        df["Acción Benchmark"] = "No aplica"

    return df

def clean_roadmap(df):
    if df.empty:
        return df
    df = df.copy()
    for c in ["Fecha Inicio","Fecha Objetivo","Última Actualización"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    if "Score Autolux" in df.columns:
        df["Score Autolux"] = pd.to_numeric(df["Score Autolux"], errors="coerce")
    return df

def score_breakdown(row):
    data = [
        ("Impacto económico", row.get("Impacto Económico (0-25)", np.nan), 25),
        ("Experiencia cliente", row.get("Experiencia Cliente (0-20)", np.nan), 20),
        ("Aplicabilidad Autolux", row.get("Aplicabilidad Autolux (0-20)", np.nan), 20),
        ("Facilidad implementación", row.get("Facilidad Implementación (0-15)", np.nan), 15),
        ("Inversión favorable", row.get("Inversión (0-10)", np.nan), 10),
        ("Alineación estratégica", row.get("Alineación Estratégica (0-10)", np.nan), 10),
    ]
    out = pd.DataFrame(data, columns=["Dimensión","Puntos","Máximo"])
    out["%"] = (pd.to_numeric(out["Puntos"], errors="coerce") / out["Máximo"] * 100).round(0)
    return out

def render_tags(row):
    vals = [
        f"{priority_icon(row.get('Prioridad'))} {text(row.get('Prioridad'))}",
        text(row.get("Categoría")),
        text(row.get("Región / País")),
        text(row.get("Tipo Hallazgo")),
    ]
    macro = text(row.get("Macrotendencia"), "")
    if macro:
        vals.append(f"{MACRO_ICONS.get(macro,'🔭')} {macro}")
    return "".join(
        f'<span class="pill">{esc(v)}</span>'
        for v in vals if v not in ["", "—"]
    )

def render_news_card(row, show_score_expander=True):
    quick = text(row.get("Quick Win", "No"))
    qws = text(row.get("Quick Win Sugerido", "No"))
    quick_tag = ""
    if quick == "Sí":
        quick_tag = '<span class="pill">⚡ Quick Win confirmado</span>'
    elif qws == "Sí":
        quick_tag = '<span class="pill">⚡ Quick Win sugerido</span>'

    st.markdown(
        f"""
        <div class="radar-card">
          <div>{render_tags(row)} {quick_tag}</div>
          <h3 style="margin:.35rem 0 .5rem 0;">{esc(text(row.get("Título")))}</h3>
          <div class="muted">
            Publicación: {fmt_date(row.get("Fecha Publicación"))}
            · Radar: {fmt_date(row.get("Fecha Radar"))}
            · Fuente: {esc(text(row.get("Fuente")))}
          </div>
          <div style="margin-top:.6rem;">
            <span class="score-pill">Score Autolux: {fmt_num(row.get("Score Autolux"))}</span>
            <span class="pill">Señal: {esc(text(row.get("Señal Estratégica")))}</span>
            <span class="pill">Benchmark: {esc(text(row.get("Acción Benchmark")))}</span>
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

    url = text(row.get("URL", ""), "")
    if url:
        st.link_button("🔗 Ver fuente original", url)

    if show_score_expander:
        with st.expander("¿Por qué tiene este Score?"):
            br = score_breakdown(row)
            st.dataframe(
                br, use_container_width=True, hide_index=True,
                column_config={
                    "%": st.column_config.ProgressColumn(
                        min_value=0,max_value=100,format="%d%%"
                    )
                }
            )

def missing_roadmap_fields(row):
    checks = {
        "Responsable": row.get("Responsable"),
        "Fecha Objetivo": row.get("Fecha Objetivo"),
        "KPI Base": row.get("KPI Base"),
        "KPI Meta": row.get("KPI Meta"),
    }
    missing = []
    for label, value in checks.items():
        if pd.isna(value) or str(value).strip() in ["","None","nan"]:
            missing.append(label)
    return missing

news = clean_news(safe_load(SHEETS["noticias"]))
roadmap = clean_roadmap(safe_load(SHEETS["roadmap"]))
fuentes = safe_load(SHEETS["fuentes"])
autolog = safe_load(SHEETS["autolog"])

with st.sidebar:
    st.markdown("## 📡 Observatorio IA")
    st.caption("Postventa Autolux · V0.2")
    st.divider()
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Lectura automática del Google Sheet cada 5 minutos.")
    st.divider()
    st.markdown("**Modelo del Observatorio**")
    st.caption("1. Inteligencia → 2. Decisión → 3. Ejecución")
    if not news.empty and "Fecha Radar" in news.columns:
        st.caption(f"Último radar: {fmt_date(news['Fecha Radar'].dropna().max())}")

st.title("📡 Observatorio IA Postventa")
st.caption(
    "Inteligencia estratégica aplicada a Taller / Servicios, Repuestos, "
    "experiencia de cliente e innovación."
)

if news.empty:
    st.error("La hoja NOTICIAS está vacía o no pudo leerse.")
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

# TAB 1
with tabs[0]:
    latest = news["Fecha Radar"].dropna().max()
    day = news[news["Fecha Radar"] == latest].copy()
    day = day.sort_values("Score Autolux", ascending=False)

    st.subheader(f"Radar IA Postventa — Edición Ejecutiva {fmt_date(latest)}")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Oportunidades detectadas", len(day))
    c2.metric("Score promedio", fmt_num(day["Score Autolux"].mean(),1))
    c3.metric("Prioridad crítica", int((day["Prioridad"]=="Crítica").sum()))
    c4.metric("Quick Wins sugeridos", int(day["Quick Win Sugerido"].eq("Sí").sum()))

    if not day.empty:
        top = day.iloc[0]
        st.markdown("### 🔥 Oportunidad Nº 1 para Autolux")
        st.markdown(
            f"""
            <div class="hero">
              <div class="section-kicker">Mayor prioridad del radar</div>
              <h2 style="margin:.25rem 0 .4rem 0;">{esc(text(top.get("Título")))}</h2>
              <span class="score-pill">Score {fmt_num(top.get("Score Autolux"))}</span>
              <span class="pill">{priority_icon(top.get("Prioridad"))} {esc(text(top.get("Prioridad")))}</span>
              <span class="pill">{esc(text(top.get("Macrotendencia")))}</span>
              <p style="margin-top:.9rem;">{esc(text(top.get("Aplicación Autolux")))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Novedades del radar")
    for _, row in day.iterrows():
        render_news_card(row)
        st.divider()

# TAB 2
with tabs[1]:
    st.subheader("Histórico completo")
    f1,f2,f3,f4 = st.columns(4)
    with f1:
        sel_cat = st.multiselect("Categoría", sorted(news["Categoría"].dropna().astype(str).unique()))
    with f2:
        sel_priority = st.multiselect("Prioridad", PRIORITY_ORDER)
    with f3:
        sel_region = st.multiselect("Región / País", sorted(news["Región / País"].dropna().astype(str).unique()))
    with f4:
        sel_type = st.multiselect("Tipo de hallazgo", sorted(news["Tipo Hallazgo"].dropna().astype(str).unique()))

    g1,g2 = st.columns([2,1])
    with g1:
        search = st.text_input("Buscar", placeholder="Ej.: Video MPI, eCommerce, IA, ADAS...")
    with g2:
        min_score = st.slider("Score mínimo",0,100,0)

    hist = news.copy()
    if sel_cat: hist = hist[hist["Categoría"].isin(sel_cat)]
    if sel_priority: hist = hist[hist["Prioridad"].isin(sel_priority)]
    if sel_region: hist = hist[hist["Región / País"].isin(sel_region)]
    if sel_type: hist = hist[hist["Tipo Hallazgo"].isin(sel_type)]
    hist = hist[hist["Score Autolux"].fillna(0) >= min_score]

    if search.strip():
        needle = search.strip().lower()
        cols = [c for c in ["Título","Resumen Ejecutivo","Por qué importa","Aplicación Autolux","Tema Normalizado","Macrotendencia","Fuente"] if c in hist.columns]
        mask = pd.Series(False,index=hist.index)
        for c in cols:
            mask = mask | hist[c].fillna("").astype(str).str.lower().str.contains(needle, regex=False)
        hist = hist[mask]

    m1,m2,m3 = st.columns(3)
    m1.metric("Resultados",len(hist))
    m2.metric("Score promedio",fmt_num(hist["Score Autolux"].mean(),1))
    m3.metric("Críticas",int((hist["Prioridad"]=="Crítica").sum()))

    hist = hist.sort_values(["Score Autolux","Fecha Radar"],ascending=[False,False])

    show_cols = [c for c in [
        "ID","Fecha Radar","Fecha Publicación","Título","Categoría","Macrotendencia",
        "Región / País","Score Autolux","Prioridad","Quick Win Sugerido","Estado","Fuente","URL"
    ] if c in hist.columns]

    st.dataframe(
        hist[show_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fecha Radar": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Fecha Publicación": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Score Autolux": st.column_config.ProgressColumn(min_value=0,max_value=100,format="%d"),
            "URL": st.column_config.LinkColumn("Fuente original"),
        }
    )

    if not hist.empty:
        st.markdown("### Ver detalle")
        opts = hist["ID"].astype(str) + " · " + hist["Título"].astype(str)
        selected = st.selectbox("Selecciona un hallazgo",opts.tolist())
        sid = selected.split(" · ",1)[0]
        selected_row = hist[hist["ID"].astype(str)==sid].iloc[0]
        render_news_card(selected_row)

        macro = text(selected_row.get("Macrotendencia",""),"")
        if macro:
            related = news[
                (news["Macrotendencia"].fillna("").astype(str)==macro)
                & (news["ID"].astype(str)!=str(selected_row.get("ID")))
            ].sort_values("Score Autolux",ascending=False)
            if not related.empty:
                st.markdown("#### Oportunidades relacionadas")
                st.dataframe(
                    related[["Fecha Radar","Título","Score Autolux","Prioridad"]],
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Fecha Radar": st.column_config.DateColumn(format="DD/MM/YYYY"),
                        "Score Autolux": st.column_config.ProgressColumn(min_value=0,max_value=100,format="%d")
                    }
                )

# TAB 3
with tabs[2]:
    st.subheader("Señales estratégicas y macrotendencias")
    base = news.copy()
    base["Macrotendencia"] = base["Macrotendencia"].fillna("Sin clasificar").astype(str).str.strip()

    trends = (
        base.groupby("Macrotendencia")
        .agg(
            Señales=("ID","count"),
            Score_Promedio=("Score Autolux","mean"),
            Score_Máximo=("Score Autolux","max"),
            Última_Aparición=("Fecha Radar","max"),
        )
        .reset_index()
    )

    trends["Lectura"] = np.select(
        [trends["Señales"]>=5,trends["Señales"]>=3,trends["Señales"]>=2],
        ["Tendencia consolidada","Tendencia","Señal emergente"],
        default="Señal inicial"
    )
    trends = trends.sort_values(["Señales","Score_Promedio"],ascending=[False,False])

    if not trends.empty:
        t = trends.iloc[0]
        st.markdown(
            f"""
            <div class="hero">
              <div class="section-kicker">Señal con mayor recurrencia</div>
              <h3>{MACRO_ICONS.get(text(t["Macrotendencia"]),'🔭')} {esc(text(t["Macrotendencia"]))}</h3>
              <p>{int(t["Señales"])} señal(es) · Score promedio {fmt_num(t["Score_Promedio"],1)} · {esc(text(t["Lectura"]))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Recurrencia por macrotendencia")
        if not trends.empty:
            st.bar_chart(trends.set_index("Macrotendencia")["Señales"])
    with c2:
        st.markdown("#### Score promedio")
        if not trends.empty:
            st.bar_chart(trends.set_index("Macrotendencia")["Score_Promedio"])

    st.dataframe(
        trends,use_container_width=True,hide_index=True,
        column_config={
            "Score_Promedio": st.column_config.NumberColumn(format="%.1f"),
            "Score_Máximo": st.column_config.NumberColumn(format="%.0f"),
            "Última_Aparición": st.column_config.DateColumn(format="DD/MM/YYYY"),
        }
    )

# TAB 4
with tabs[3]:
    st.subheader("Quick Wins")
    qw = news[news["Quick Win Sugerido"]=="Sí"].copy()
    qw = qw.sort_values(
        ["Score Autolux","Facilidad Implementación (0-15)","Inversión (0-10)"],
        ascending=[False,False,False]
    )

    a,b,c,d = st.columns(4)
    a.metric("Quick Wins sugeridos",len(qw))
    b.metric("Score promedio",fmt_num(qw["Score Autolux"].mean(),1) if not qw.empty else "—")
    c.metric("Confirmados",int(qw["Quick Win"].fillna("").astype(str).str.lower().eq("sí").sum()) if "Quick Win" in qw.columns else 0)
    d.metric("Críticos",int((qw["Prioridad"]=="Crítica").sum()) if not qw.empty else 0)

    st.caption("Criterio: Score ≥80 + Aplicabilidad ≥16 + Facilidad ≥11 + Inversión favorable ≥7.")

    for i,(_,row) in enumerate(qw.iterrows(),start=1):
        st.markdown(f"### #{i} · {text(row.get('Título'))}")
        st.markdown(
            f"""
            <div class="initiative-card">
              <span class="score-pill">Score {fmt_num(row.get("Score Autolux"))}</span>
              <span class="pill">{priority_icon(row.get("Prioridad"))} {esc(text(row.get("Prioridad")))}</span>
              <span class="pill">Facilidad {fmt_num(row.get("Facilidad Implementación (0-15)"))}/15</span>
              <span class="pill">Inversión favorable {fmt_num(row.get("Inversión (0-10)"))}/10</span>
              <span class="pill">{esc(text(row.get("Macrotendencia")))}</span>
              <p style="margin-top:.8rem;"><b>Acción:</b> {esc(text(row.get("Próxima Acción")))}</p>
              <p><b>KPI sugerido:</b> {esc(text(row.get("KPI Esperado")))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Ver detalle completo"):
            render_news_card(row,show_score_expander=False)
        st.divider()

# TAB 5
with tabs[4]:
    st.subheader("Roadmap Autolux")
    if roadmap.empty:
        st.info("La hoja ROADMAP todavía no tiene iniciativas.")
    else:
        states = ["Detectada","En análisis","Aprobada","Piloto","Implementada","Descartada"]
        counts = roadmap["Estado"].fillna("Sin estado").value_counts() if "Estado" in roadmap.columns else pd.Series(dtype=int)
        st.markdown("### Pipeline de iniciativas")
        cols = st.columns(len(states))
        for col,state in zip(cols,states):
            with col:
                st.markdown(
                    f"""
                    <div class="pipeline-box">
                      <div class="muted">{esc(state)}</div>
                      <div style="font-size:1.8rem;font-weight:800;">{int(counts.get(state,0))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("### Portfolio de iniciativas")
        rd = roadmap.sort_values("Score Autolux",ascending=False,na_position="last") if "Score Autolux" in roadmap.columns else roadmap
        for _,row in rd.iterrows():
            missing = missing_roadmap_fields(row)
            st.markdown(
                f"""
                <div class="initiative-card">
                  <div class="section-kicker">{esc(text(row.get("ID Iniciativa"),""))}</div>
                  <h3 style="margin:.2rem 0 .5rem 0;">{esc(text(row.get("Iniciativa")))}</h3>
                  <span class="score-pill">Score {fmt_num(row.get("Score Autolux"))}</span>
                  <span class="pill">Estado: {esc(text(row.get("Estado")))}</span>
                  <span class="pill">Horizonte: {esc(text(row.get("Horizonte")))}</span>
                  <span class="pill">Responsable: {esc(text(row.get("Responsable"),"Pendiente"))}</span>
                  <p style="margin-top:.8rem;"><b>Objetivo:</b> {esc(text(row.get("Objetivo")))}</p>
                  <p><b>Próximo hito:</b> {esc(text(row.get("Próximo Hito")))}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if missing:
                st.markdown(
                    f'<div class="alert-soft">⚠️ <b>Iniciativa incompleta:</b> faltan {esc(", ".join(missing))}.</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="success-soft">✅ La iniciativa tiene definidos los campos básicos de gestión.</div>',
                    unsafe_allow_html=True
                )

            d1,d2,d3,d4 = st.columns(4)
            d1.metric("KPI Base",text(row.get("KPI Base")))
            d2.metric("KPI Meta",text(row.get("KPI Meta")))
            d3.metric("KPI Real",text(row.get("KPI Real")))
            d4.metric("Fecha objetivo",fmt_date(row.get("Fecha Objetivo")))
            st.divider()

# TAB 6
with tabs[5]:
    st.subheader("Benchmark Explorer")
    st.caption("¿Qué están haciendo otros que Autolux podría copiar, adaptar, usar como inspiración o monitorear?")

    bench = news[
        (news["Tipo Hallazgo"].fillna("").astype(str).str.lower()=="benchmark")
        | (news["Tipo Benchmark"].fillna("").astype(str).str.lower()!="no aplica")
    ].copy()

    b1,b2,b3,b4 = st.columns(4)
    with b1:
        rf = st.multiselect("Región",sorted(bench["Región / País"].dropna().astype(str).unique()))
    with b2:
        cf = st.multiselect("Categoría",sorted(bench["Categoría"].dropna().astype(str).unique()))
    with b3:
        tf = st.multiselect("Tipo benchmark",sorted(bench["Tipo Benchmark"].dropna().astype(str).unique()))
    with b4:
        af = st.multiselect("Acción",["Copiar","Adaptar","Inspirarse","Monitorear","No aplica"])

    if rf: bench = bench[bench["Región / País"].isin(rf)]
    if cf: bench = bench[bench["Categoría"].isin(cf)]
    if tf: bench = bench[bench["Tipo Benchmark"].isin(tf)]
    if af: bench = bench[bench["Acción Benchmark"].isin(af)]

    bench = bench.sort_values("Score Autolux",ascending=False)
    for _,row in bench.iterrows():
        st.markdown(f"### {text(row.get('Acción Benchmark'))} · {text(row.get('Título'))}")
        render_news_card(row)
        st.divider()

# TAB 7
with tabs[6]:
    st.subheader("Mapa de fuentes del Observatorio")
    if fuentes.empty:
        st.info("La hoja FUENTES todavía está vacía.")
    else:
        f = fuentes.copy()
        if "Última Revisión" in f.columns:
            f["Última Revisión"] = pd.to_datetime(f["Última Revisión"],errors="coerce",dayfirst=True)
        if "Fuente / Medio" in f.columns:
            f = f[~f["Fuente / Medio"].fillna("").astype(str).str.lower().str.contains("ejemplo de fuente")]

        c1,c2,c3 = st.columns(3)
        c1.metric("Fuentes registradas",len(f))
        c2.metric("Confiabilidad alta",int((f["Confiabilidad"].fillna("")=="Alta").sum()) if "Confiabilidad" in f.columns else 0)
        c3.metric("Activas",int(f["Activa"].fillna("").astype(str).str.lower().eq("sí").sum()) if "Activa" in f.columns else 0)

        if f.empty:
            st.warning("La hoja FUENTES solo contiene el registro de ejemplo. Cuando carguemos fuentes reales, aparecerán aquí.")
        else:
            cols = [c for c in [
                "Fuente / Medio","Tipo","Región","Especialidad","URL Base","Confiabilidad",
                "Frecuencia Recomendada","Última Revisión","Activa","Notas"
            ] if c in f.columns]
            st.dataframe(
                f[cols],use_container_width=True,hide_index=True,
                column_config={
                    "URL Base": st.column_config.LinkColumn("Sitio"),
                    "Última Revisión": st.column_config.DateColumn(format="DD/MM/YYYY")
                }
            )

        st.markdown("### Cobertura objetivo")
        st.write(
            "Argentina/NOA, automoción internacional, aftermarket/repuestos, "
            "tecnología/IA y benchmarks cross-industry."
        )

st.divider()
st.caption(
    "Observatorio IA Postventa · V0.2 · Google Sheets + Streamlit · "
    "El dashboard consulta la base y no modifica el Google Sheet."
)
