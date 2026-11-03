"""
Radar Chile–Bolivia · L3B Logistic Living Lab · www.l3b.cl
Motor del piloto: (1) genera documentos FICTICIOS de una semana de naves y
(2) los cruza entre sí para marcar contenedores calientes.

Todos los datos son simulados. Naves, clientes, BL, sellos y contenedores son inventados.
El motor recibe tablas con el mismo formato que tendrían los archivos reales
(plano BAPLIE, manifiesto, bookings, registro de terminal y listado de vacíos).
"""
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Catálogos
# ----------------------------------------------------------------------------
PUERTOS = [
    dict(code="CLARI", name="Arica", lat=-18.47, lon=-70.32, svc=["Alpaca"], vol=dict(imp=60, bimp=220, bexp=140, exp=30, vac=120)),
    dict(code="CLIQQ", name="Iquique", lat=-20.21, lon=-70.15, svc=["Alpaca", "Inca"], vol=dict(imp=180, bimp=120, bexp=40, exp=60, vac=50)),
    dict(code="CLMJS", name="Angamos", lat=-23.07, lon=-70.39, svc=["Inca"], vol=dict(imp=90, exp=120, vac=30)),
    dict(code="CLVAP", name="Valparaíso", lat=-33.03, lon=-71.63, svc=["Inca", "NWC–USA–SAWC"], vol=dict(imp=420, exp=360, vac=80)),
    dict(code="CLSAI", name="San Antonio", lat=-33.59, lon=-71.61, svc=["Andes Express", "Alpaca", "NWC–USA–SAWC"], vol=dict(imp=640, exp=580, vac=150)),
    dict(code="CLSVE", name="San Vicente", lat=-36.73, lon=-73.13, svc=["Inca", "Recalada vacíos"], vol=dict(imp=60, exp=280, vac=780)),
    dict(code="CLLQN", name="Lirquén", lat=-36.71, lon=-72.97, svc=["Andes Express"], vol=dict(imp=80, exp=260, vac=120)),
    dict(code="CLCNL", name="Coronel", lat=-37.03, lon=-73.16, svc=["Andes Express", "NWC–USA–SAWC"], vol=dict(imp=140, exp=300, vac=200)),
]
PN = {p["code"]: p["name"] for p in PUERTOS}

EXT = {
    "CNNGB": ("Ningbo", "Asia"), "CNSHA": ("Shanghái", "Asia"), "KRPUS": ("Busan", "Asia"), "HKHKG": ("Hong Kong", "Asia"), "CNNSA": ("Nansha", "Asia"),
    "NLRTM": ("Rotterdam", "Europa"), "BEANR": ("Amberes", "Europa"), "ESVLC": ("Valencia", "Europa"), "DEHAM": ("Hamburgo", "Europa"),
    "PTSIE": ("Sines", "Europa"), "GBLGP": ("London Gateway", "Europa"),
    "USNYC": ("Nueva York", "Norteamérica"), "USPHL": ("Filadelfia", "Norteamérica"), "USHOU": ("Houston", "Norteamérica"),
    "PECLL": ("Callao", "Sudamérica y Caribe"), "ECGYE": ("Guayaquil", "Sudamérica y Caribe"), "COBUN": ("Buenaventura", "Sudamérica y Caribe"),
    "BRSSZ": ("Santos", "Sudamérica y Caribe"), "DOCAU": ("Caucedo", "Sudamérica y Caribe"), "PAROD": ("Rodman", "Sudamérica y Caribe"),
}
REG = {}
for _c, (_n, _r) in EXT.items():
    REG.setdefault(_r, []).append(_c)

BOLIVIA = {"BOLPB": "La Paz", "BOSRZ": "Santa Cruz", "BOCBB": "Cochabamba", "BOORU": "Oruro"}
TARA = {"45G1": 3880, "22G1": 2200}
NAVES = {"Inca": ("MN L3B SIMULADA", "644S"), "Andes Express": ("MN L3B EXPRESS", "212N"), "Alpaca": ("MV AUSTRAL DEMO", "118S"),
         "NWC–USA–SAWC": ("MN L3B PACÍFICO", "077S"), "Recalada vacíos": ("MN L3B VACÍOS", "015E")}

