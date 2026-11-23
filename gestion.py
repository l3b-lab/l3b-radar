"""
Radar Chile–Bolivia · Capa de gestión (demo)
L3B · Logistic Living Lab · www.l3b.cl

Registra qué se hizo con cada alerta: estado, responsable, fecha de coordinación
con Aduana y comentario, con historial de cambios.

En la demo la gestión vive en memoria del servidor (compartida entre usuarios
mientras la app esté arriba) y se precarga con una semana SIMULADA de trabajo.
En la implementación real esto va a una base de datos.
"""
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

ESTADOS = ["Nuevo", "En revisión MSC", "Coordinado con Aduana", "Cerrado · con hallazgo", "Cerrado · sin hallazgo"]
ABIERTOS = ESTADOS[:3]
CERRADOS = ESTADOS[3:]
COLOR_ESTADO = {"Nuevo": "#9AA5B1", "En revisión MSC": "#C98A00", "Coordinado con Aduana": "#2A78D6",
                "Cerrado · con hallazgo": "#C4382A", "Cerrado · sin hallazgo": "#2C8A4B"}

EQUIPOS = {"Equipo Norte": ["CLARI", "CLIQQ", "CLMJS"], "Equipo Centro": ["CLVAP", "CLSAI"],
           "Equipo Biobío": ["CLSVE", "CLLQN", "CLCNL"]}
EQUIPO_PUERTO = {p: e for e, ps in EQUIPOS.items() for p in ps}
SIN_ASIGNAR = "Sin asignar"

COMENTARIOS = {
    "En revisión MSC": ["Se pide aclaración a la agencia por la diferencia documental.",
                        "Revisando con Equipos el historial del contenedor.",
                        "Consulta enviada al cliente; esperando respaldo del llenado."],
    "Coordinado con Aduana": ["Coordinado con Aduana: rayos X antes del retiro.",
                              "Aduana programa aforo físico en el terminal.",
                              "Contenedor retenido hasta la revisión de Aduana."],
    "Cerrado · con hallazgo": ["Aforo confirma diferencia con lo declarado. Aduana sigue el caso.",
                               "Rayos X muestran carga no coincidente con el manifiesto. Caso en Aduana."],
    "Cerrado · sin hallazgo": ["Rayos X sin observaciones. La agencia corrigió el documento.",
                               "Diferencia explicada por error de digitación del BL; corregido.",
                               "Pesaje repetido dentro de tolerancia. Sin acción."],
}


def semana(hoy=None):
    """Los últimos 7 días hasta hoy: la 'semana' del escenario."""
    hoy = hoy or date.today()
    return hoy - timedelta(days=6), hoy


def _ts(d, rng):
    return datetime.combine(d, time(int(rng.integers(8, 19)), int(rng.choice([0, 10, 20, 30, 40, 50]))))


def simular(res, seed=44, hoy=None):
    """Precarga una semana de gestión ficticia sobre los rojos y amarillos del escenario."""
    rng = np.random.default_rng(seed + 1000)
    ini, fin = semana(hoy)
    g = {}
    alertas = res[res.semaforo != "Verde"].sort_values(["score", "contenedor"], ascending=[False, True])
    rojos = alertas[alertas.semaforo == "Rojo"].contenedor.tolist()
    amar = alertas[alertas.semaforo == "Amarillo"].contenedor.tolist()

    # Reparto de estados: los rojos casi todos trabajados (es lo que se le muestra a la gerencia),
    # los amarillos mayormente en cola.
    plan_r = (["Cerrado · con hallazgo"] * 2 + ["Cerrado · sin hallazgo"] + ["Coordinado con Aduana"] * 2
              + ["En revisión MSC"] * 2 + ["Nuevo"] * max(0, len(rojos) - 7))[:len(rojos)]
    rng.shuffle(plan_r)
    plan_a = [rng.choice(ESTADOS, p=[.55, .25, .02, .0, .18]) for _ in amar]

    puerto = res.set_index("contenedor").puerto_code.to_dict()
    for c, est in list(zip(rojos, plan_r)) + list(zip(amar, plan_a)):
        det = ini + timedelta(days=int(rng.integers(0, 5)))
        eq = EQUIPO_PUERTO.get(puerto.get(c), SIN_ASIGNAR)
        resp = SIN_ASIGNAR if est == "Nuevo" else eq
        hist = [dict(ts=_ts(det, rng), usuario="radar", estado="Nuevo", comentario="Alerta generada por el cruce de documentos.")]
        f_ad, d = None, det
        for paso in ESTADOS[1:ESTADOS.index(est) + 1] if est not in CERRADOS else (
                ["En revisión MSC"] + (["Coordinado con Aduana"] if est == "Cerrado · con hallazgo" or (c in set(rojos) and rng.random() < .6)
                                       else []) + [est]):
            d = min(fin, d + timedelta(days=int(rng.integers(0, 2))))
            if paso == "Coordinado con Aduana":
                f_ad = d
            hist.append(dict(ts=_ts(d, rng), usuario=resp, estado=paso, comentario=str(rng.choice(COMENTARIOS[paso]))))
        hist.sort(key=lambda h: h["ts"])
        g[c] = dict(estado=est, responsable=resp, fecha_aduana=f_ad, comentario=hist[-1]["comentario"] if est != "Nuevo" else "",
                    detectado=det, actualizado=hist[-1]["ts"], actualizado_por=hist[-1]["usuario"], historial=hist)
    return g


