"""
Radar Chile–Bolivia · Piloto en Streamlit
L3B · Logistic Living Lab · www.l3b.cl
Datos 100% simulados. Ejecutar:  streamlit run app.py
"""
import io
import json

import pandas as pd
import plotly.graph_objects as go
import hmac

import streamlit as st
import streamlit.components.v1 as components

import motor as M

st.set_page_config(page_title="Radar Chile–Bolivia · L3B", page_icon="🛰️", layout="wide")
components.html("<script>const d=window.parent.document.documentElement;d.lang='es';d.setAttribute('translate','no');d.classList.add('notranslate');</script>", height=0)

NAVY, ORANGE, GREY = "#0E1C34", "#F15A0F", "#5B6B78"
SEM = {"Verde": "#2C8A4B", "Amarillo": "#C98A00", "Rojo": "#C4382A"}
FLUJO_COL = {"Importación": "#2A78D6", "Exportación": "#EB6834", "Tránsito a Bolivia": "#1BAF7A", "Exportación boliviana": "#0F7A55", "Vacío": "#EDA100"}

LOGO = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="270 385 545 640" width="55" height="64" style="flex:none">
<rect x="280" y="487" width="525" height="37" fill="{ORANGE}"/><rect x="767" y="487" width="38" height="393" fill="{ORANGE}"/>
<rect x="499" y="664" width="306" height="38" fill="{ORANGE}"/><rect x="316" y="843" width="489" height="37" fill="{ORANGE}"/>
<rect x="499" y="395" width="41" height="618" fill="{NAVY}"/><rect x="499" y="972" width="291" height="41" fill="{NAVY}"/>
<circle cx="297" cy="505.5" r="15" fill="{NAVY}"/><circle cx="334" cy="861.5" r="15" fill="{NAVY}"/>
<circle cx="768" cy="993" r="14" fill="{ORANGE}"/><circle cx="519.5" cy="416" r="14" fill="{ORANGE}"/></svg>"""


# ---------------------------------------------------------------- acceso
LOGO_W = LOGO.replace(NAVY, "#FFFFFF").replace('width="55" height="64"', 'width="70" height="82"')


def usuarios():
    try:
        return {str(k).lower(): str(v) for k, v in st.secrets["usuarios"].items()}
    except Exception:
        return {}


def pantalla_acceso():
    st.markdown(f"""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], header {{display:none !important}}
