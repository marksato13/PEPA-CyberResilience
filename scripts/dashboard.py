import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import os
import platform
import socket
import subprocess

st.set_page_config(
    page_title="Resiliencia Informática · UPeU 2026",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    "DDoS":              "#ef5350",
    "Malware":           "#ff9800",
    "Man-in-the-Middle": "#ab47bc",
    "Phishing":          "#42a5f5",
    "Ransomware":        "#ffca28",
    "SQL Injection":     "#26a69a",
}
BG, BG2 = "#0d1117", "#161b22"

# ── estado de navegación ──────────────────────────────────────────────────────
if "nav" not in st.session_state:
    st.session_state.nav = "dashboard"

st.markdown("""
<style>
/* ── base ─────────────────────────────────────────── */
.stApp                        { background:#0d1117; color:#e6edf3; }
[data-testid="stSidebar"]     { background:#0d1117; border-right:1px solid #21262d; }
[data-testid="stSidebar"]>div { padding:0 !important; overflow-x:hidden; }
[data-testid="stSidebar"] *   { box-sizing:border-box; }

/* ── sidebar logo ──────────────────────────────────── */
.sb-logo {
    padding:20px 18px 16px;
    border-bottom:1px solid #21262d;
}
.sb-logo-t { font-size:.9rem; font-weight:800; color:#fff; line-height:1.3; }
.sb-logo-s { font-size:.64rem; color:#8b949e; margin-top:3px; }

/* ── nav tabs ──────────────────────────────────────── */
[data-testid="stSidebar"] [role="radiogroup"] {
    display:grid !important;
    grid-template-columns:1fr 1fr;
    gap:0 !important;
    width:100%;
    border-top:1px solid #21262d;
    border-bottom:1px solid #21262d;
    background:#161b22;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-width:0 !important;
    margin:0 !important;
    padding:0 !important;
    border-radius:0 !important;
    background:transparent !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child {
    display:none !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label>div:last-child {
    width:100%;
    min-height:42px;
    display:flex;
    align-items:center;
    justify-content:center;
    padding:0 8px;
    border-bottom:2px solid transparent;
    color:#8b949e;
    font-size:.68rem;
    font-weight:800;
    letter-spacing:.06em;
    text-transform:uppercase;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)>div:last-child {
    color:#ffffff;
    background:#0d1117;
    border-bottom-color:#FFD700;
}

/* ── system info ───────────────────────────────────── */
.sys-blk { padding:12px 18px 6px; }
.sys-gt  { font-size:.58rem; font-weight:700; color:#444d56;
           letter-spacing:.12em; text-transform:uppercase; margin:10px 0 5px; }
.sys-row {
    display:flex; justify-content:space-between; align-items:center;
    gap:10px; padding:5px 0; border-bottom:1px solid #21262d44; font-size:.71rem;
}
.sys-l { color:#8b949e; min-width:0; overflow-wrap:anywhere; }
.sys-v { color:#e6edf3; font-family:monospace; font-size:.67rem; text-align:right; overflow-wrap:anywhere; }
.sys-ok{ color:#3fb950; font-weight:700; }
.sys-warn{ color:#ffca28; font-weight:700; }

/* ── main header ───────────────────────────────────── */
.mhd {
    display:flex; justify-content:space-between; align-items:flex-start;
    padding-bottom:12px; border-bottom:1px solid #21262d; margin-bottom:12px;
}
.mhd-t { font-size:1.35rem; font-weight:800; color:#fff; letter-spacing:-.02em; }
.mhd-s { font-size:.81rem; color:#8b949e; margin-top:2px; }
.mhd-m { text-align:right; font-size:.67rem; color:#8b949e; line-height:1.9; }
.live-dot { color:#3fb950; font-weight:700; }

/* ── info strip ────────────────────────────────────── */
.istrip { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
.icard  {
    background:#161b22; border:1px solid #21262d;
    border-radius:8px; padding:12px 14px;
}
.icard-t {
    font-size:.58rem; font-weight:700; color:#8b949e;
    letter-spacing:.1em; text-transform:uppercase; margin-bottom:8px;
}
.arow { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.av   {
    width:26px; height:26px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    font-size:.62rem; font-weight:800;
}
.an { font-size:.74rem; font-weight:600; color:#e6edf3; }
.ac { font-size:.62rem; color:#8b949e; }
.orow {
    padding:7px 9px; border-radius:5px; margin-bottom:5px;
    border-left:3px solid var(--c); background:#0d1117;
}
.ot { font-size:.58rem; font-weight:700; color:var(--c);
      letter-spacing:.07em; text-transform:uppercase; }
.ob { font-size:.7rem; color:#c9d1d9; margin-top:2px; line-height:1.4; }

/* ── KPI ───────────────────────────────────────────── */
.kpi {
    background:#161b22; border:1px solid #21262d;
    border-radius:8px; padding:13px 10px 9px; text-align:center;
}
.kv { font-size:1.55rem; font-weight:800; line-height:1; }
.kl { font-size:.68rem; color:#8b949e; margin-top:4px; }

/* ── obj badge en tabs ─────────────────────────────── */
.obj-tag-main {
    display:inline-block; padding:2px 8px;
    border-radius:4px; font-size:.6rem; font-weight:700;
    letter-spacing:.07em; text-transform:uppercase;
    margin-bottom:10px;
}

/* ── section heading ───────────────────────────────── */
.sh {
    font-size:.64rem; font-weight:700; color:#8b949e;
    letter-spacing:.1em; text-transform:uppercase;
    border-left:3px solid var(--c,#58a6ff);
    padding-left:8px; margin:4px 0 10px;
}
.cl { font-size:.79rem; font-weight:600; color:#c9d1d9; margin-bottom:5px; }

/* ── live ──────────────────────────────────────────── */
.lbar { display:flex; align-items:center; gap:9px; margin-bottom:9px; }
.pulse{
    width:8px; height:8px; border-radius:50%; background:#ef5350;
    animation:blink 1.2s ease-in-out infinite; flex-shrink:0;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.1}}
.lt { font-size:.92rem; font-weight:700; color:#e6edf3; }
.lc { font-size:.69rem; color:#8b949e; }

/* ── popover button ────────────────────────────────── */
[data-testid="stPopover"] button {
    background:#161b22 !important;
    border:1px solid #30363d !important;
    color:#e6edf3 !important;
    font-size:.75rem !important;
    font-weight:600 !important;
    border-radius:6px !important;
    padding:6px 14px !important;
}
[data-testid="stPopover"] button:hover {
    border-color:#58a6ff !important;
    color:#58a6ff !important;
}

/* ── footer ────────────────────────────────────────── */
.foot {
    margin-top:24px; padding-top:10px;
    border-top:1px solid #21262d;
    display:flex; justify-content:space-between;
    font-size:.63rem; color:#444d56;
}

/* ── misc overrides ────────────────────────────────── */
div[data-testid="stVerticalBlock"]>div { padding-top:0 !important; }
.stSlider label,.stMultiSelect label,.stSelectbox label {
    font-size:.7rem !important; color:#8b949e !important;
}
@media (max-width: 900px) {
    .mhd,.foot { flex-direction:column; gap:8px; }
    .mhd-m { text-align:left; }
    .istrip { grid-template-columns:1fr; }
}
</style>
""", unsafe_allow_html=True)