MIX_IMP = {
    "CLARI": {"Asia": 70, "Sudamérica y Caribe": 22, "Norteamérica": 4, "Europa": 4}, "CLIQQ": {"Asia": 75, "Sudamérica y Caribe": 15, "Norteamérica": 5, "Europa": 5},
    "CLMJS": {"Asia": 60, "Sudamérica y Caribe": 25, "Norteamérica": 10, "Europa": 5}, "CLVAP": {"Europa": 42, "Sudamérica y Caribe": 30, "Asia": 18, "Norteamérica": 10},
    "CLSAI": {"Asia": 48, "Europa": 20, "Norteamérica": 16, "Sudamérica y Caribe": 16}, "CLSVE": {"Asia": 50, "Norteamérica": 30, "Sudamérica y Caribe": 20},
    "CLLQN": {"Asia": 70, "Sudamérica y Caribe": 30}, "CLCNL": {"Asia": 45, "Europa": 30, "Norteamérica": 15, "Sudamérica y Caribe": 10},
}
MIX_EXP = {"def": {"Asia": 50, "Europa": 30, "Norteamérica": 15, "Sudamérica y Caribe": 5}, "CLARI": {"Asia": 60, "Europa": 20, "Norteamérica": 20}}
MIX_VAC = {"CLSVE": {"Norteamérica": 70, "Sudamérica y Caribe": 30}, "def": {"Sudamérica y Caribe": 60, "Asia": 25, "Norteamérica": 15}}

MERC_IMP = {"Repuestos de maquinaria": (6000, 18000), "Neumáticos": (7500, 12500), "Electrodomésticos": (5000, 11000), "Productos químicos": (16000, 24000),
            "Alimentos envasados": (15000, 23000), "Vehículos y partes": (6000, 15000), "Textiles": (6000, 12000), "Materiales de construcción": (18000, 26000)}
MERC_EXP = {"Madera aserrada": (20000, 26000), "Celulosa": (22000, 26000), "Fruta fresca": (18000, 23000), "Vino embotellado": (18000, 22500),
            "Cátodos de cobre": (22000, 27000), "Harina de pescado": (20000, 25000), "Papel y cartón": (20000, 26000)}
MERC_BEXP = {"Concentrado de zinc": (22000, 27000), "Soya y derivados": (20000, 26000), "Castaña amazónica": (15000, 20000), "Madera boliviana": (18000, 24000)}
MERCANCIAS = {**MERC_IMP, **MERC_EXP, **MERC_BEXP}

DEPOSITOS_LINEA = ["Depósito MSC " + p["name"] for p in PUERTOS]

REGLAS = {
    "imo_plano_no_manif": dict(w=75, label="IMO en el plano, manifiesto sin IMO", docs="Plano vs manifiesto",
                               why="Dice A, lleva B: el plano trata la carga como peligrosa y el manifiesto como carga general."),
    "no_manifestado": dict(w=70, label="A bordo sin manifestar", docs="Plano vs manifiesto", why="Viene en la nave lleno pero ningún BL lo declara."),
    "vacio_pesado": dict(w=65, label="Vacío con peso sobre la tara", docs="Plano / listado de vacíos", why="Un vacío que pesa toneladas de más puede traer carga oculta."),
    "sello_distinto": dict(w=65, label="Sello distinto al declarado", docs="Manifiesto vs terminal",
                           why="El sello registrado en descarga o gate no coincide con el declarado: indicio de contenedor abierto después del llenado."),
    "bolivia_fuera_ruta": dict(w=40, label="Vacío a Bolivia descargado fuera de Arica", docs="Listado de vacíos vs plano",
                               why="El tránsito a Bolivia es por Arica. Un vacío para Bolivia que baja en otro puerto se sale de la ruta normal."),
    "peso_mercancia": dict(w=40, label="Peso no corresponde a la mercancía", docs="Manifiesto vs catálogo",
                           why="Dice A, lleva B: el peso declarado no calza con el rango normal de esa mercancía."),
    "sin_clausula_bo": dict(w=40, label="Tránsito a Bolivia sin cláusula en el BL", docs="Manifiesto",
                            why="Por Iquique, sin la cláusula 'Cargo in Transit to Bolivia' la carga queda como consumo chileno."),
    "lugar_llenado": dict(w=35, label="Llenado en un lugar distinto al declarado", docs="Booking vs terminal", why="Se llenó en otro sitio, no en la planta declarada."),
    "destino_cambiado": dict(w=35, label="Destino final cambiado a última hora", docs="Booking", why="El destino cambió poco antes del arribo o del cierre."),
    "peso_vgm": dict(w=35, label="VGM difiere del peso manifestado", docs="Plano vs manifiesto", why="El pesaje (VGM) no calza con el peso declarado más la tara."),
    "vacio_sin_origen": dict(w=30, label="Vacío sin origen conocido", docs="Listado de vacíos",
                             why="Embarcado en un hub de transbordo y sin puerto de origen (ORI): no se sabe dónde se cargó realmente."),
    "ultimo_lleno_riesgo": dict(w=30, label="Último viaje lleno desde puerto en lista roja", docs="Historial del equipo",
                                why="Su último viaje con carga salió de un puerto crítico. Los contenedores contaminados a veces vuelven vacíos."),
    "pod_distinto": dict(w=25, label="Puerto de descarga no coincide", docs="Plano vs manifiesto", why="Plano y manifiesto no coinciden en el puerto de descarga."),
    "origen_riesgo": dict(w=25, label="Puerto extranjero en lista roja", docs="Parámetro de seguridad",
                          why="Origen o destino marcado como crítico por seguridad. No acusa: sube la prioridad."),
    "deposito_externo": dict(w=20, label="Vacío a depósito externo", docs="Listado de vacíos",
                             why="El vacío no va a un depósito de la línea sino a uno de terceros: se pierde el control del equipo."),
    "cliente_nuevo": dict(w=20, label="Cliente sin historial", docs="Maestro de clientes", why="Primer embarque con la línea."),
    "combo_riesgo": dict(w=20, label="Cliente no recurrente y puerto en lista roja", docs="Combinación", why="La combinación pesa más que cada señal por separado."),
    "mod_tarde": dict(w=15, label="Documento modificado a última hora", docs="Manifiesto", why="Cambio a menos de la ventana definida antes del arribo o del cierre."),
    "bolivia_iquique": dict(w=10, label="Vacío a Bolivia por Iquique", docs="Listado de vacíos", why="Iquique se usa para Bolivia solo con cláusula de tránsito. Conviene confirmarla."),
    "cliente_ocasional": dict(w=10, label="Cliente ocasional", docs="Maestro de clientes", why="Pocos embarques en 24 meses."),
}
# Señales que por sí solas no son una inconsistencia documental
CONTEXTO = {"origen_riesgo", "cliente_nuevo", "cliente_ocasional", "combo_riesgo", "bolivia_iquique"}

