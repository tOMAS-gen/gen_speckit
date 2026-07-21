#!/usr/bin/env python3
"""Esqueleto de CLI para clasificacion de modelos (feature 007).

T005: monta el esqueleto de linea de comandos, salida JSON y codigos de salida.
La logica de fetch/match/aplicacion se implementa en tareas posteriores (T009-T015).
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_HELPER = Path(__file__).resolve().parent / "platform_helper.py"
_spec = importlib.util.spec_from_file_location("_gen_platform", _HELPER)
_platform = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_platform)


def _global_path():
    """Ruta absoluta del almacen global de la maquina."""
    return str(_platform.user_config_dir() / "global.json")


def load_global_store(path):
    """Lee el almacen global de forma tolerante, sin abortar nunca.

    Devuelve un dict con:
      - data: dict minimo con version 1, mas planes/mapeos preservados cuando aplica.
      - estado: "ausente" | "valido" | "corrupto" | "version-desconocida"
    """
    base = {"data": {"version": 1}, "estado": "ausente"}
    p = Path(path)

    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return base
    except OSError as exc:
        print(f"Aviso: no se pudo leer el almacen global ({exc}); se ignorara.", file=sys.stderr)
        return {"data": {"version": 1}, "estado": "corrupto"}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(
            f"Aviso: el almacen global esta corrupto ({exc}); se ignorara sin sobrescribir.",
            file=sys.stderr,
        )
        return {"data": {"version": 1}, "estado": "corrupto"}

    if not isinstance(data, dict):
        print(
            "Aviso: el almacen global no es un objeto JSON; se ignorara sin sobrescribir.",
            file=sys.stderr,
        )
        return {"data": {"version": 1}, "estado": "corrupto"}

    if data.get("version") == 1:
        base["data"] = data
        base["estado"] = "valido"
        return base

    # Version de formato no reconocida: preservar datos declarados por el usuario.
    preservado = {"version": 1}
    if "planes" in data:
        preservado["planes"] = data["planes"]
    if "mapeos" in data:
        preservado["mapeos"] = data["mapeos"]
    print(
        "Aviso: el almacen global tiene una version de formato no reconocida; "
        "se preservaron los planes y mapeos declarados y se descarto el resto.",
        file=sys.stderr,
    )
    return {"data": preservado, "estado": "version-desconocida"}


# Claves que jamas pueden persistirse en el almacen de la maquina (FR-016):
# nada de rutas de proyecto, credenciales, tokens, comandos headless ni estado de cuota.
PROHIBIDAS = {
    "headless",
    "cuota",
    "cuota_desde",
    "cuota_reset",
    "ruta_proyecto",
    "credenciales",
    "token",
    "tokens",
}


def validar_sin_claves_prohibidas(data, _prefijo=""):
    """Recorre `data` recursivamente y devuelve las rutas de claves prohibidas.

    Devuelve una lista de rutas tipo "planes.claude.cuota"; vacia si el
    objeto es apto para persistirse en el almacen global.
    """
    encontradas = []
    if isinstance(data, dict):
        for clave, valor in data.items():
            ruta = f"{_prefijo}.{clave}" if _prefijo else str(clave)
            if isinstance(clave, str) and clave.lower() in PROHIBIDAS:
                encontradas.append(ruta)
            encontradas.extend(validar_sin_claves_prohibidas(valor, ruta))
    elif isinstance(data, list):
        for i, valor in enumerate(data):
            encontradas.extend(validar_sin_claves_prohibidas(valor, f"{_prefijo}[{i}]"))
    return encontradas


def save_global_store(path, data):
    """Escribe el almacen global de forma atomica, validando FR-016 antes.

    Si `data` contiene claves prohibidas no escribe nada: avisa por stderr
    y lanza ValueError para que quien llama decida como continuar.
    Se invocara desde la logica de aplicacion (T012/T019) cuando haya
    clasificacion nueva que persistir.
    """
    prohibidas = validar_sin_claves_prohibidas(data)
    if prohibidas:
        print(
            "Aviso: el almacen global no se escribio porque contiene claves "
            f"prohibidas (FR-016): {', '.join(prohibidas)}.",
            file=sys.stderr,
        )
        raise ValueError(
            f"claves prohibidas en el almacen global: {', '.join(prohibidas)}"
        )
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        _platform.write_json_atomic(path, data)
    except OSError as exc:
        print(
            f"Aviso: no se pudo escribir el almacen de la maquina ({exc}); "
            f"se continua trabajando solo con datos locales del proyecto.",
            file=sys.stderr,
        )


def get_catalog_classification(repo_root):
    """Devuelve el bloque "clasificacion" de .specify/clis-catalog.json (o {} si falta)."""
    path = Path(repo_root) / ".specify" / "clis-catalog.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    bloque = data.get("clasificacion") if isinstance(data, dict) else None
    return bloque if isinstance(bloque, dict) else {}


def fetch_dataset(categoria, catalogo_clasificacion):
    """Consulta el leaderboard en datasets-server para una categoria (contrato §2).

    GET sin cookies, sin credenciales y sin cuerpo (C4). URL, dataset, config,
    split y timeout salen del bloque "clasificacion" del catalogo, nunca del
    codigo. Devuelve el JSON parseado (dict con "rows": [{"row": {...}}]) o
    None ante cualquier fallo (timeout, error de red, HTTP distinto de 200,
    respuesta que no es JSON). No reintenta: quien llama decide como degradar
    (FR-018, se integra en T032).
    """
    try:
        base_url = catalogo_clasificacion["dataset_url"]
        params = urllib.parse.urlencode(
            {
                "dataset": catalogo_clasificacion["dataset"],
                # C1: NUNCA hardcodear "text" como config; debe venir siempre del catalogo.
                "config": catalogo_clasificacion["config"],
                "split": catalogo_clasificacion["split"],
                "where": f"\"category\"='{categoria}'",
                # C2: el orden se deriva de rating descendente, nunca de rank.
                "orderby": '"rating" DESC',
                "offset": 0,
                "length": 100,
            }
        )
        url = f"{base_url}?{params}"
        # C5: timeout obligatorio desde el catalogo; nunca colgarse.
        timeout = catalogo_clasificacion["timeout_s"]
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
    except (
        urllib.error.URLError,
        socket.timeout,
        json.JSONDecodeError,
        KeyError,
        OSError,
        ValueError,
    ):
        return None
    return data if isinstance(data, dict) else None


def normalize_rows(dataset_response, votos_minimos):
    """Normaliza la respuesta de la datasets-server API a filas limpias (contrato §2).

    Descarta filas sin los cuatro campos obligatorios (model_name, organization,
    rating, leaderboard_publish_date) y las que no llegan a `votos_minimos` votos
    (C6, FR-019a). Devuelve una lista ordenada por rating descendente (C2); el
    rank del dataset solo se conserva como referencia en "rank_dataset" (C3
    aporta la fecha via leaderboard_publish_date). Nunca lanza excepcion:
    entrada invalida => lista vacia.
    """
    if not isinstance(dataset_response, dict):
        return []
    rows = dataset_response.get("rows")
    if not isinstance(rows, list):
        return []

    obligatorios = ("model_name", "organization", "rating", "leaderboard_publish_date")
    normalizadas = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        row = item.get("row")
        if not isinstance(row, dict):
            continue
        if any(campo not in row or row[campo] is None for campo in obligatorios):
            continue
        # C6 / FR-019a: sin vote_count se trata como 0 y la fila se descarta.
        vote_count = row.get("vote_count") or 0
        if vote_count < votos_minimos:
            continue
        normalizadas.append(
            {
                "model_name": row["model_name"],
                "organization": row["organization"],
                "rating": row["rating"],
                "rank_dataset": row.get("rank"),
                "vote_count": vote_count,
                "leaderboard_publish_date": row["leaderboard_publish_date"],
                "categorias": {},
            }
        )

    # C2: ordenar SIEMPRE por rating descendente, nunca por el rank del dataset.
    return sorted(normalizadas, key=lambda fila: fila["rating"], reverse=True)


def match_models(modelos_inventario, entradas_leaderboard, alias):
    """Correspondencia inventario -> leaderboard (FR-003, FR-004a, contrato §5 inv. 5).

    La correspondencia automatica SOLO se aplica cuando es inequivoca:
      1. Si el `cli/modelo` esta en `alias` (catalogo, salida de escape
         declarativa), el match es la entrada cuyo model_name coincide
         EXACTAMENTE con alias[ref]. Si esa entrada no vino en esta consulta,
         el modelo queda "sin dato externo" (no ambiguo).
      2. Sin alias, se busca por CONTENCION simple: el nombre base (lo que
         sigue al prefijo "cli/", en minusculas) como substring del
         model_name en minusculas. Heuristica deliberadamente simple: para
         nombres genericos como "opus" o "sonnet" produce varios candidatos,
         y ese es el comportamiento buscado (se reportan como ambiguos).
      3. Cero candidatos => "sin dato externo".
      4. Un candidato => match resuelto inequivoco.
      5. Dos o mas => AMBIGUO. Esta PROHIBIDO elegir por similitud, rating o
         posicion; el caso se reporta para que el usuario decida.

    Devuelve (resueltos, ambiguos, sin_dato):
      - resueltos: dict {cli_modelo: entrada completa del leaderboard}.
      - ambiguos: lista de {"ref": cli_modelo, "candidatos": [model_name, ...]}.
      - sin_dato: lista de cli_modelo sin ninguna entrada correspondiente.
    """
    resueltos = {}
    ambiguos = []
    sin_dato = []

    por_nombre = {
        entrada["model_name"]: entrada
        for entrada in entradas_leaderboard
        if isinstance(entrada, dict) and "model_name" in entrada
    }

    for ref in modelos_inventario:
        if ref in alias:
            entrada = por_nombre.get(alias[ref])
            if entrada is not None:
                resueltos[ref] = entrada
            else:
                # El alias apunta a un model_name que no vino en esta consulta:
                # no hay match, pero tampoco es ambiguo.
                sin_dato.append(ref)
            continue

        base = ref.split("/", 1)[1] if "/" in ref else ref
        base = base.lower()
        candidatos = [
            entrada
            for entrada in entradas_leaderboard
            if isinstance(entrada, dict)
            and base in str(entrada.get("model_name", "")).lower()
        ]

        if not candidatos:
            sin_dato.append(ref)
        elif len(candidatos) == 1:
            resueltos[ref] = candidatos[0]
        else:
            ambiguos.append(
                {
                    "ref": ref,
                    "candidatos": [c["model_name"] for c in candidatos],
                }
            )

    return resueltos, ambiguos, sin_dato


def rating_a_capacidad(rating, escala):
    """Convierte un rating a capacidad usando la escala del catalogo.

    Aplica la formula: capacidad = clamp(1, 10, floor((rating - piso) / paso) + 1).
    Devuelve un entero entre 1 y 10 inclusive.
    """
    capacidad_cruda = math.floor((rating - escala["piso"]) / escala["paso"])
    capacidad = capacidad_cruda + 1
    return max(1, min(10, capacidad))


def fetch_categorias(categorias, catalogo_clasificacion):
    """Consulta el leaderboard para cada categoria solicitada.

    Recibe una lista de nombres de categoria ya deduplicados y el dict del
    catalogo de clasificacion. Para cada categoria consulta la fuente via
    `fetch_dataset` y, si la respuesta no es None, la normaliza con
    `normalize_rows` usando `votos_minimos` del catalogo (por defecto 500).

    Devuelve un dict {categoria: entradas_normalizadas}. Las categorias cuya
    consulta devolvio None se omiten silenciosamente.
    """
    if not isinstance(categorias, list):
        return {}
    votos_minimos = catalogo_clasificacion.get("votos_minimos", 500) if isinstance(catalogo_clasificacion, dict) else 500
    resultado = {}
    for categoria in categorias:
        if not isinstance(categoria, str) or not categoria:
            continue
        dataset = fetch_dataset(categoria, catalogo_clasificacion)
        if dataset is None:
            continue
        entradas = normalize_rows(dataset, votos_minimos)
        if entradas:
            resultado[categoria] = entradas
    return resultado


def calcular_fortalezas(model_name, entradas_por_categoria, escala):
    """Calcula las fortalezas por categoria para un modelo ya resuelto.

    Recibe el nombre publicado del modelo (por ejemplo "claude-fable-5"), el
    dict que mapea categoria -> lista de entradas normalizadas de esa categoria
    (salida de `fetch_categorias`), y la escala de conversion.

    Para cada categoria busca una entrada cuyo `model_name` coincida
    EXACTAMENTE con `model_name`; si la encuentra, convierte su rating a
    capacidad con `rating_a_capacidad`.

    Devuelve un dict {categoria: capacidad_entero} solo para las categorias
    donde el modelo aparecio. Si el modelo no esta en la lista de una categoria,
    esa categoria simplemente no figura en el resultado.
    """
    if not isinstance(entradas_por_categoria, dict):
        return {}
    if not isinstance(escala, dict):
        return {}
    fortalezas = {}
    for categoria, entradas in entradas_por_categoria.items():
        if not isinstance(entradas, list):
            continue
        entrada = next(
            (e for e in entradas if isinstance(e, dict) and e.get("model_name") == model_name),
            None,
        )
        if entrada is not None:
            fortalezas[categoria] = rating_a_capacidad(entrada["rating"], escala)
    return fortalezas


def aplicar_nivel_medido(modelo_actual, entrada_leaderboard, escala):
    """Aplica el nivel medido (o estimado) a un modelo del inventario.

    Devuelve un NUEVO dict con el modelo actualizado (no modifica el original).

    Si entrada_leaderboard es None:
      - Conserva la capacidad actual
      - Agrega "nivel_origen": "estimado" si no existe ya un "nivel_origen"
      - NUNCA pisa un "nivel_origen" existente que sea "manual"

    Si entrada_leaderboard no es None:
      - Calcula la nueva capacidad usando rating_a_capacidad()
      - Actualiza "capacidad" con el nuevo valor
      - Agrega "nivel_origen": "medido"
      - Agrega "clasificacion" con {"entrada": model_name, "rating": rating, "publicado": fecha}
    """
    modelo = dict(modelo_actual)

    if entrada_leaderboard is None:
        if "nivel_origen" not in modelo:
            modelo["nivel_origen"] = "estimado"
    else:
        capacidad_nueva = rating_a_capacidad(entrada_leaderboard["rating"], escala)
        modelo["capacidad"] = capacidad_nueva
        modelo["nivel_origen"] = "medido"
        modelo["clasificacion"] = {
            "entrada": entrada_leaderboard["model_name"],
            "rating": entrada_leaderboard["rating"],
            "publicado": entrada_leaderboard["leaderboard_publish_date"],
        }

    return modelo


def aplicar_clasificacion_al_inventario(inventario, catalogo_clasificacion, entradas_leaderboard):
    """Aplica la clasificacion del leaderboard al inventario completo de modelos.

    Recorre cada CLI y cada modelo dentro de `inventario["clis"]`, construye el
    ref "cli/modelo_id" y usa `match_models` para resolver correspondencias.
    Los modelos con match inequivoco reciben nivel "medido"; el resto conserva
    su nivel previo marcado como "estimado".

    La funcion NO muta el inventario original: devuelve una copia profunda con
    las listas de modelos actualizadas. La clave "asignacion" se copia sin
    modificaciones.

    Devuelve (inventario_actualizado, ambiguos).
    """
    if not isinstance(inventario, dict):
        raise TypeError("inventario debe ser un dict")
    if not isinstance(catalogo_clasificacion, dict):
        raise TypeError("catalogo_clasificacion debe ser un dict")

    inventario_actualizado = copy.deepcopy(inventario)
    clis = inventario_actualizado.get("clis", {})
    if not isinstance(clis, dict):
        return inventario_actualizado, []

    alias = catalogo_clasificacion.get("alias", {})
    escala = catalogo_clasificacion.get("escala", {})

    refs = []
    for cli, info in clis.items():
        if not isinstance(info, dict):
            continue
        for modelo in info.get("modelos", []):
            if isinstance(modelo, dict) and "id" in modelo:
                refs.append(f"{cli}/{modelo['id']}")

    resueltos, ambiguos, _sin_dato = match_models(refs, entradas_leaderboard, alias)

    for cli, info in clis.items():
        if not isinstance(info, dict):
            continue
        modelos_originales = info.get("modelos", [])
        modelos_actualizados = []
        for modelo in modelos_originales:
            if not isinstance(modelo, dict) or "id" not in modelo:
                modelos_actualizados.append(modelo)
                continue
            ref = f"{cli}/{modelo['id']}"
            entrada = resueltos.get(ref)
            modelos_actualizados.append(aplicar_nivel_medido(modelo, entrada, escala))
        info["modelos"] = modelos_actualizados

    return inventario_actualizado, ambiguos


def mapeos_previos_del_almacen(global_data):
    """Extrae el dict de mapeos confirmados del almacen global.

    `global_data` es el dict "data" devuelto por `load_global_store`, es decir,
    {"version": 1, "mapeos": {...}, ...}. Si no existe la clave "mapeos" o no
    es un dict, devuelve un dict vacio.
    """
    if not isinstance(global_data, dict):
        return {}
    mapeos = global_data.get("mapeos")
    return mapeos if isinstance(mapeos, dict) else {}


def resolver_ambiguos_con_mapeos_previos(ambiguos, mapeos_guardados, entradas_por_nombre):
    """Aplica mapeos previos confirmados por el usuario a los casos ambiguos.

    Para cada caso ambiguo, si su "ref" (cli/modelo) ya fue guardada por el
    usuario (modo "usuario" y con una entrada no nula) y esa entrada sigue
    presente en `entradas_por_nombre`, se resuelve directamente sin repreguntar.

    Devuelve (resueltos_desde_mapeos, ambiguos_restantes):
      - resueltos_desde_mapeos: dict {ref: entrada_completa}.
      - ambiguos_restantes: lista de ambiguos que aun necesitan confirmacion.
    """
    if not isinstance(ambiguos, list) or not isinstance(mapeos_guardados, dict):
        return {}, list(ambiguos) if isinstance(ambiguos, list) else []

    resueltos_desde_mapeos = {}
    ambiguos_restantes = []

    for caso in ambiguos:
        if not isinstance(caso, dict):
            continue
        ref = caso.get("ref")
        mapeo = mapeos_guardados.get(ref)

        resuelto = False
        if isinstance(mapeo, dict) and mapeo.get("modo") == "usuario":
            entrada_guardada = mapeo.get("entrada")
            if entrada_guardada is not None and entrada_guardada in entradas_por_nombre:
                resueltos_desde_mapeos[ref] = entradas_por_nombre[entrada_guardada]
                resuelto = True

        if not resuelto:
            ambiguos_restantes.append(caso)

    return resueltos_desde_mapeos, ambiguos_restantes


def guardar_mapeo_elegido(path_almacen, cli_modelo, model_name_elegido):
    """Persiste la eleccion del usuario para un mapeo ambiguo.

    Lee el almacen global, actualiza la clave "mapeos" para `cli_modelo` con
    {"entrada": model_name_elegido, "modo": "usuario", "confianza": "alta"},
    preservando el resto del almacen, y escribe atomicamente.

    Lanza ValueError si el resultado viola FR-016 (propagado desde
    save_global_store).
    """
    store = load_global_store(path_almacen)
    data = store["data"]

    if "mapeos" not in data or not isinstance(data["mapeos"], dict):
        data["mapeos"] = {}

    data["mapeos"][cli_modelo] = {
        "entrada": model_name_elegido,
        "modo": "usuario",
        "confianza": "alta",
    }

    save_global_store(path_almacen, data)


def guardar_snapshot_clasificacion(path_almacen, catalogo_clasificacion, entradas, via):
    """Persiste un snapshot del leaderboard en el almacen global de la maquina.

    Construye el snapshot segun el contrato E2 de data-model.md y lo guarda bajo
    la clave "clasificacion" del almacen global, preservando el resto del contenido
    (version, compartir, planes, mapeos, etc.).

    Parametros:
      - path_almacen: ruta del archivo global (por ejemplo _global_path()).
      - catalogo_clasificacion: dict del bloque "clasificacion" del catalogo.
      - entradas: lista de filas ya normalizadas (salida de normalize_rows).
      - via: "dataset" o "agente" segun el origen de los datos.

    No decide si guardar o no: quien llama evalua la condicion (por ejemplo,
    que "compartir" sea "si") antes de invocar esta funcion.
    """
    publicado = None
    if isinstance(entradas, list):
        for entrada in entradas:
            if isinstance(entrada, dict) and entrada.get("leaderboard_publish_date"):
                publicado = entrada["leaderboard_publish_date"]
                break

    snapshot = {
        "fuente": catalogo_clasificacion.get("dataset_url", "") if isinstance(catalogo_clasificacion, dict) else "",
        "via": via,
        "publicado": publicado,
        "obtenido": datetime.now(timezone.utc).isoformat(),
        "escala": catalogo_clasificacion.get("escala", {}) if isinstance(catalogo_clasificacion, dict) else {},
        "entradas": entradas if isinstance(entradas, list) else [],
    }

    store = load_global_store(path_almacen)
    data = store["data"]
    data["clasificacion"] = snapshot
    save_global_store(path_almacen, data)


def resolver_fuente_clasificacion(global_data, entradas_frescas_o_none):
    """Decide que snapshot de clasificacion usar segun la precedencia FR-012.

    Puramente de decision: no hace I/O; recibe los datos ya cargados.

    Parametros:
      - global_data: dict "data" devuelto por load_global_store (puede o no
        tener la clave "clasificacion").
      - entradas_frescas_o_none: entradas recien obtenidas en ESTA corrida si
        la consulta a la fuente fue exitosa, o None si no se pudo consultar
        (sin red, fuente caida, etc.).

    Devuelve {"fuente_ganadora": ..., "entradas": [...]} donde fuente_ganadora es:
      - "actual": se consulto la fuente con exito; ganan los datos frescos.
      - "global": sin consulta exitosa, pero el almacen de la maquina tiene un
        snapshot valido que se reutiliza.
      - "ninguna": sin red y sin nada guardado; entradas vacias.
    """
    if entradas_frescas_o_none is not None:
        return {"fuente_ganadora": "actual", "entradas": entradas_frescas_o_none}

    clasificacion = global_data.get("clasificacion") if isinstance(global_data, dict) else None
    if isinstance(clasificacion, dict) and isinstance(clasificacion.get("entradas"), list):
        return {"fuente_ganadora": "global", "entradas": clasificacion["entradas"]}

    return {"fuente_ganadora": "ninguna", "entradas": []}


def necesita_refresco(global_data, frescura_dias, forzar):
    """Decide si la clasificacion cacheada debe refrescarse (FR-019).

    Parametros:
      - global_data: dict "data" devuelto por load_global_store.
      - frescura_dias: umbral de antiguedad en dias (int/float).
      - forzar: True cuando el usuario paso --refrescar; ignora la frescura.

    Devuelve True si se deberia intentar consultar la fuente externa:
      - siempre que `forzar` sea True;
      - si no hay snapshot de clasificacion o no tiene fecha de obtencion;
      - si la fecha de obtencion tiene antiguedad MAYOR O IGUAL a `frescura_dias`;
      - si la fecha no se puede parsear (se trata como vencida).
    """
    if forzar:
        return True
    if not isinstance(global_data, dict):
        return True
    clasificacion = global_data.get("clasificacion")
    if not isinstance(clasificacion, dict):
        return True
    obtenido = clasificacion.get("obtenido")
    if obtenido is None:
        return True
    try:
        fecha_obtenido = datetime.fromisoformat(obtenido)
        antiguedad = (datetime.now(timezone.utc) - fecha_obtenido).days
        return antiguedad >= frescura_dias
    except (ValueError, TypeError):
        # Fecha malformada: tratar como vencida para no quedarse con dato dudoso.
        return True


def resolver_fuente_plan(global_data, cli, plan_local_o_none):
    """Decide que plan usar para un CLI segun la precedencia FR-012.

    Puramente de decision: no hace I/O; recibe los datos ya cargados.

    Parametros:
      - global_data: dict "data" devuelto por load_global_store.
      - cli: nombre del CLI (por ejemplo "claude").
      - plan_local_o_none: plan declarado en el .specify/models.json del
        proyecto para ese cli, o None si figura ausente/"desconocido".

    Devuelve {"fuente_ganadora": ..., "plan": ...} donde fuente_ganadora es:
      - "local": el proyecto ya declara un plan concreto; gana lo local.
      - "global": sin plan local, pero el almacen de la maquina tiene una
        entrada de plan para ese cli.
      - "ninguna": sin plan en ninguna fuente; plan "desconocido".
    """
    if plan_local_o_none is not None and plan_local_o_none != "desconocido":
        return {"fuente_ganadora": "local", "plan": plan_local_o_none}

    planes = global_data.get("planes") if isinstance(global_data, dict) else None
    if isinstance(planes, dict):
        entrada = planes.get(cli)
        if isinstance(entrada, dict) and "plan" in entrada:
            return {"fuente_ganadora": "global", "plan": entrada["plan"]}

    return {"fuente_ganadora": "ninguna", "plan": "desconocido"}


def planes_heredados(path_almacen, planes_locales):
    """Resuelve el plan efectivo de cada CLI usando el almacen global.

    Recibe la ruta del almacen de la maquina y un dict `planes_locales` de la
    forma {"claude": "Max 5x", "codex": "desconocido", "kimi": None}, donde
    "desconocido" o None indican que el proyecto no declara un plan concreto
    para ese CLI.

    Para cada cli en `planes_locales` consulta `resolver_fuente_plan` con el
    contenido del almacen global cargado via `load_global_store`.

    Devuelve un dict {cli: {"plan": valor_efectivo, "fuente": "local" |
    "global" | "ninguna"}} para cada cli.
    """
    store = load_global_store(path_almacen)
    global_data = store["data"]

    resultado = {}
    for cli, plan_local in planes_locales.items():
        resolucion = resolver_fuente_plan(global_data, cli, plan_local)
        resultado[cli] = {
            "plan": resolucion["plan"],
            "fuente": resolucion["fuente_ganadora"],
        }
    return resultado


def guardar_plan_corregido(path_almacen, cli, plan_nuevo):
    """Persiste una correccion o declaracion nueva de plan para un CLI.

    Lee el almacen global con `load_global_store`, crea la clave "planes" si
    no existe, actualiza (o agrega) la entrada del CLI con
    {"plan": plan_nuevo, "declarado": "YYYY-MM-DD"} y escribe atomicamente
    con `save_global_store`, preservando el resto del almacen.

    La fecha de declaracion se genera en UTC con
    `datetime.now(timezone.utc).date().isoformat()`.
    """
    store = load_global_store(path_almacen)
    data = store["data"]

    if "planes" not in data or not isinstance(data["planes"], dict):
        data["planes"] = {}

    data["planes"][cli] = {
        "plan": plan_nuevo,
        "declarado": datetime.now(timezone.utc).date().isoformat(),
    }

    save_global_store(path_almacen, data)


def build_summary(args, global_store, antiguedad_dias=None, fuente_ganadora=None, estado=None, motivo=None, via=None):
    """Arma el resumen de salida con el estado/motivo resuelto por la fuente."""
    global_data = global_store.get("data", {}) if isinstance(global_store, dict) else {}
    tiene_datos_utiles = (
        global_store.get("estado") in ("valido", "version-desconocida")
        and bool({"compartir", "clasificacion", "planes", "mapeos"}.intersection(global_data.keys()))
    )
    preguntar_global = (
        getattr(args, "global") is None
        and "compartir" not in global_data
    )
    summary = {
        "estado": estado if estado is not None else "omitida",
        "motivo": motivo if motivo else None,
        "via": via,
        "publicado": None,
        "obtenido": None,
        "global": {"usado": tiene_datos_utiles, "ruta": _global_path()},
        "modelos": {"medidos": 0, "estimados": 0, "ambiguos": 0},
        "ambiguos": [],
        "preguntar_global": preguntar_global,
    }
    if antiguedad_dias is not None:
        summary["antiguedad_dias"] = antiguedad_dias
    if fuente_ganadora is not None:
        summary["fuente_ganadora"] = fuente_ganadora
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description="Clasifica modelos por nivel desde fuente externa")
    ap.add_argument("--json", action="store_true", help="Imprime el resumen en JSON")
    ap.add_argument("--refrescar", action="store_true", help="Ignora la frescura y vuelve a consultar la fuente")
    ap.add_argument("--desde-agente", default=None, help="Camino de respaldo: lee filas ya obtenidas por el agente")
    ap.add_argument("--sin-red", action="store_true", help="Prohibe cualquier salida a la red")
    ap.add_argument("--global", choices=["si", "no"], default=None, help="Fija compartir sin preguntar")
    ap.add_argument("--olvidar-global", action="store_true", help="Borra el almacen de la maquina")
    ap.add_argument("--repo-root", default=None, help="Raiz del repositorio")
    args = ap.parse_args(argv)

    # Lectura tolerante del almacen global; nunca aborta por si sola.
    global_path = _global_path()
    global_store = load_global_store(global_path)
    if global_store["estado"] == "corrupto":
        print(
            "Aviso: el almacen global esta ilegible; se continuara sin el.",
            file=sys.stderr,
        )
    elif global_store["estado"] == "version-desconocida":
        print(
            "Aviso: el almacen global usa un formato desconocido; "
            "se conservaron planes/mapeos y se descarto la clasificacion anterior.",
            file=sys.stderr,
        )

    # Manejo explicito de --olvidar-global y --global (FR-015).
    if args.olvidar_global:
        try:
            os.remove(global_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(
                f"Aviso: no se pudo borrar el almacen global ({exc}); se continuara.",
                file=sys.stderr,
            )
        global_store = load_global_store(global_path)

    global_explicito = getattr(args, "global")
    if global_explicito in ("si", "no"):
        data = global_store["data"]
        data["compartir"] = global_explicito
        Path(global_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            save_global_store(global_path, data)
        except (OSError, ValueError):
            # save_global_store ya imprime el motivo por stderr en ValueError;
            # OSError (permisos, etc.) se ignora para no abortar la corrida.
            pass
        global_store = load_global_store(global_path)

    # Codigo de salida 3 reservado para "almacen global ilegible y no recuperable".

    # Decision de frescura (FR-019): ¿debemos intentar consultar la fuente externa?
    repo_root = args.repo_root or "."
    catalogo_clasificacion = get_catalog_classification(repo_root)
    frescura_dias = 7
    if isinstance(catalogo_clasificacion, dict):
        frescura_dias = catalogo_clasificacion.get("frescura_dias", 7)
    refrescar = necesita_refresco(global_store["data"], frescura_dias, args.refrescar)

    antiguedad_dias = None
    fuente_ganadora = None
    via_actual = None
    if not refrescar:
        resolucion = resolver_fuente_clasificacion(global_store["data"], None)
    else:
        entradas_frescas = None
        via_actual = None
        try:
            # FR-018: cualquier fallo de la fuente (incluyendo red, HTTP no-200
            # o JSON invalido) se absorbe y se degrada al almacen global.
            if args.desde_agente is not None:
                # Camino de respaldo: el agente principal ya obtuvo los datos.
                # Misma forma que la respuesta de la API: {"rows": [{"row": {...}}]}.
                contenido = json.loads(
                    Path(args.desde_agente).read_text(encoding="utf-8")
                )
                votos_minimos = catalogo_clasificacion.get("votos_minimos", 500)
                entradas_frescas = normalize_rows(contenido, votos_minimos)
                if entradas_frescas:
                    via_actual = "agente"
            elif not args.sin_red:
                datos = fetch_dataset("overall", catalogo_clasificacion)
                if datos is not None:
                    votos_minimos = catalogo_clasificacion.get("votos_minimos", 500)
                    entradas_frescas = normalize_rows(datos, votos_minimos)
                    if entradas_frescas:
                        via_actual = "dataset"

            if not entradas_frescas:
                # Lista vacia (0 filas utilizables) se trata igual que "sin datos":
                # degradar al almacen global en vez de declarar exito con nada.
                entradas_frescas = None
                via_actual = None

            if entradas_frescas is not None and global_store["data"].get("compartir") == "si":
                guardar_snapshot_clasificacion(
                    global_path,
                    catalogo_clasificacion,
                    entradas_frescas,
                    via_actual or "dataset",
                )
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            # Fallo del camino --desde-agente: degradar igual que fallo de red/API.
            print(
                f"Aviso: no se pudieron leer los datos entregados por el agente ({exc}); "
                "se usara el almacen global como respaldo si existe.",
                file=sys.stderr,
            )
            entradas_frescas = None
            via_actual = None
        except Exception as exc:
            # Salvaguarda de ultimo recurso: nunca abortar por un fallo inesperado.
            print(
                f"Aviso: fallo inesperado al consultar la fuente de clasificacion ({exc}); "
                "se usara el almacen global como respaldo si existe.",
                file=sys.stderr,
            )
            entradas_frescas = None
            via_actual = None
        resolucion = resolver_fuente_clasificacion(global_store["data"], entradas_frescas)

    fuente_ganadora = resolucion["fuente_ganadora"]
    if fuente_ganadora == "global":
        obtenido = global_store["data"].get("clasificacion", {}).get("obtenido")
        try:
            fecha_obtenido = datetime.fromisoformat(obtenido)
            antiguedad_dias = (datetime.now(timezone.utc) - fecha_obtenido).days
        except (ValueError, TypeError):
            antiguedad_dias = None

    if fuente_ganadora == "actual":
        estado_final = "actualizada"
        motivo_final = ""
    elif fuente_ganadora == "global":
        estado_final = "reutilizada"
        motivo_final = ""
    else:
        estado_final = "omitida"
        motivo_final = "sin-red" if args.sin_red else "fuente-invalida"

    summary = build_summary(
        args,
        global_store,
        antiguedad_dias=antiguedad_dias,
        fuente_ganadora=fuente_ganadora,
        estado=estado_final,
        motivo=motivo_final,
        via=via_actual,
    )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        if summary.get("motivo"):
            print(f"Clasificacion {summary['estado']} ({summary['motivo']}).")
        else:
            print(f"Clasificacion {summary['estado']}.")
        if summary.get("fuente_ganadora") == "global" and summary.get("antiguedad_dias") is not None:
            print(
                f"Usando clasificacion guardada ({summary['antiguedad_dias']} dias de antiguedad)."
            )
        print(
            f"Modelos: medidos={summary['modelos']['medidos']}, "
            f"estimados={summary['modelos']['estimados']}, "
            f"ambiguos={summary['modelos']['ambiguos']}."
        )
        print(f"Global: usado={summary['global']['usado']}, ruta={summary['global']['ruta']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