count = st_autorefresh(interval=3000, key="ar")

HOME     = os.path.expanduser("~")
PARQUET  = os.path.join(HOME, "bigdata", "output", "cybersecurity_joined")
LIVE_CSV = os.path.join(HOME, "bigdata", "output", "live_events.csv")

def proc_pids(pattern):
    try:
        out = subprocess.check_output(["pgrep", "-f", pattern], text=True).strip()
        return [p for p in out.splitlines() if p]
    except subprocess.CalledProcessError:
        return []

def first_ip():
    try:
        return subprocess.check_output(["hostname", "-I"], text=True).split()[0]
    except Exception:
        return socket.gethostbyname(socket.gethostname())

def human_status(pids, suffix=""):
    if not pids:
        return '<span class="sys-v sys-warn">inactivo</span>'
    label = f"activo · PID {pids[0]}"
    if suffix:
        label = f"activo · {suffix}"
    return f'<span class="sys-v sys-ok">{label}</span>'

@st.cache_data(ttl=60)
def load_static():
    df = pd.read_parquet(PARQUET)
    for c in ["Financial_Loss_M","Affected_Users","Year"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

@st.cache_data(ttl=2)
def load_live():
    if os.path.exists(LIVE_CSV):
        return pd.read_csv(LIVE_CSV, parse_dates=["timestamp"])
    return pd.DataFrame(columns=["timestamp","attack_type","severity",
                                  "country","data_GB","outcome"])

df  = load_static()
liv = load_live()
host_ip = first_ip()
gen_pids = proc_pids("event_generator.py")
dash_pids = proc_pids("streamlit run")
parquet_rows, parquet_cols = df.shape
partitions = sum(name.startswith("Year=") for _, dirs, _ in os.walk(PARQUET) for name in dirs) if os.path.isdir(PARQUET) else 0

years     = sorted(df["Year"].dropna().unique().astype(int).tolist())
atk_types = sorted(df["Attack_Type"].dropna().unique().tolist())
inds      = sorted(df["Target_Industry"].dropna().unique().tolist())

# ══════════════════════════════════════════════════════
# SIDEBAR — logo + navegación estable + contenido
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-t">Big Data · Resiliencia<br>Informática</div>
        <div class="sb-logo-s">UPeU · Semestre 2026-1</div>
    </div>
    """, unsafe_allow_html=True)

    nav_label = st.radio(
        "Navegación",
        ["Dashboard", "Sistema"],
        index=0 if st.session_state.nav == "dashboard" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.nav = "dashboard" if nav_label == "Dashboard" else "sistema"

    # ── contenido según nav ──────────────────────────
    if st.session_state.nav == "sistema":
        st.markdown(f"""
        <div class="sys-blk">
            <div class="sys-gt">Procesos activos</div>
            <div class="sys-row"><span class="sys-l">Pipeline Spark</span>
                <span class="sys-v sys-ok">completado</span></div>
            <div class="sys-row"><span class="sys-l">Generador eventos</span>
                {human_status(gen_pids)}</div>
            <div class="sys-row"><span class="sys-l">Dashboard</span>
                {human_status(dash_pids, ":8501")}</div>

            <div class="sys-gt">Datos</div>
            <div class="sys-row"><span class="sys-l">Parquet (estático)</span>
                <span class="sys-v">{parquet_rows:,} filas · {parquet_cols} cols</span></div>
            <div class="sys-row"><span class="sys-l">Particiones</span>
                <span class="sys-v">{partitions or "OK"} particiones</span></div>
            <div class="sys-row"><span class="sys-l">Feed vivo (CSV)</span>
                <span class="sys-v sys-ok">{len(liv):,} eventos</span></div>
            <div class="sys-row"><span class="sys-l">Tasa generador</span>
                <span class="sys-v">~1 / 1.5 seg</span></div>

            <div class="sys-gt">Infraestructura</div>
            <div class="sys-row"><span class="sys-l">VM host</span>
                <span class="sys-v">{host_ip}</span></div>
            <div class="sys-row"><span class="sys-l">SO</span>
                <span class="sys-v">{platform.system()} {platform.release()}</span></div>
            <div class="sys-row"><span class="sys-l">RAM / vCPUs</span>
                <span class="sys-v">7.8 GB / 4</span></div>
            <div class="sys-row"><span class="sys-l">Java</span>
                <span class="sys-v">OpenJDK 17.0.19</span></div>

            <div class="sys-gt">Stack tecnológico</div>
            <div class="sys-row"><span class="sys-l">Apache Spark</span>
                <span class="sys-v">4.1.2 local[*]</span></div>
            <div class="sys-row"><span class="sys-l">Driver memory</span>
                <span class="sys-v">5 GB</span></div>
            <div class="sys-row"><span class="sys-l">PySpark / pandas</span>
                <span class="sys-v">4.1.2 / 2.2.3</span></div>
            <div class="sys-row"><span class="sys-l">pyarrow</span>
                <span class="sys-v">24.0.0</span></div>
            <div class="sys-row"><span class="sys-l">Streamlit / Plotly</span>
                <span class="sys-v">1.58 / 6.7</span></div>

            <div class="sys-gt">Configuración Spark</div>
            <div class="sys-row"><span class="sys-l">Shuffle partitions</span>
                <span class="sys-v">4</span></div>
            <div class="sys-row"><span class="sys-l">Cache Parquet</span>
                <span class="sys-v">ttl = 60 s</span></div>
            <div class="sys-row"><span class="sys-l">Cache feed vivo</span>
                <span class="sys-v">ttl = 2 s</span></div>
            <div class="sys-row"><span class="sys-l">Autorefresh UI</span>
                <span class="sys-v">3 s</span></div>
        </div>
        """, unsafe_allow_html=True)

# ── valores por defecto (sin filtros activos en sidebar) ─────────────────────
sel_years   = (min(years), max(years))
sel_attacks = atk_types.copy()
sel_ind     = inds.copy()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="mhd">
  <div>
    <div class="mhd-t">Arquitectura de Big Data para la Resiliencia Informática</div>
    <div class="mhd-s">Correlación de Brechas de Seguridad, Ataques Globales y Eventos de IA · 2015–2025</div>
  </div>
  <div class="mhd-m">
    <span class="live-dot">● EN VIVO</span><br>
    {datetime.now().strftime('%H:%M:%S')}<br>UPeU 2026-1
  </div>
</div>
""", unsafe_allow_html=True)

