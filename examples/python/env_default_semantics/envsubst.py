"""Author: Sandeep Belgavi. ${VAR:-d}, ${VAR-d}, ${VAR:?msg}, ${VAR?msg}, ${VAR:+r}, ${VAR+r} as POSIX
sh and Docker Compose define them, plus the 'set means use it' variant that ignores the colon."""
import re

PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?)([-?+])([^}]*))?\}")


class MissingVariable(Exception):
    pass


def expand(text, env, colon_aware=True):
    def sub(m):
        name, colon, op, word = m.group(1), m.group(2), m.group(3), m.group(4)
        is_set = name in env
        value = env.get(name, "")
        usable = is_set and (value != "" if (colon and colon_aware) else True)
        if op is None:
            return value
        if op == "-":
            return value if usable else word
        if op == "?":
            if usable:
                return value
            raise MissingVariable(f"{name}: {word or 'parameter null or not set'}")
        if op == "+":
            return word if usable else ""
    return PATTERN.sub(sub, text)


CASES = [("unset", None), ("empty", ""), ("value", "https://catalog.example.test")]
FORMS = ["${API_BASE:-https://default.example.test}", "${API_BASE-https://default.example.test}", "${API_BASE:+set}", "${API_BASE+set}"]

if __name__ == "__main__":
    for label, val in CASES:
        env = {} if val is None else {"API_BASE": val}
        for f in FORMS:
            print(f"{label:6} {f:42} posix={expand(f, env)!r:34} ignore-colon={expand(f, env, colon_aware=False)!r}")