PARAMS_DEF = dict(
    lista_roja=["ECGYE", "COBUN", "BEANR"], hubs=["DOCAU", "PAROD"], depositos_linea=DEPOSITOS_LINEA,
    umbral_amarillo=30, umbral_rojo=60, tol_vgm_pct=10.0, tol_vacio_kg=500, ventana_h=48, tol_mercancia_pct=10.0,
    pesos={k: v["w"] for k, v in REGLAS.items()},
)

FLUJOS = ["Importación", "Exportación", "Tránsito a Bolivia", "Exportación boliviana", "Vacío"]


def nombre_puerto(c):
    if c in PN: return PN[c]
    if c in EXT: return EXT[c][0]
    if c in BOLIVIA: return BOLIVIA[c]
    return c or "—"


# ISO 6346 dígito verificador
_LV, _v = {}, 10
for _ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    if _v % 11 == 0: _v += 1
    _LV[_ch] = _v; _v += 1


def _check_digit(s):
    t = sum((int(c) if c.isdigit() else _LV[c]) * (2 ** i) for i, c in enumerate(s[:10]))
    return t % 11 % 10


# ----------------------------------------------------------------------------
# 1. Generador de documentos ficticios
# ----------------------------------------------------------------------------
def generar(seed=44):
    rng = np.random.default_rng(seed)
    pick = lambda a: a[int(rng.integers(len(a)))]
    rint = lambda a, b: int(round(a + rng.random() * (b - a)))

    def wpick(d):
        ks = list(d); w = np.array([d[k] for k in ks], float)
        return ks[int(rng.choice(len(ks), p=w / w.sum()))]

    used = set()

    def mk_id():
        while True:
            b = pick(["MSCU", "MEDU", "MSDU", "MSNU", "MSMU"]) + f"{int(rng.integers(1_000_000)):06d}"
            if b not in used:
                used.add(b); return b + str(_check_digit(b))

    sello = lambda: "MSC" + f"{int(rng.integers(1_000_000, 9_999_999))}"

    # Maestro de clientes ficticios
    clientes = []
    for pref in ("CL", "BO"):
        for i in range(1, 61):
            u = rng.random()
            emb = rint(4, 40) if u < .72 else rint(1, 3) if u < .87 else 0
            clientes.append(dict(cliente_id=f"{pref}-{i:04d}", nombre=f"Cliente ficticio {pref}-{i:04d}", embarques_24m=emb))
    recurrentes = {c["cliente_id"] for c in clientes if c["embarques_24m"] >= 4}

    rows = []
    for p in PUERTOS:
        for fl, n in p["vol"].items():
            for _ in range(n):
                if fl in ("imp", "bimp"): reg = wpick(MIX_IMP[p["code"]])
                elif fl == "vac": reg = wpick(MIX_VAC.get(p["code"], MIX_VAC["def"]))
                else: reg = wpick(MIX_EXP.get(p["code"], MIX_EXP["def"]))
                fx = pick(REG[reg])
                merc = pick(list(MERC_IMP)) if fl in ("imp", "bimp") else pick(list(MERC_EXP)) if fl == "exp" else pick(list(MERC_BEXP)) if fl == "bexp" else None
                iso = "45G1" if rng.random() < .8 else "22G1"
                svc = "Recalada vacíos" if fl == "vac" and p["code"] == "CLSVE" else pick([s for s in p["svc"] if s != "Recalada vacíos"] or p["svc"])
                x = dict(id=mk_id(), port=p["code"], fl=fl, fx=fx, iso=iso, merc=merc, svc=svc,
                         cli=(("BO-" if fl in ("bimp", "bexp") else "CL-") + f"{rint(1, 60):04d}") if merc else "",
                         peso=rint(*MERCANCIAS[merc]) if merc else 0, s_decl=sello() if merc else "", imo_p="", imo_m="",
                         pod_m=None, vgm_extra=0, llen_reg=None, dest_orig=None, cambio_h=None, mod_h=None, clausula="SI", no_manif=False,
                         bo=pick(list(BOLIVIA)) if fl == "bimp" else None, bo_orig=pick(list(BOLIVIA)) if fl == "bexp" else None)
                x["s_reg"] = x["s_decl"]
                x["llen_decl"] = ("Planta " + x["cli"]) if fl in ("exp", "bexp") else ""
                if fl == "vac":
                    hub = fx in PARAMS_DEF["hubs"]
                    bo = (p["code"] == "CLARI" and rng.random() < .55) or (p["code"] == "CLIQQ" and rng.random() < .15)
                    x.update(emb=fx, ori=("" if rng.random() < .85 else pick(["PECLL", "COBUN", "ECGYE", "BRSSZ"])) if hub else fx,
                             fin=pick(list(BOLIVIA)) if bo else p["code"],
                             dep="Depósito MSC " + p["name"],
                             ult=pick(["ECGYE", "COBUN"]) if rng.random() < .04 else pick(["PECLL", "CNNGB", "USNYC", "NLRTM", "CLSAI"]),
                             peso_vac=TARA[iso] + rint(-150, 150))
                    if not bo and x["ori"] and x["ult"] not in ("ECGYE", "COBUN") and rng.random() < .02:
                        x["dep"] = "Depósito externo " + pick(["Los Andes", "Lo Aguirre", "Talcahuano Norte"])
                rows.append(x)

    def take(port, fl, cond=lambda z: True):
        c = [z for z in rows if z["port"] == port and z["fl"] == fl and not z.get("_tocado") and cond(z)]
        z = c[int(rng.integers(len(c)))]
        z["_tocado"] = True
        return z

    no_rojo = lambda z: z["fx"] not in PARAMS_DEF["lista_roja"]
    # --- Casos guionizados (los 8 calientes de la simulación) ---
    a1 = take("CLARI", "bimp"); a1.update(fx="ECGYE", cli="BO-0101", merc="Repuestos de maquinaria", peso=24060)            # peso no calza
    a2 = take("CLARI", "bimp", no_rojo); a2.update(fx="CNNGB", cli="BO-0013", merc="Alimentos envasados", imo_p="8/1760",     # IMO oculto
                                                   bo="BOSRZ", dest_orig="BOLPB", cambio_h=26)
    a3 = take("CLARI", "bimp"); a3.update(fx="COBUN", cli="BO-0052", merc="Electrodomésticos", mod_h=30)                    # sello
    a3["s_decl"], a3["s_reg"] = "MSC4471920", "MSC4471983"
    s1 = take("CLSVE", "exp", no_rojo); s1.update(fx="PTSIE", cli="CL-0057", merc="Madera aserrada")
    s1["s_decl"], s1["s_reg"] = "MSC8820417", "MSC8820956"
    s2 = take("CLSVE", "vac", no_rojo); s2.update(peso_vac=9840, ult="COBUN", ori=s2["ori"] or "PECLL")
    v1 = take("CLVAP", "vac"); v1.update(fx="DOCAU", emb="DOCAU", ori="", fin="BOSRZ", dep="Depósito externo Placilla", ult="PECLL")
    v2 = take("CLVAP", "vac"); v2.update(fx="PECLL", emb="PECLL", ori="ECGYE", fin="BOLPB", dep="Depósito externo Curauma", ult="ECGYE")
    c1 = take("CLCNL", "exp"); c1.update(fx="BEANR", cli="CL-0134", merc="Celulosa", llen_reg="Bodega Lota (tercero)")
    clientes += [dict(cliente_id="BO-0101", nombre="Cliente ficticio BO-0101", embarques_24m=0),
                 dict(cliente_id="BO-0013", nombre="Cliente ficticio BO-0013", embarques_24m=2),
                 dict(cliente_id="BO-0052", nombre="Cliente ficticio BO-0052", embarques_24m=1),
                 dict(cliente_id="CL-0057", nombre="Cliente ficticio CL-0057", embarques_24m=2),
                 dict(cliente_id="CL-0134", nombre="Cliente ficticio CL-0134", embarques_24m=0)]
    clientes = list({c["cliente_id"]: c for c in clientes}.values())
    for z in (a2, a3, s1, c1):  # peso coherente con la nueva mercancía declarada
        lo, hi = MERCANCIAS[z["merc"]]
        z["peso"] = rint(lo + (hi - lo) * .3, hi - (hi - lo) * .3)

    # --- Observaciones (amarillos y verdes) en clientes recurrentes y fuera de lista roja ---
    ok = lambda z: no_rojo(z) and z["cli"] in recurrentes
    obs = [("CLARI", "bimp", "vgm", 2), ("CLARI", "bexp", "mod", 2), ("CLIQQ", "bimp", "clausula", 2), ("CLIQQ", "imp", "vgm", 1),
           ("CLMJS", "imp", "pod", 1), ("CLVAP", "imp", "vgm", 2), ("CLVAP", "imp", "pod", 1), ("CLVAP", "exp", "mod", 2),
           ("CLSAI", "imp", "vgm", 3), ("CLSAI", "exp", "llenado", 1), ("CLSAI", "imp", "pod", 2), ("CLSVE", "exp", "vgm", 2),
           ("CLSVE", "exp", "mod", 1), ("CLLQN", "exp", "vgm", 2), ("CLCNL", "exp", "vgm", 2), ("CLCNL", "exp", "mod", 1)]
    for port, fl, k, n in obs:
        for _ in range(n):
            z = take(port, fl, ok)
            if k == "vgm": z["vgm_extra"] = int(z["peso"] * rng.uniform(.15, .22))
            elif k == "mod": z["mod_h"] = rint(20, 40)
            elif k == "pod": z["pod_m"] = pick([c for c in ("CLSAI", "CLVAP", "CLCNL") if c != port])
            elif k == "llenado": z["llen_reg"] = "Depósito de tercero San Antonio"
            elif k == "clausula": z["clausula"] = "NO"

    # --- Emitir documentos ---
    plano, manif, book, term, vac = [], [], [], [], []
    for i, x in enumerate(rows):
        nave, viaje = NAVES[x["svc"]]
        llena = x["fl"] != "vac"
        sale = x["fl"] in ("exp", "bexp")
        tara = TARA[x["iso"]]
        vgm = (x["peso"] + tara + int(rng.normal(0, x["peso"] * .006)) + x["vgm_extra"]) if llena else x["peso_vac"]
        pol, pod = (x["port"], x["fx"]) if sale else (x["fx"], x["port"])
        plano.append(dict(nave=nave, viaje=viaje, contenedor=x["id"], puerto_chile=x["port"], movimiento="Embarque" if sale else "Descarga",
                          pol=pol, pod=pod, lleno_vacio="F" if llena else "E", iso=x["iso"], vgm_kg=vgm, imo_clase=x["imo_p"]))
        if not llena:
            vac.append(dict(contenedor=x["id"], ORI=x["ori"], EMB=x["emb"], TRA="", DES=x["port"], FIN=x["fin"], deposito=x["dep"],
                            peso_kg=x["peso_vac"], tara_kg=tara, ultimo_lleno=x["ult"]))
            continue
        dest = x["bo"] if x["fl"] == "bimp" else x["port"] if x["fl"] == "imp" else x["fx"]
        if not x["no_manif"]:
            manif.append(dict(bl=f"MEDUL3B{100000 + i}", nave=nave, viaje=viaje, contenedor=x["id"], pol=pol, pod=x["pod_m"] or pod,
                              origen_carga=x["bo_orig"] or "", destino_final=dest, cliente_id=x["cli"], mercancia=x["merc"],
                              peso_bruto_kg=x["peso"], sello=x["s_decl"], imo_clase=x["imo_m"],
                              clausula_bolivia=x["clausula"] if x["fl"] in ("bimp", "bexp") else "",
                              modificado_h_antes=x["mod_h"]))
        book.append(dict(booking=f"BKL3B{200000 + i}", contenedor=x["id"], cliente_id=x["cli"], destino_final=dest,
                         destino_original=x["dest_orig"] or dest, cambio_destino_h_antes=x["cambio_h"], lugar_llenado_declarado=x["llen_decl"]))
        term.append(dict(contenedor=x["id"], puerto_chile=x["port"], evento="Gate-in" if sale else "Descarga", sello_registrado=x["s_reg"],
                         lugar_llenado_registrado=(x["llen_reg"] or x["llen_decl"]) if sale else ""))

    return dict(plano=pd.DataFrame(plano), manifiesto=pd.DataFrame(manif), bookings=pd.DataFrame(book),
                terminal=pd.DataFrame(term), vacios=pd.DataFrame(vac), clientes=pd.DataFrame(clientes))


