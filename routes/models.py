CAMPOS = ("nombre", "categoria", "peso_toneladas", "descripcion")
EDITABLES = ("categoria", "peso_toneladas", "descripcion")


def _peso_valido(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


def validate_vehiculo(data, partial=False):
    """Valida el body. Retorna (clean, error); error None si OK."""
    if not isinstance(data, dict):
        return None, "cuerpo JSON inválido"
    if partial:
        clean = {k: v for k, v in data.items() if k in EDITABLES}
        if not clean:
            return None, "nada que actualizar (categoria, peso_toneladas, descripcion)"
    else:
        faltan = [k for k in CAMPOS if k not in data]
        if faltan:
            return None, f"faltan campos: {', '.join(faltan)}"
        clean = {k: data[k] for k in CAMPOS}
    for k in ("nombre", "categoria", "descripcion"):
        if k in clean and (not isinstance(clean[k], str) or not clean[k].strip()):
            return None, f"campo inválido: {k}"
    if "peso_toneladas" in clean and not _peso_valido(clean["peso_toneladas"]):
        return None, "campo inválido: peso_toneladas (número >= 0)"
    return clean, None
