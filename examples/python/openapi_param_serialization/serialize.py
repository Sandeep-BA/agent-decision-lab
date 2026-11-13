"""Serialize OpenAPI 3.1 parameters by style and explode.

Author: Sandeep Belgavi. Original implementation of the rules in OpenAPI 3.1.1
section 4.8.12 (Style Values and Style Examples). Values are percent-encoded
with RFC 3986 unreserved characters left as they are. Combinations the
specification marks n/a raise ValueError instead of guessing.
"""
from urllib.parse import quote

DEFAULT_STYLE = {"query": "form", "cookie": "form", "path": "simple", "header": "simple"}


def enc(v):
    if isinstance(v, bool):
        v = "true" if v else "false"
    return quote(str(v), safe="-._~")


def serialize(name, value, style=None, explode=None, location="query"):
    style = style or DEFAULT_STYLE[location]
    if explode is None:
        explode = style == "form"          # the spec's default: true only for form
    is_list, is_obj = isinstance(value, list), isinstance(value, dict)
    n = enc(name)
    if value is None:
        if style in ("spaceDelimited", "pipeDelimited", "deepObject"):
            raise ValueError("n/a: undefined value with " + style)
        return {"matrix": ";" + n, "label": ".", "simple": "", "form": n + "="}[style]
    if style in ("spaceDelimited", "pipeDelimited"):
        if explode or not (is_list or is_obj):
            raise ValueError(f"n/a: {style} with explode={explode} for this type")
        sep = "%20" if style == "spaceDelimited" else "%7C"
        parts = [enc(x) for x in value] if is_list else [p for k, v in value.items() for p in (enc(k), enc(v))]
        return n + "=" + sep.join(parts)
    if style == "deepObject":
        if not (explode and is_obj):
            raise ValueError("n/a: deepObject needs an object and explode=true")
        return "&".join(f"{n}%5B{enc(k)}%5D={enc(v)}" for k, v in value.items())
    if is_list:
        items = [enc(x) for x in value]
    elif is_obj:
        items = [(enc(k), enc(v)) for k, v in value.items()]
    else:
        items = None
    if style == "simple":
        if items is None:
            return enc(value)
        if is_obj:
            return ",".join(f"{k}={v}" if explode else f"{k},{v}" for k, v in items)
        return ",".join(items)
    if style == "label":
        if items is None:
            return "." + enc(value)
        if is_obj:
            return "." + (".".join(f"{k}={v}" for k, v in items) if explode else ",".join(f"{k},{v}" for k, v in items))
        return "." + ("." if explode else ",").join(items)
    if style == "matrix":
        if items is None:
            return f";{n}={enc(value)}"
        if is_obj:
            return "".join(f";{k}={v}" for k, v in items) if explode else f";{n}=" + ",".join(f"{k},{v}" for k, v in items)
        return "".join(f";{n}={x}" for x in items) if explode else f";{n}=" + ",".join(items)
    if style == "form":
        if items is None:
            return f"{n}={enc(value)}"
        if is_obj:
            return "&".join(f"{k}={v}" for k, v in items) if explode else f"{n}=" + ",".join(f"{k},{v}" for k, v in items)
        return "&".join(f"{n}={x}" for x in items) if explode else f"{n}=" + ",".join(items)
    raise ValueError("unknown style " + style)


def parse_form_exploded_object(query, properties):
    """What a server sees for form+explode objects: bare keys, no parameter name."""
    pairs = dict(p.split("=", 1) for p in query.split("&") if p)
    return {k: pairs[k] for k in properties if k in pairs}