DOCS = ["plano", "manifiesto", "bookings", "terminal", "vacios", "clientes"]
COLUMNAS = {k: list(v.columns) for k, v in generar(1).items()}


# ----------------------------------------------------------------------------
# 2. Motor de cruce
# ----------------------------------------------------------------------------
def _nm(c):
    n = nombre_puerto(c)
    return f"{n} ({c})" if c and n != c else (c or "—")


def _blank(v):
    return v is None or (isinstance(v, float) and np.isnan(v)) or str(v).strip() in ("", "nan", "None", "NaT")


def analizar(docs, params=None):
    P = {**PARAMS_DEF, **(params or {})}
    W = {**PARAMS_DEF["pesos"], **P.get("pesos", {})}
    roja, hubs, deps = set(P["lista_roja"]), set(P["hubs"]), set(P["depositos_linea"])
    pl = docs["plano"].copy()
    idx = lambda name: docs[name].drop_duplicates("contenedor").set_index("contenedor").to_dict("index") if len(docs[name]) else {}
    M, B, T, V = idx("manifiesto"), idx("bookings"), idx("terminal"), idx("vacios")
    CLI = docs["clientes"].set_index("cliente_id")["embarques_24m"].to_dict()

    out = []
    for r in pl.to_dict("records"):
        c = r["contenedor"]; m, b, t, v = M.get(c), B.get(c), T.get(c), V.get(c)
        hits = []
        add = lambda rid, det: hits.append(dict(id=rid, regla=REGLAS[rid]["label"], detalle=det, puntos=int(W[rid]), cruce=REGLAS[rid]["docs"]))
        llena = r["lleno_vacio"] == "F"
        sale = r["movimiento"] == "Embarque"
        ext = r["pod"] if sale else r["pol"]
        tipo_cli, cli, merc, dest = "", "", "", ""
        if llena:
            if m is None:
                add("no_manifestado", f"Plano: lleno, {int(r['vgm_kg']):,} kg · Manifiesto: sin BL".replace(",", "."))
                flujo = "Exportación" if sale else "Importación"
            else:
                cli, merc, dest = m["cliente_id"], m["mercancia"], m["destino_final"]
                if not _blank(m.get("origen_carga")) and str(m["origen_carga"]).startswith("BO"):
                    flujo = "Exportación boliviana"
                elif str(dest).startswith("BO") and not sale:
                    flujo = "Tránsito a Bolivia"
                else:
                    flujo = "Exportación" if sale else "Importación"
                if not _blank(r["imo_clase"]) and _blank(m.get("imo_clase")):
                    cl, un = (str(r["imo_clase"]).split("/") + [""])[:2]
                    add("imo_plano_no_manif", f"Plano: clase {cl} / ONU {un} · Manifiesto: \"{merc.lower()}\" sin IMO")
                pod_p = r["pod"]
                if m["pod"] != pod_p:
                    add("pod_distinto", f"Plano: {_nm(pod_p)} · Manifiesto: {_nm(m['pod'])}")
                tara = TARA.get(r["iso"], 3880)
                esperado = float(m["peso_bruto_kg"]) + tara
                dif = (float(r["vgm_kg"]) - esperado) / esperado * 100
                rng_m = MERCANCIAS.get(merc)
                tol_m = P["tol_mercancia_pct"] / 100
                fuera = rng_m and not (rng_m[0] * (1 - tol_m) <= float(m["peso_bruto_kg"]) <= rng_m[1] * (1 + tol_m))
                if fuera:
                    add("peso_mercancia", f"Declara {merc.lower()} (rango {rng_m[0]:,}–{rng_m[1]:,} kg) y el BL indica {int(m['peso_bruto_kg']):,} kg · VGM {int(r['vgm_kg']):,} kg".replace(",", "."))
                elif abs(dif) > P["tol_vgm_pct"]:
                    add("peso_vgm", f"VGM {int(r['vgm_kg']):,} kg vs. {int(m['peso_bruto_kg']):,} kg manifestados + tara {tara:,} kg ({dif:+.0f}%)".replace(",", "."))
                if t is not None and not _blank(m.get("sello")) and str(m["sello"]) != str(t.get("sello_registrado")):
                    add("sello_distinto", f"{'BL' if not sale else 'Declarado'} sello {m['sello']} · registrado en {t.get('evento', 'terminal').lower()} {t.get('sello_registrado')}")
                if not _blank(m.get("modificado_h_antes")) and float(m["modificado_h_antes"]) < P["ventana_h"]:
                    add("mod_tarde", f"Manifiesto modificado {int(m['modificado_h_antes'])} h antes del {'cierre' if sale else 'arribo'}")
                if flujo == "Tránsito a Bolivia" and r["puerto_chile"] == "CLIQQ" and str(m.get("clausula_bolivia")).upper() != "SI":
                    add("sin_clausula_bo", "Consignatario boliviano, BL sin la cláusula 'Cargo in Transit to Bolivia'")
            if b is not None:
                if b["destino_original"] != b["destino_final"] and not _blank(b.get("cambio_destino_h_antes")) and float(b["cambio_destino_h_antes"]) < P["ventana_h"]:
                    add("destino_cambiado", f"Destino final cambiado de {nombre_puerto(b['destino_original'])} a {nombre_puerto(b['destino_final'])} {int(b['cambio_destino_h_antes'])} h antes")
                if sale and t is not None and not _blank(b.get("lugar_llenado_declarado")) and b["lugar_llenado_declarado"] != t.get("lugar_llenado_registrado"):
                    add("lugar_llenado", f"Declarado: {b['lugar_llenado_declarado']} · registrado: {t.get('lugar_llenado_registrado')}")
            if ext in roja:
                add("origen_riesgo", f"{_nm(ext)} está en la lista roja")
            documental = any(h["id"] not in CONTEXTO for h in hits)
            if cli:
                n = CLI.get(cli, 0)
                tipo_cli = "recurrente" if n >= 4 else "ocasional" if n >= 1 else "nuevo"
                if documental:
                    if tipo_cli == "nuevo": add("cliente_nuevo", f"{cli}: primer embarque con la línea")
                    elif tipo_cli == "ocasional": add("cliente_ocasional", f"{cli}: {n} embarque(s) en 24 meses")
                    if ext in roja and tipo_cli != "recurrente": add("combo_riesgo", f"{cli} ({tipo_cli}) con {_nm(ext)}")
        else:
            flujo = "Vacío"
            peso = float(v["peso_kg"]) if v is not None else float(r["vgm_kg"])
            tara = float(v["tara_kg"]) if v is not None else TARA.get(r["iso"], 3880)
            if max(peso, float(r["vgm_kg"])) > tara + P["tol_vacio_kg"]:
                add("vacio_pesado", f"{int(max(peso, float(r['vgm_kg']))):,} kg declarado vacío (tara {int(tara):,} kg)".replace(",", "."))
            if v is not None:
                ori, emb, fin = ("" if _blank(v["ORI"]) else v["ORI"]), v["EMB"], v["FIN"]
                ext = ori or emb
                dest = fin
                if not ori and emb in hubs:
                    add("vacio_sin_origen", f"ORI sin dato · embarcado en {_nm(emb)}, hub de transbordo")
                rr = [z for z in dict.fromkeys([ori, emb]) if z and z in roja]
                if rr:
                    add("origen_riesgo", ", ".join(_nm(z) for z in rr) + " en lista roja")
                if not _blank(v.get("ultimo_lleno")) and v["ultimo_lleno"] in roja:
                    add("ultimo_lleno_riesgo", f"Último viaje lleno desde {_nm(v['ultimo_lleno'])}")
                if str(fin).startswith("BO"):
                    if r["puerto_chile"] == "CLIQQ":
                        add("bolivia_iquique", f"Destino {nombre_puerto(fin)} vía Iquique")
                    elif r["puerto_chile"] != "CLARI":
                        add("bolivia_fuera_ruta", f"Destino {nombre_puerto(fin)} (Bolivia) · descargado en {nombre_puerto(r['puerto_chile'])}, no en Arica")
                if not _blank(v.get("deposito")) and v["deposito"] not in deps:
                    add("deposito_externo", f"{v['deposito']} en vez de un depósito de la línea")
        hits.sort(key=lambda h: -h["puntos"])
        score = min(100, sum(h["puntos"] for h in hits))
        documental = any(h["id"] not in CONTEXTO for h in hits)
        if not documental:  # sin inconsistencia documental nunca pasa de verde
            score = min(score, P["umbral_amarillo"])
        sem = "Rojo" if score > P["umbral_rojo"] else "Amarillo" if score > P["umbral_amarillo"] else "Verde"
        out.append(dict(contenedor=c, puerto_code=r["puerto_chile"], puerto=nombre_puerto(r["puerto_chile"]), nave=r["nave"], viaje=r["viaje"],
                        flujo=flujo, ext=ext, ext_nombre=nombre_puerto(ext), region=EXT.get(ext, ("", "Otro"))[1],
                        cliente=cli, tipo_cliente=tipo_cli, mercancia=merc or ("Vacío" if not llena else "—"), destino=nombre_puerto(dest),
                        bolivia=flujo in ("Tránsito a Bolivia", "Exportación boliviana") or str(dest).startswith("BO") or str(dest) in BOLIVIA.values(),
                        score=int(score), semaforo=sem, alerta=documental or sem != "Verde",
                        motivo=" · ".join(h["regla"] for h in hits if h["puntos"] > 10) or ("—" if not hits else hits[0]["regla"]),
                        hits=hits, n_hits=len(hits)))
    return pd.DataFrame(out)