.stApp {{background: radial-gradient(circle at 50% 25%, #18294a, {NAVY} 70%);}}
.block-container {{padding-top: 9vh; max-width: 480px;}}
.acc-badge {{position:fixed; top:22px; right:28px; background:{ORANGE}; color:#fff; font:700 12px Arial; letter-spacing:.06em; padding:5px 12px; border-radius:14px; z-index:10}}
.acc-brand {{display:flex; align-items:center; gap:16px; margin-bottom:22px}}
.acc-l3b {{font:700 34px Arial; color:#fff; line-height:1}} .acc-sub {{font:700 12px Arial; letter-spacing:.14em; color:{ORANGE}; margin-top:6px}}
.acc-line {{height:1px; background:#8A9AB0; width:190px; margin:7px 0 5px}} .acc-tag {{font:700 9px Arial; letter-spacing:.12em; color:#c9d2de}}
.acc-t {{color:#fff !important; font-size:1.6rem !important; font-weight:700; margin:0 !important}} .acc-s {{color:#a9b6c8; font-size:.9rem; margin:2px 0 4px}}
[data-testid="stForm"] {{background:#132442; border:1px solid #2a3d63; border-radius:14px; padding:30px 32px; box-shadow:0 20px 60px rgba(0,0,0,.45)}}
[data-testid="stForm"] label p {{color:#c9d2de !important}}
[data-testid="stForm"] input {{background:{NAVY} !important; color:#e6ebf2 !important}}
[data-testid="stForm"] [data-baseweb="input"] {{background:{NAVY} !important; border-color:#34486f !important}}
[data-testid="stForm"] button[kind="secondaryFormSubmit"], [data-testid="stForm"] button[kind="primaryFormSubmit"] {{background:{ORANGE}; color:#fff; border:none; width:100%; font-weight:700; height:44px}}
.acc-foot {{color:#7f8ea5; font-size:.78rem; text-align:center; margin-top:14px}}
</style>
<div class="acc-badge">DEMO</div>""", unsafe_allow_html=True)
    with st.form("acceso"):
        st.markdown(f"""<div class="acc-brand">{LOGO_W}<div><div class="acc-l3b">L3B</div><div class="acc-sub">LOGISTIC LIVING LAB</div>
<div class="acc-line"></div><div class="acc-tag">IA-OPS &amp; VENTURE BUILDER</div></div></div>
<p class="acc-t">Radar Chile–Bolivia</p><p class="acc-s">Acceso restringido · versión demo con datos simulados</p>""", unsafe_allow_html=True)
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        ok = st.form_submit_button("Ingresar", type="primary")
    st.markdown("<div class='acc-foot'>www.l3b.cl · ¿Sin acceso? Escribe a mrojo@l3b.cl</div>", unsafe_allow_html=True)
    if ok:
        users = usuarios()
        if not users:
            st.error("La app no tiene usuarios configurados (falta la sección [usuarios] en Secrets).")
        elif u.strip().lower() in users and hmac.compare_digest(p, users[u.strip().lower()]):
            st.session_state["usuario"] = u.strip().lower()
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


if not st.session_state.get("usuario"):
    pantalla_acceso()
    st.stop()

MSC_LOGO = "data:image/png;base64,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HA4HvLy88MILL+Dxxx9341qICAsXLlQ3ml6vx5///GdMmzYNoiiCiHDo0CFKS0uDIAjo378/goODWUxMDG3duhUHDhzAhQsXKDIykrm+GOXk2L59O/Ly8rBixYrL5so+deoUMjMz1d83b94c06ZNQ3BwMIqKimjx4sXqAoqIiGCPPPIIpaamwmKxYMuWLejVq5fbxmGMYcCAAYiMjMTx48fxySef4O23376iperuu+9m//nPf+jTTz9FTk4Ozp07hxMnTiApKQlLlizBBx98QI8//jhz/U1GRgYUtcC1msTz8/Px0EMPgYhUrtbf3x8PPvggDAYD+60qDIqLizF58mQ1A6aS/XLatGnw9vZmClfd0Ca5++67MWzYMCQlJWHevHno2rWr27swGo2w2Wwq5+/v78+ICG+++SaOHDmiclndu3fHunXrqFWrVqy+64CiAiAiNGvWTOUiXA9cIkJJSYn67GbNmsHHx8etzLu/v79qKVXmQ+HSevTogeDgYFy8eBGJiYnIzc2FwWBA37598csvvzT6Tj/99FN89tlnqsFDlmXcdddd6NGjB4qLi0nZ/4MGDYKXlxf7rbYfTp48iZ07d9KwYcNYfeZj2rRp+O6775CXl4eVK1eiT58+l3DjvxkqWFJSEu3atQu5ubmQJAnjxo1DbGyseshJ9X9011134eDBg0hOTsbFixcRFBSEu+66C+vWrUNjL/nee+9Fr169VG7G19cXer2eKS+2odPLZDK5nUqNZSi8lkyMOp0OTz/9NAIDA9XPevbseYnDYEJCAsLCwrB582bk5OTgq6++wt13343777/f7bkjR45Eq1atsGXLFuTn52PhwoWIjo7GI488AqfTiQ8++EC1Vu7ZswdnzpwhxYpVUlKC//73v/jrX/96iU6pZ8+ebMSIEbRu3TqsW7cO7du3b3CMyga677771O/1er2qW9q8eTOKiorAGIPD4cDf/vY3qqqqUsXO5ORkvP7665Bl2U3XEhgYiD//+c947rnncODAAWzfvv2KcyuKIsaNG8cGDRpEZ8+exZkzZ7BhwwZs2LAB5eXlmDNnDiZNmuTW99/EZwBAdnY25s2bd9X+QVqtFpGRkVAS4nXp0gUTJkzAwIED3URcSZIQGRkJxYLatWtX9borJZYTBAGzZs3CgQMHUFpaisTERLd16u3trXIHNTU1qK2thV6v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"

st.markdown(f"""
<style>
.block-container {{padding-top: 3.6rem;}}
.l3b-head {{display:flex; align-items:center; gap:18px; margin-bottom:.3rem}}
.l3b-head h1 {{margin:0; font-size:1.9rem; color:{NAVY}}}
.l3b-sub {{color:{ORANGE}; font-weight:700; letter-spacing:.08em; font-size:.78rem}}
.l3b-note {{background:#FFF4EC; border-left:4px solid {ORANGE}; padding:.5rem .8rem; border-radius:4px; font-size:.86rem; color:{NAVY}}}
.hit {{border:1px solid #E3E7EC; border-left:5px solid var(--c); border-radius:6px; padding:.5rem .7rem; margin-bottom:.45rem}}
.hit b {{color:{NAVY}}} .hit small {{color:{GREY}}}
.pill {{display:inline-block; padding:2px 10px; border-radius:12px; color:white; font-weight:700; font-size:.85rem}}
</style>
<div class="l3b-head">{LOGO}<div><p class="l3b-sub" style="margin:0">L3B · LOGISTIC LIVING LAB · WWW.L3B.CL</p>
<p style="margin:0;font-size:1.9rem;font-weight:700;color:{NAVY};line-height:1.2">Radar Chile–Bolivia</p></div>
<div style="margin-left:auto;text-align:center"><div style="font-size:.78rem;color:{GREY};margin-bottom:4px">👤 <b style="color:{NAVY}">{st.session_state["usuario"]}</b></div><div style="font-size:.7rem;letter-spacing:.12em;color:{GREY};font-weight:700">PROPUESTA PARA</div>
<img src="{MSC_LOGO}" alt="MSC" style="height:54px"></div></div>
<div class="l3b-note"><b>Piloto con datos simulados.</b> Naves, clientes, BL, sellos y contenedores son ficticios.
El radar cruza plano (BAPLIE), manifiesto, bookings, registro de terminal y listado de vacíos, y prioriza: no acusa. Demo de L3B: no es una herramienta oficial de MSC.</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- datos
@st.cache_data(show_spinner="Generando semana simulada…")
def docs_simulados(seed):
    return M.generar(seed)


@st.cache_data(show_spinner="Cruzando documentos…")
def correr(docs, params_json):
    return M.analizar(docs, json.loads(params_json))


def a_excel(dfs):
    b = io.BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        for k, v in dfs.items():
            v.to_excel(w, sheet_name=k[:31], index=False)
    return b.getvalue()


with st.sidebar:
    st.markdown(f"<div style='text-align:center'>{LOGO}</div>", unsafe_allow_html=True)
    if st.button(f"Salir ({st.session_state['usuario']})", use_container_width=True):
        st.session_state.pop("usuario", None)
        st.rerun()
    st.header("Datos")
    fuente = st.radio("Fuente", ["Semana simulada", "Subir Excel (6 hojas)"], label_visibility="collapsed")
    if fuente == "Semana simulada":
        seed = st.number_input("Semilla del escenario", 1, 9999, 44, help="44 = escenario de la presentación. Otro número = otra semana ficticia.")
        docs = docs_simulados(int(seed))
    else:
        up = st.file_uploader("Excel con hojas: " + ", ".join(M.DOCS), type=["xlsx"])
        if up is None:
            st.info("Descarga la plantilla (semana simulada), modifícala y súbela.")
            docs = docs_simulados(44)
        else:
            try:
                docs = M.leer_excel(up)
                st.success(f"{len(docs['plano']):,} contenedores leídos".replace(",", "."))
            except Exception as e:
                st.error(f"No pude leer el archivo: {e}")
                st.stop()
    st.download_button("⬇️ Plantilla / documentos simulados (.xlsx)", a_excel(docs), "L3B_radar_documentos_simulados.xlsx", width="stretch")

    st.header("Parámetros MSC")
    st.caption("Los define el equipo de seguridad de MSC.")
    ext_opts = sorted(M.EXT, key=lambda c: (M.EXT[c][1], M.EXT[c][0]))
    roja = st.multiselect("Lista roja (puertos extranjeros)", ext_opts, default=M.PARAMS_DEF["lista_roja"],
                          format_func=lambda c: f"{M.EXT[c][0]} ({c})")
    c1, c2 = st.columns(2)
    u_am = c1.number_input("Amarillo desde >", 0, 100, M.PARAMS_DEF["umbral_amarillo"])
    u_ro = c2.number_input("Rojo desde >", 0, 100, M.PARAMS_DEF["umbral_rojo"])
    tol_vgm = st.slider("Tolerancia VGM vs manifiesto (%)", 1, 30, int(M.PARAMS_DEF["tol_vgm_pct"]))
    tol_vac = st.slider("Tolerancia peso de vacío sobre tara (kg)", 100, 3000, M.PARAMS_DEF["tol_vacio_kg"], step=100)
    ventana = st.slider("Ventana de cambios de última hora (h)", 12, 96, M.PARAMS_DEF["ventana_h"], step=6)
    with st.expander("Puntos por regla"):
        pesos = {k: st.number_input(v["label"], 0, 100, v["w"], key="w_" + k) for k, v in M.REGLAS.items()}
    params = dict(lista_roja=roja, umbral_amarillo=u_am, umbral_rojo=u_ro, tol_vgm_pct=tol_vgm, tol_vacio_kg=tol_vac, ventana_h=ventana, pesos=pesos)

res = correr(docs, json.dumps(params, sort_keys=True))
COLS_ES = {"semaforo": "Semáforo", "puerto": "Puerto", "contenedor": "Contenedor", "flujo": "Flujo", "destino": "Destino", "cliente": "Cliente",
           "tipo_cliente": "Tipo cliente", "mercancia": "Mercancía", "deposito": "Depósito", "motivo": st.column_config.TextColumn("Por qué", width="large"),
           "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")}
fmt = lambda n: f"{int(n):,}".replace(",", ".")

# ---------------------------------------------------------------- KPIs
k = st.columns(6)
k[0].metric("Contenedores", fmt(len(res)))
k[1].metric("Importación", fmt((res.flujo == "Importación").sum()))
k[2].metric("Exportación", fmt((res.flujo == "Exportación").sum()))
k[3].metric("Bolivia (entran · salen)", f"{fmt((res.flujo == 'Tránsito a Bolivia').sum())} · {fmt((res.flujo == 'Exportación boliviana').sum())}")
k[4].metric("Vacíos", fmt((res.flujo == "Vacío").sum()))
nr, na = (res.semaforo == "Rojo").sum(), (res.semaforo == "Amarillo").sum()
k[5].metric("🔴 Calientes", fmt(nr), f"{fmt(na)} en amarillo", delta_color="off")

tabs = st.tabs(["🗺️ Panorama", "🇧🇴 Bolivia", "📦 Vacíos", "🔥 Lista caliente", "📄 Documentos", "⚙️ Reglas"])

# ---------------------------------------------------------------- Panorama
with tabs[0]:
    por = res.groupby("puerto_code").agg(n=("contenedor", "size"), rojos=("semaforo", lambda s: (s == "Rojo").sum()),
                                         amarillos=("semaforo", lambda s: (s == "Amarillo").sum())).reset_index()
    geo = pd.DataFrame(M.PUERTOS)[["code", "name", "lat", "lon"]].merge(por, left_on="code", right_on="puerto_code")
    geo["col"] = geo.apply(lambda r: SEM["Rojo"] if r.rojos else SEM["Amarillo"] if r.amarillos else SEM["Verde"], axis=1)
    BOC = {"BOLPB": (-16.50, -68.15), "BOSRZ": (-17.78, -63.18), "BOCBB": (-17.39, -66.16), "BOORU": (-17.97, -67.11)}
    fig = go.Figure()
    ar = geo[geo.code == "CLARI"].iloc[0]
    for c, (la, lo) in BOC.items():
        fig.add_trace(go.Scattergeo(lat=[ar.lat, la], lon=[ar.lon, lo], mode="lines", line=dict(width=2, color="#1BAF7A"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scattergeo(lat=[v[0] for v in BOC.values()], lon=[v[1] for v in BOC.values()], text=[M.BOLIVIA[c] for c in BOC],
                                mode="markers+text", textposition="middle right", marker=dict(size=9, color="#1BAF7A", symbol="diamond"),
                                hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scattergeo(lat=geo.lat, lon=geo.lon, mode="markers+text", textposition="middle left",
                                text=[f"{r['name']}  {'🔴' * int(r.rojos)}" for _, r in geo.iterrows()],
                                marker=dict(size=geo.n ** .5 * .9 + 6, color=geo.col, line=dict(width=1, color="white")),
                                customdata=geo[["n", "rojos", "amarillos"]],
                                hovertemplate="<b>%{text}</b><br>%{customdata[0]} contenedores<br>%{customdata[1]} rojos · %{customdata[2]} amarillos<extra></extra>",
                                showlegend=False))
    fig.update_geos(lataxis_range=[-39, -14], lonaxis_range=[-80, -60], showcountries=True, countrycolor="#B8C2CC", showland=True,
                    landcolor="#F4F6F8", showocean=True, oceancolor="#E8F1F8", showcoastlines=False, resolution=50)
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0))

    flujo_p = res.groupby(["puerto", "flujo"]).size().unstack(fill_value=0)
    orden = [p["name"] for p in M.PUERTOS]
    flujo_p = flujo_p.reindex(orden).fillna(0)
    bar = go.Figure()
    for f in M.FLUJOS:
        if f in flujo_p:
            bar.add_bar(y=flujo_p.index, x=flujo_p[f], name=f, orientation="h", marker_color=FLUJO_COL[f])
    bar.update_layout(barmode="stack", height=420, yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.15),
                      margin=dict(l=0, r=10, t=30, b=0), title="Contenedores por puerto y flujo", plot_bgcolor="white")
    a, b = st.columns([1, 1.25])
    a.plotly_chart(fig, use_container_width=True)
    with b:
        st.plotly_chart(bar, use_container_width=True)
        tab = por.assign(Puerto=por.puerto_code.map(M.PN)).set_index("Puerto").reindex(orden)[["n", "rojos", "amarillos"]]
        tab.columns = ["Contenedores", "Rojos", "Amarillos"]
        st.dataframe(tab, width="stretch")

# ---------------------------------------------------------------- Bolivia
with tabs[1]:
    bo = res[res.bolivia]
    vbo = bo[bo.flujo == "Vacío"]
    c = st.columns(4)
    c[0].metric("Tránsito a Bolivia (entran)", fmt((bo.flujo == "Tránsito a Bolivia").sum()))
    c[1].metric("Exportación boliviana (salen)", fmt((bo.flujo == "Exportación boliviana").sum()))
    c[2].metric("Vacíos con destino Bolivia", fmt(len(vbo)))
    c[3].metric("Vacíos fuera de ruta (no Arica/Iquique)", fmt((~vbo.puerto_code.isin(["CLARI", "CLIQQ"])).sum()))
    g = bo.groupby(["puerto", "flujo"]).size().unstack(fill_value=0)
    fb = go.Figure()
    for f in ["Tránsito a Bolivia", "Exportación boliviana", "Vacío"]:
        if f in g: fb.add_bar(x=g.index, y=g[f], name=f, marker_color=FLUJO_COL[f])
    fb.update_layout(barmode="group", height=360, title="Carga y vacíos de Bolivia por puerto chileno", plot_bgcolor="white", margin=dict(t=40, l=0, r=0, b=0))
    st.plotly_chart(fb, use_container_width=True)
    st.markdown("**Alertas relacionadas con Bolivia**")
    st.dataframe(bo[bo.semaforo != "Verde"].sort_values("score", ascending=False)[["semaforo", "score", "puerto", "contenedor", "flujo", "ext_nombre", "destino", "motivo"]],
                 width="stretch", hide_index=True,
                 column_config={**COLS_ES, "ext_nombre": "Puerto extranjero"})

# ---------------------------------------------------------------- Vacíos
with tabs[2]:
    va = res[res.flujo == "Vacío"].merge(docs["vacios"][["contenedor", "deposito", "FIN", "EMB"]], on="contenedor", how="left")
    deps = set(M.PARAMS_DEF["depositos_linea"])

    def destino_cat(r):
        if str(r.FIN).startswith("BO"):
            return "Bolivia vía Arica" if r.puerto_code == "CLARI" else "Bolivia vía Iquique" if r.puerto_code == "CLIQQ" else "Bolivia fuera de ruta"
        return "Depósito de la línea" if r.deposito in deps else "Depósito externo"

    va["dest_cat"] = va.apply(destino_cat, axis=1)
    va["emb_reg"] = va.EMB.map(lambda c: M.EXT.get(c, ("", "Otro"))[1])
    va["caliente"] = va.semaforo == "Rojo"
    regs = sorted(va.emb_reg.unique())
    ports = [p["name"] for p in M.PUERTOS if p["name"] in set(va.puerto)]
    dcat = ["Depósito de la línea", "Bolivia vía Arica", "Bolivia vía Iquique", "Depósito externo", "Bolivia fuera de ruta"]
    nodes = regs + ports + dcat
    ix = {n: i for i, n in enumerate(nodes)}
    s, t, v, col = [], [], [], []
    for (a_, b_, h), n in va.groupby(["emb_reg", "puerto", "caliente"]).size().items():
        s.append(ix[a_]); t.append(ix[b_]); v.append(n); col.append("rgba(196,56,42,.85)" if h else "rgba(237,161,0,.35)")
    for (a_, b_, h), n in va.groupby(["puerto", "dest_cat", "caliente"]).size().items():
        s.append(ix[a_]); t.append(ix[b_]); v.append(n); col.append("rgba(196,56,42,.85)" if h else "rgba(14,28,52,.18)")
    ncol = ["#5B6B78"] * len(regs) + [NAVY] * len(ports) + ["#2C8A4B", "#1BAF7A", "#C98A00", "#C4382A", "#C4382A"]
    sk = go.Figure(go.Sankey(node=dict(label=[f"{n} · {int(va[(va.emb_reg == n) | (va.puerto == n) | (va.dest_cat == n)].shape[0])}" for n in nodes],
                                       color=ncol, pad=14, thickness=16), textfont=dict(color=NAVY, size=12),
                             link=dict(source=s, target=t, value=v, color=col)))
    sk.update_layout(height=560, margin=dict(l=0, r=0, t=30, b=0), title="Vacíos: región de embarque → puerto chileno → destino (rojo = caliente)")
    st.plotly_chart(sk, use_container_width=True)
    st.markdown("**Vacíos con alertas**")
    st.dataframe(va[va.semaforo != "Verde"].sort_values("score", ascending=False)[["semaforo", "score", "puerto", "contenedor", "ext_nombre", "destino", "deposito", "motivo"]],
                 width="stretch", hide_index=True,
                 column_config={**COLS_ES, "ext_nombre": "Origen / embarque"})

# ---------------------------------------------------------------- Lista caliente
CAMPO_REGLA = {"sello_distinto": ["Sello"], "imo_plano_no_manif": ["IMO"], "pod_distinto": ["Puerto de descarga (POD)"], "peso_vgm": ["Peso (kg)"],
               "peso_mercancia": ["Peso (kg)", "Mercancía"], "lugar_llenado": ["Lugar de llenado"], "destino_cambiado": ["Destino final", "Destino original"],
               "vacio_pesado": ["Peso (kg)"], "vacio_sin_origen": ["Origen (ORI)"], "ultimo_lleno_riesgo": ["Último viaje lleno"],
               "bolivia_fuera_ruta": ["Destino final", "Puerto de descarga (POD)"], "deposito_externo": ["Depósito"], "no_manifestado": ["Lleno / vacío"]}
ACCION = {"Rojo": "Coordinar con Aduana la revisión del contenedor (rayos X o aforo) antes del retiro o del embarque.",
          "Amarillo": "Revisión documental con la agencia o el cliente; aclarar la diferencia antes del cierre.",
          "Verde": "Flujo normal. Sin acción."}
with tabs[3]:
    f1, f2, f3 = st.columns([1.2, 1.6, 1])
    sems = f1.multiselect("Semáforo", ["Rojo", "Amarillo", "Verde"], default=["Rojo", "Amarillo"])
    pts = f2.multiselect("Puertos", [p["name"] for p in M.PUERTOS], default=[], placeholder="Todos")
    fls = f3.multiselect("Flujo", M.FLUJOS, default=[], placeholder="Todos")
    hot = res[res.semaforo.isin(sems)]
    if pts: hot = hot[hot.puerto.isin(pts)]
    if fls: hot = hot[hot.flujo.isin(fls)]
    hot = hot.sort_values(["score", "puerto"], ascending=[False, True])
    cols = ["semaforo", "score", "puerto", "contenedor", "flujo", "ext_nombre", "destino", "cliente", "tipo_cliente", "mercancia", "motivo"]
    st.dataframe(hot[cols], width="stretch", hide_index=True, height=330,
                 column_config={**COLS_ES, "ext_nombre": "Puerto extranjero"})
    d1, d2, _ = st.columns([1, 1, 3])
    exp = hot[cols].rename(columns={"ext_nombre": "puerto_extranjero", "motivo": "por_que"})
    d1.download_button("⬇️ Lista para Aduana (.xlsx)", a_excel({"lista_caliente": exp}), "L3B_lista_caliente.xlsx")
    d2.download_button("⬇️ CSV", exp.to_csv(index=False).encode("utf-8-sig"), "L3B_lista_caliente.csv")

    st.subheader("Ficha del contenedor")
    if len(hot):
        sel = st.selectbox("Contenedor", hot.contenedor, format_func=lambda c: f"{c} · {hot.set_index('contenedor').loc[c, 'puerto']} · score {hot.set_index('contenedor').loc[c, 'score']}")
        x = res.set_index("contenedor").loc[sel]
        a, b = st.columns([1, 1.5])
        with a:
            st.markdown(f"<span class='pill' style='background:{SEM[x.semaforo]}'>{x.semaforo} · {x.score}</span> &nbsp; <b>{sel}</b><br>"
                        f"<small>{x.puerto} · {x.flujo} · {x.nave} {x.viaje}<br>{'Desde' if x.flujo != 'Exportación' else 'Hacia'} {x.ext_nombre} → {x.destino}</small>",
                        unsafe_allow_html=True)
            st.markdown("**Qué está mal y por qué importa**")
            for h in x.hits:
                c_ = SEM["Rojo"] if h["puntos"] >= 40 else SEM["Amarillo"] if h["puntos"] >= 20 else "#9AA5B1"
                st.markdown(f"<div class='hit' style='--c:{c_}'><b>+{h['puntos']} · {h['regla']}</b><br>{h['detalle']}<br>"
                            f"<small>Cruce: {h['cruce']} — {M.REGLAS[h['id']]['why']}</small></div>", unsafe_allow_html=True)
            if not x.hits: st.caption("Sin observaciones.")
            st.info("**Acción sugerida:** " + ACCION[x.semaforo])
        with b:
            st.markdown("**Cruce campo a campo** (en naranja, los campos que no calzan)")
            fi = M.ficha(docs, sel)
            marcar = {c for h in x.hits for c in CAMPO_REGLA.get(h["id"], [])}
            st.dataframe(fi.style.apply(lambda r: ["background-color:#FFE3D3" if r["Campo"] in marcar else "" for _ in r], axis=1),
                         width="stretch", hide_index=True, height=min(38 * len(fi) + 40, 600))
    else:
        st.caption("No hay contenedores con esos filtros.")

# ---------------------------------------------------------------- Documentos
QUIEN = {"plano": "Planners · BAPLIE de arribo y zarpe", "manifiesto": "Agencia · manifiesto EDI", "bookings": "Comercial · bookings",
         "terminal": "Terminal · registro de descarga y gate-in (sello, lugar de llenado)", "vacios": "Equipos · listado de vacíos (ORI, EMB, TRA, DES, FIN)",
         "clientes": "Comercial · maestro de clientes (embarques en 24 meses)"}
with tabs[4]:
    doc = st.radio("Documento", M.DOCS, horizontal=True, format_func=lambda k: k.capitalize())
    st.caption(f"Entrega: {QUIEN[doc]} · {fmt(len(docs[doc]))} filas")
    st.dataframe(docs[doc], width="stretch", hide_index=True, height=480)

# ---------------------------------------------------------------- Reglas
with tabs[5]:
    rg = pd.DataFrame([dict(Regla=v["label"], Puntos=params["pesos"][k], Cruce=v["docs"], Disparos=int(sum(any(h["id"] == k for h in hs) for hs in res.hits)),
                            Por_qué=v["why"]) for k, v in M.REGLAS.items()]).sort_values("Puntos", ascending=False)
    st.dataframe(rg, width="stretch", hide_index=True, height=560, column_config={"Por_qué": st.column_config.TextColumn("Por qué", width="large")})
    st.caption(f"Semáforo: verde ≤ {u_am} · amarillo {u_am + 1}–{u_ro} · rojo > {u_ro}. "
               "Venir de un puerto en lista roja o el perfil del cliente nunca dejan rojo por sí solos: debe existir una inconsistencia documental.")

st.markdown(f"<hr><center><small style='color:{GREY}'>L3B · Logistic Living Lab · www.l3b.cl · Piloto con datos ficticios</small></center>", unsafe_allow_html=True)