# ── banda autores + objetivos ─────────────────────────────────────────────────
st.markdown("""
<div class="istrip">
  <div class="icard">
    <div class="icard-t">Autores</div>
    <div class="arow">
      <div class="av" style="background:#1f6feb20;color:#1f6feb;">RM</div>
      <div><div class="an">Ruben Mark Salazar Tocas</div><div class="ac">Cód. 75184251</div></div>
    </div>
    <div class="arow">
      <div class="av" style="background:#26a69a20;color:#26a69a;">DC</div>
      <div><div class="an">Daniel H. Calderon Camacho</div><div class="ac">Cód. 71101519</div></div>
    </div>
    <div class="arow">
      <div class="av" style="background:#ab47bc20;color:#ab47bc;">UE</div>
      <div><div class="an">Uziel Elias Sauñe Fernandez</div><div class="ac">Cód. 75664788</div></div>
    </div>
  </div>
  <div class="icard">
    <div class="icard-t">Objetivos del proyecto</div>
    <div class="orow" style="--c:#3fb950">
      <div class="ot">Objetivo 1 — Pipeline distribuido</div>
      <div class="ob">JOIN triple · 3 fuentes (123K registros) · Spark 4.1.2 · Parquet particionado por Attack_Type × Year</div>
    </div>
    <div class="orow" style="--c:#ab47bc">
      <div class="ot">Objetivo 2 — Clasificación ML</div>
      <div class="ob">RF · DT · MLP · GBT · CrossValidator 3-fold · 33 features · 5 clases de ataque</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs + botón filtros ──────────────────────────────────────────────────────
filt_col, *kpi_cols = st.columns([0.7, 1, 1, 1, 1, 1])

with filt_col:
    with st.popover("⚙ Filtros"):
        st.markdown("**Ajusta los datos mostrados**")
        sel_years   = st.select_slider("Periodo", options=years,
                                       value=(min(years), max(years)))
        sel_attacks = st.multiselect("Tipo de ataque", atk_types, default=atk_types)
        sel_ind     = st.multiselect("Industria", inds, default=inds)

filt = (
    df["Year"].between(sel_years[0], sel_years[1]) &
    df["Attack_Type"].isin(sel_attacks) &
    df["Target_Industry"].isin(sel_ind)
)
dff = df[filt]

kpis = [
    (f"{len(dff):,}",                             "Incidentes",       "#58a6ff"),
    (f"${dff['Financial_Loss_M'].sum()/1000:.1f}B","Pérdida USD",     "#ef5350"),
    (f"{dff['Affected_Users'].sum()/1e9:.2f}B",   "Usuarios afect.", "#ff9800"),
    (f"{dff['Country'].nunique()}",                "Países",          "#26a69a"),
    (f"{len(liv):,}",                             "Eventos vivo",    "#ab47bc"),
]
for col, (val, lbl, color) in zip(kpi_cols, kpis):
    col.markdown(f'<div class="kpi"><div class="kv" style="color:{color}">{val}</div>'
                 f'<div class="kl">{lbl}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS — cada uno etiquetado con su objetivo
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "  Tendencia y Distribución  ",
    "  Geografía y Finanzas  ",
    "  Industria y Severidad  ",
    "  ML y Feed en Vivo  ",
])

def chart_cfg(fig, h=280):
    fig.update_layout(paper_bgcolor=BG2, plot_bgcolor=BG, font_color="#c9d1d9",
                      margin=dict(t=4,b=4,l=4,r=4), height=h)
    return fig

# ─── TAB 1 — Objetivo 1 ───────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div style="background:#3fb95015;border:1px solid #3fb95040;border-radius:6px;
         padding:8px 12px;margin-bottom:12px;">
      <span style="font-size:.62rem;font-weight:700;color:#3fb950;
            letter-spacing:.08em;text-transform:uppercase;">
        Objetivo 1 — Pipeline distribuido
      </span>
      <span style="font-size:.73rem;color:#8b949e;margin-left:8px;">
        Visualiza el dataset consolidado (T1+T2+T3) tras el JOIN triple · 3,000 filas · Parquet
      </span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown('<div class="cl">Distribución por tipo de ataque</div>', unsafe_allow_html=True)
        pie = dff["Attack_Type"].value_counts().reset_index()
        pie.columns = ["Attack_Type","n"]
        fig = px.pie(pie, values="n", names="Attack_Type",
                     color="Attack_Type", color_discrete_map=COLORS, hole=0.46)
        fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=10)
        st.plotly_chart(chart_cfg(fig), use_container_width=True)

    with c2:
        st.markdown('<div class="cl">Pérdida financiera acumulada por año (USD M) · fuente T1</div>',
                    unsafe_allow_html=True)
        yr = dff.groupby(["Year","Attack_Type"])["Financial_Loss_M"].sum().reset_index()
        fig = px.bar(yr, x="Year", y="Financial_Loss_M", color="Attack_Type",
                     color_discrete_map=COLORS, barmode="stack",
                     labels={"Financial_Loss_M":"USD M","Year":""})
        fig.update_layout(legend=dict(orientation="h",y=-0.24,font_size=9,title=""),
                          xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(chart_cfg(fig), use_container_width=True)

    st.markdown('<div class="sh" style="--c:#3fb950">Evolución de incidentes año a año · dataset integrado</div>',
                unsafe_allow_html=True)
    line = dff.groupby(["Year","Attack_Type"]).size().reset_index(name="n")
    fig = px.line(line, x="Year", y="n", color="Attack_Type",
                  color_discrete_map=COLORS, markers=True,
                  labels={"n":"Incidentes","Year":""})
    fig.update_layout(legend=dict(orientation="h",y=-0.2,font_size=9,title=""),
                      xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
    st.plotly_chart(chart_cfg(fig, 230), use_container_width=True)

# ─── TAB 2 — Objetivo 1 ───────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div style="background:#3fb95015;border:1px solid #3fb95040;border-radius:6px;
         padding:8px 12px;margin-bottom:12px;">
      <span style="font-size:.62rem;font-weight:700;color:#3fb950;
            letter-spacing:.08em;text-transform:uppercase;">
        Objetivo 1 — Pipeline distribuido
      </span>
      <span style="font-size:.73rem;color:#8b949e;margin-left:8px;">
        Análisis geográfico y financiero sobre el dataset consolidado · columnas de T1
      </span>
    </div>
    """, unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="cl">Top 10 países por incidentes</div>', unsafe_allow_html=True)
        top_c = (dff.groupby("Country").size()
                 .reset_index(name="n").sort_values("n").tail(10))
        fig = px.bar(top_c, x="n", y="Country", orientation="h",
                     color="n", color_continuous_scale=["#161b22","#1f6feb"],
                     labels={"n":"Incidentes","Country":""})
        fig.update_layout(coloraxis_showscale=False, xaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(chart_cfg(fig, 300), use_container_width=True)

    with c4:
        st.markdown('<div class="cl">Pérdida financiera promedio por tipo (USD M)</div>',
                    unsafe_allow_html=True)
        avg = (dff.groupby("Attack_Type")["Financial_Loss_M"]
               .mean().reset_index().sort_values("Financial_Loss_M"))
        fig = px.bar(avg, x="Financial_Loss_M", y="Attack_Type", orientation="h",
                     color="Attack_Type", color_discrete_map=COLORS,
                     labels={"Financial_Loss_M":"USD M prom.","Attack_Type":""})
        fig.update_layout(showlegend=False, xaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(chart_cfg(fig, 300), use_container_width=True)

    st.markdown('<div class="sh" style="--c:#3fb950">Pérdida total por país — Top 15 (USD M)</div>',
                unsafe_allow_html=True)
    cl2 = (dff.groupby("Country")["Financial_Loss_M"]
           .sum().reset_index().sort_values("Financial_Loss_M", ascending=False).head(15))
    fig = px.bar(cl2, x="Country", y="Financial_Loss_M",
                 color="Financial_Loss_M",
                 color_continuous_scale=["#161b22","#ef5350"],
                 labels={"Financial_Loss_M":"USD M","Country":""})
    fig.update_layout(coloraxis_showscale=False, yaxis=dict(gridcolor="#21262d"))
    st.plotly_chart(chart_cfg(fig, 230), use_container_width=True)

# ─── TAB 3 — Objetivo 1 (T2 + T3) ────────────────────────────────────────────
with tab3:
    st.markdown("""
    <div style="background:#3fb95015;border:1px solid #3fb95040;border-radius:6px;
         padding:8px 12px;margin-bottom:12px;">
      <span style="font-size:.62rem;font-weight:700;color:#3fb950;
            letter-spacing:.08em;text-transform:uppercase;">
        Objetivo 1 — Pipeline distribuido
      </span>
      <span style="font-size:.73rem;color:#8b949e;margin-left:8px;">
        Métricas enriquecidas desde T2 (severidad) y T3 (datos comprometidos) tras el JOIN
      </span>
    </div>
    """, unsafe_allow_html=True)

    c5, c6 = st.columns(2)
    with c5:
        st.markdown('<div class="cl">Incidentes por industria objetivo · T1</div>',
                    unsafe_allow_html=True)
        ind = dff.groupby("Target_Industry").size().reset_index(name="n")
        fig = px.bar(ind.sort_values("n", ascending=False), x="Target_Industry", y="n",
                     color="n", color_continuous_scale=["#0d9488","#26a69a"],
                     labels={"n":"Incidentes","Target_Industry":""})
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(chart_cfg(fig, 300), use_container_width=True)

    with c6:
        st.markdown('<div class="cl">Severidad promedio por tipo · T2  (1=Low → 4=Critical)</div>',
                    unsafe_allow_html=True)
        sev = (dff.groupby("Attack_Type")["t2_avg_severity"]
               .mean().dropna().reset_index().sort_values("t2_avg_severity", ascending=False))
        fig = px.bar(sev, x="Attack_Type", y="t2_avg_severity",
                     color="Attack_Type", color_discrete_map=COLORS,
                     labels={"t2_avg_severity":"Severidad 1–4","Attack_Type":""})
        fig.update_layout(showlegend=False,
                          yaxis=dict(gridcolor="#21262d", range=[0,4]))
        st.plotly_chart(chart_cfg(fig, 300), use_container_width=True)

    st.markdown('<div class="sh" style="--c:#3fb950">Datos comprometidos promedio (GB) por tipo · T3</div>',
                unsafe_allow_html=True)
    t3 = (dff.groupby("Attack_Type")["t3_avg_data_GB"]
          .mean().dropna().reset_index().sort_values("t3_avg_data_GB", ascending=False))
    fig = px.bar(t3, x="Attack_Type", y="t3_avg_data_GB",
                 color="Attack_Type", color_discrete_map=COLORS,
                 labels={"t3_avg_data_GB":"GB prom.","Attack_Type":""})
    fig.update_layout(showlegend=False, yaxis=dict(gridcolor="#21262d"))
    st.plotly_chart(chart_cfg(fig, 230), use_container_width=True)

# ─── TAB 4 — Objetivo 2 + Feed vivo ──────────────────────────────────────────
with tab4:
    st.markdown("""
    <div style="background:#ab47bc15;border:1px solid #ab47bc40;border-radius:6px;
         padding:8px 12px;margin-bottom:12px;">
      <span style="font-size:.62rem;font-weight:700;color:#ab47bc;
            letter-spacing:.08em;text-transform:uppercase;">
        Objetivo 2 — Clasificación ML
      </span>
      <span style="font-size:.73rem;color:#8b949e;margin-left:8px;">
        Spark MLlib · 4 algoritmos · CrossValidator 3-fold · 33 features · 5 clases de ataque
      </span>
    </div>
    """, unsafe_allow_html=True)

    c7, c8 = st.columns([4, 6])
    with c7:
        st.markdown('<div class="cl">Métricas F1 / Accuracy por algoritmo</div>',
                    unsafe_allow_html=True)
        ml = pd.DataFrame({
            "Algoritmo": ["RandomForest","DecisionTree","MLP Neural","GBT binario"],
            "F1 Score":  [0.1949, 0.1949, 0.1867, 0.4989],
            "Accuracy":  [0.1962, 0.2014, 0.1934, 0.4993],
        })
        fig = go.Figure()
        fig.add_trace(go.Bar(name="F1 Score", x=ml["Algoritmo"], y=ml["F1 Score"],
                             marker_color="#42a5f5", width=0.35, offset=-0.2))
        fig.add_trace(go.Bar(name="Accuracy", x=ml["Algoritmo"], y=ml["Accuracy"],
                             marker_color="#26a69a", width=0.35, offset=0.2))
        fig.add_hline(y=0.20, line_dash="dot", line_color="#ef5350", line_width=1.5,
                      annotation_text="Bayes = 0.20 (1/K, K=5)",
                      annotation_font_color="#ef5350", annotation_font_size=9)
        fig.update_layout(barmode="overlay",
                          legend=dict(orientation="h",y=-0.28,font_size=9,title=""),
                          yaxis=dict(gridcolor="#21262d", range=[0,0.58]),
                          xaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(chart_cfg(fig, 290), use_container_width=True)
        st.caption("CrossValidator 3-fold · numTrees=[50,100] × maxDepth=[5,10] · 33 features (4 num + 6 OHE)")

    with c8:
        st.markdown('<div class="cl">Importancia relativa de features · RandomForest</div>',
                    unsafe_allow_html=True)
        feat = pd.DataFrame({
            "Feature": ["Financial_Loss_M","Incidents_Reported",
                        "t2_avg_severity","t3_avg_response_time",
                        "Country (OHE)","Protocol_Used (OHE)",
                        "Attack_Source (OHE)","Target_Industry (OHE)",
                        "Action_Taken (OHE)","Vuln_Type (OHE)"],
            "Imp":  [0.18,0.15,0.14,0.12,0.09,0.08,0.08,0.07,0.05,0.04],
            "Tipo": ["Numérica"]*4 + ["OHE (cat.)"]*6,
        })
        fig = px.bar(feat.sort_values("Imp"), x="Imp", y="Feature", orientation="h",
                     color="Tipo",
                     color_discrete_map={"Numérica":"#42a5f5","OHE (cat.)":"#ab47bc"},
                     labels={"Imp":"Importancia","Feature":""})
        fig.update_layout(legend=dict(orientation="h",y=-0.22,font_size=9,title=""),
                          xaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(chart_cfg(fig, 290), use_container_width=True)

    # ── Feed en vivo ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sh" style="--c:#ef5350">Feed en vivo · event_generator.py (proceso continuo)</div>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div class="lbar">
        <div class="pulse"></div>
        <div class="lt">Eventos en tiempo real</div>
        <div class="lc">{len(liv):,} acumulados · ~1 evento / 1.5 seg · refresh 2 s</div>
    </div>
    """, unsafe_allow_html=True)

    if len(liv) > 0:
        recent = liv.sort_values("timestamp", ascending=False).head(15).copy()
        recent["timestamp"] = recent["timestamp"].dt.strftime("%H:%M:%S")
        def ca(v):
            c = COLORS.get(v,"#444")
            return f"background:{c}22;color:{c};font-weight:600"
        st.dataframe(recent.style.applymap(ca, subset=["attack_type"])
                     .format({"severity":"{:.0f}","data_GB":"{:.1f}"}),
                     use_container_width=True, height=280)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total acumulado", f"{len(liv):,}")
        m2.metric("Más frecuente",   liv["attack_type"].value_counts().index[0])
        m3.metric("Severidad prom.", f"{liv['severity'].mean():.1f}")
        m4.metric("Success rate",    f"{(liv['outcome']=='Success').mean()*100:.1f}%")
    else:
        st.info("Esperando eventos del generador...")

# ── datos Parquet expandible ──────────────────────────────────────────────────
with st.expander(f"Datos del Parquet · Objetivo 1  ({len(dff):,} filas filtradas · 22 columnas)"):
    cols_s = ["Country","Year","Attack_Type","Target_Industry",
              "Financial_Loss_M","Affected_Users",
              "t2_total_eventos","t2_avg_severity","t3_avg_data_GB"]
    st.dataframe(dff[cols_s].sort_values("Financial_Loss_M", ascending=False),
                 use_container_width=True, height=280)

st.markdown("""
<div class="foot">
  <span>Arquitectura de Big Data para la Resiliencia Informática · UPeU 2026-1</span>
  <span>Salazar Tocas · Calderon Camacho · Sauñe Fernandez</span>
</div>""", unsafe_allow_html=True)
