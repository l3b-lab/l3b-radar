"""
Radar Chile–Bolivia · Piloto en Streamlit
L3B · Logistic Living Lab · www.l3b.cl
Datos 100% simulados. Ejecutar:  streamlit run app.py
"""
import io
import json

import pandas as pd
import plotly.graph_objects as go
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
<div style="margin-left:auto"><span style="background:{ORANGE};color:white;font-weight:700;font-size:.8rem;padding:5px 12px;border-radius:14px;letter-spacing:.06em">MODO TEST</span></div></div>
<div class="l3b-note"><b>Piloto con datos simulados.</b> Naves, clientes, BL, sellos y contenedores son ficticios.
El radar cruza plano (BAPLIE), manifiesto, bookings, registro de terminal y listado de vacíos, y prioriza: no acusa. Versión de prueba de L3B.</div>
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

    st.header("Parámetros de la naviera")
    st.caption("Los define el equipo de seguridad de la línea.")
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