def registro(g, res, hoy=None):
    """Asegura una entrada 'Nuevo' para toda alerta que aún no tenga gestión."""
    hoy = hoy or date.today()
    for c in res.loc[res.semaforo != "Verde", "contenedor"]:
        if c not in g:
            g[c] = dict(estado="Nuevo", responsable=SIN_ASIGNAR, fecha_aduana=None, comentario="", detectado=hoy,
                        actualizado=datetime.combine(hoy, time(8, 0)), actualizado_por="radar",
                        historial=[dict(ts=datetime.combine(hoy, time(8, 0)), usuario="radar", estado="Nuevo",
                                        comentario="Alerta generada por el cruce de documentos.")])
    return g


def actualizar(g, contenedor, usuario, estado, responsable, fecha_aduana, comentario):
    e = g[contenedor]
    if estado == "Coordinado con Aduana" and fecha_aduana is None:
        fecha_aduana = date.today()
    ahora = datetime.now().replace(second=0, microsecond=0)
    cambios = []
    if estado != e["estado"]: cambios.append(f"{e['estado']} → {estado}")
    if responsable != e["responsable"]: cambios.append(f"responsable: {responsable}")
    if fecha_aduana != e["fecha_aduana"]: cambios.append(f"Aduana: {fecha_aduana:%d-%m}" if fecha_aduana else "sin fecha Aduana")
    if comentario.strip() and comentario.strip() != e["comentario"]: cambios.append("comentario")
    if not cambios:
        return False
    e.update(estado=estado, responsable=responsable, fecha_aduana=fecha_aduana, comentario=comentario.strip() or e["comentario"],
             actualizado=ahora, actualizado_por=usuario)
    e["historial"].append(dict(ts=ahora, usuario=usuario, estado=estado,
                               comentario=comentario.strip() or "(" + "; ".join(cambios) + ")"))
    return True


def tabla(g):
    """La gestión como DataFrame para cruzar con el resultado del motor."""
    cols = ["contenedor", "estado", "responsable", "fecha_aduana", "comentario", "detectado", "actualizado", "actualizado_por"]
    if not g:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame([{**{k: v for k, v in e.items() if k != "historial"}, "contenedor": c} for c, e in g.items()])[cols]
    df["fecha_aduana"] = pd.to_datetime(df["fecha_aduana"])
    df["detectado"] = pd.to_datetime(df["detectado"])
    return df


def resumen(t):
    """Números del reporte semanal sobre la tabla combinada (motor + gestión)."""
    r = t[t.semaforo == "Rojo"]
    cer = t[t.estado.isin(CERRADOS)]
    con = (cer.estado == "Cerrado · con hallazgo").sum()
    return dict(rojos=len(r), amarillos=int((t.semaforo == "Amarillo").sum()),
                coordinados=int(t.fecha_aduana.notna().sum()), coordinados_rojos=int(r.fecha_aduana.notna().sum()),
                en_revision=int((t.estado == "En revisión MSC").sum()), nuevos=int((t.estado == "Nuevo").sum()),
                cerrados=len(cer), con_hallazgo=int(con), sin_hallazgo=int(len(cer) - con),
                rojos_abiertos=int(r.estado.isin(ABIERTOS).sum()), rojos_sin_asignar=int((r.responsable == SIN_ASIGNAR).sum()),
                tasa_hallazgo=(con / len(cer) * 100) if len(cer) else None)