def ficha(docs, contenedor):
    """Compara campo a campo un contenedor en todos los documentos."""
    g = lambda name: docs[name][docs[name]["contenedor"] == contenedor].to_dict("records")
    p, m, b, t, v = [(g(n) or [{}])[0] for n in ("plano", "manifiesto", "bookings", "terminal", "vacios")]
    filas = [
        ("Nave / viaje", f"{p.get('nave', '')} {p.get('viaje', '')}", f"{m.get('nave', '')} {m.get('viaje', '')}" if m else "", "", "", ""),
        ("Lleno / vacío", p.get("lleno_vacio", ""), "Lleno" if m else "", "", "", "Vacío" if v else ""),
        ("Puerto de carga (POL)", _nm(p.get("pol")), _nm(m.get("pol")) if m else "", "", "", _nm(v.get("EMB")) if v else ""),
        ("Puerto de descarga (POD)", _nm(p.get("pod")), _nm(m.get("pod")) if m else "", "", t.get("puerto_chile", "") and _nm(t.get("puerto_chile")), _nm(v.get("DES")) if v else ""),
        ("Origen (ORI)", "", _nm(m.get("origen_carga")) if m and m.get("origen_carga") else "", "", "", _nm(v.get("ORI")) if v and v.get("ORI") else ("sin dato" if v else "")),
        ("Destino final", "", _nm(m.get("destino_final")) if m else "", _nm(b.get("destino_final")) if b else "", "", _nm(v.get("FIN")) if v else ""),
        ("Destino original", "", "", _nm(b.get("destino_original")) if b else "", "", ""),
        ("Cliente", "", m.get("cliente_id", ""), b.get("cliente_id", ""), "", ""),
        ("Mercancía", "", m.get("mercancia", ""), "", "", ""),
        ("Peso (kg)", f"VGM {int(p['vgm_kg']):,}".replace(",", ".") if p else "", f"{int(m['peso_bruto_kg']):,} + tara".replace(",", ".") if m else "", "", "",
         f"{int(v['peso_kg']):,} (tara {int(v['tara_kg']):,})".replace(",", ".") if v else ""),
        ("IMO", p.get("imo_clase") or "—", (m.get("imo_clase") or "—") if m else "", "", "", ""),
        ("Sello", "", m.get("sello", ""), "", t.get("sello_registrado", ""), ""),
        ("Lugar de llenado", "", "", b.get("lugar_llenado_declarado", ""), t.get("lugar_llenado_registrado", ""), ""),
        ("Depósito", "", "", "", "", v.get("deposito", "")),
        ("Último viaje lleno", "", "", "", "", _nm(v.get("ultimo_lleno")) if v else ""),
    ]
    df = pd.DataFrame(filas, columns=["Campo", "Plano (BAPLIE)", "Manifiesto", "Booking", "Terminal", "Listado de vacíos"])
    df = df[(df.iloc[:, 1:] != "").any(axis=1)]
    keep = ["Campo"] + [c for c in df.columns[1:] if (df[c] != "").any()]
    return df[keep].reset_index(drop=True)


def leer_excel(file):
    xl = pd.read_excel(file, sheet_name=None, dtype={"imo_clase": str, "ORI": str, "sello": str, "sello_registrado": str})
    faltan = [k for k in DOCS if k not in xl]
    if faltan:
        raise ValueError("Faltan hojas: " + ", ".join(faltan))
    for k in DOCS:
        miss = [c for c in COLUMNAS[k] if c not in xl[k].columns]
        if miss:
            raise ValueError(f"Hoja '{k}': faltan columnas {', '.join(miss)}")
        xl[k] = xl[k].fillna("") if k in ("vacios",) else xl[k]
    for col in ("imo_clase",):
        for k in ("plano", "manifiesto"):
            xl[k][col] = xl[k][col].fillna("").astype(str).replace("nan", "")
    return {k: xl[k] for k in DOCS}


if __name__ == "__main__":
    d = generar()
    res = analizar(d)
    print({k: len(v) for k, v in d.items()})
    print(res.flujo.value_counts().to_dict())
    print(res.semaforo.value_counts().to_dict())
    print(res[res.semaforo == "Rojo"][["puerto", "contenedor", "flujo", "ext_nombre", "destino", "score", "motivo"]].to_string())
