"""Write a result through a handle opened before untrusted work runs.

Author: Sandeep Belgavi. Original example. A tool step (standing in for code an
agent runs in a sandbox that can write to the same directory) replaces the
output pathname while the job is running. Two writers are compared:

  late_write   opens the pathname after the work and writes there
  bound_write  opens before the work, keeps the handle, checks that the pathname
               still names the same file, and refuses multiply linked files

Runs on the local filesystem in a temporary directory. Symlink swaps need extra
privileges on Windows, so the reproduction uses rename and hard links, which
need none; on Linux and macOS the same checks also catch a symlink swap.
"""
import os
import tempfile


class UnsafeOutput(Exception):
    pass


def same_file(a, b):
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


def open_bound(path):
    """Open (creating if needed) without following a final symlink where supported."""
    try:
        if os.path.islink(path):
            raise UnsafeOutput(f"{path} is a symbolic link")
    except OSError:
        pass
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    st = os.fstat(fd)
    if st.st_nlink > 1:
        os.close(fd)
        raise UnsafeOutput(f"{path} has {st.st_nlink} links")
    return fd, st


def bound_write(path, work, text):
    fd, opened = open_bound(path)
    try:
        work()
        try:
            now = os.stat(path, follow_symlinks=False)
        except FileNotFoundError:
            raise UnsafeOutput(f"{path} was removed while the work ran")
        if not same_file(now, opened):
            raise UnsafeOutput(f"{path} now names a different file")
        if os.fstat(fd).st_nlink > 1:
            raise UnsafeOutput(f"{path} gained a hard link while the work ran")
        os.ftruncate(fd, 0)
        os.write(fd, text.encode())
        return "written through the bound handle"
    finally:
        os.close(fd)


def late_write(path, work, text):
    work()
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return "written through the pathname"


def scenario(writer, attack, preplant=False):
    """Return what ended up where. `attack` runs as the untrusted work."""
    d = tempfile.mkdtemp(prefix="bound-output-")
    out = os.path.join(d, "result.md")
    precious = os.path.join(d, "store-settings.conf")
    with open(precious, "w", encoding="utf-8") as f:
        f.write("refund_limit=50\n")
    if preplant:
        os.link(precious, out)
    result = "ok"
    try:
        writer(out, lambda: attack(out, precious), "Summary for CASE-9050\n")
    except UnsafeOutput as e:
        result = f"refused: {e}"
    read = lambda p: open(p, encoding="utf-8").read() if os.path.exists(p) else None
    return {"result": result, "settings": read(precious), "result_file": read(out)}


def no_attack(out, precious):
    pass


ATTACK_NOTES = []


def relink_during_work(out, precious):
    """Replace the output name with a second name for the settings file while
    the job runs. Windows refuses to delete a file another handle has open
    (WinError 32), so against bound_write this attack fails there; on Linux
    the unlink succeeds and the identity check catches it."""
    try:
        if os.path.exists(out):
            os.remove(out)
        os.link(precious, out)
    except PermissionError as e:
        ATTACK_NOTES.append(f"attack failed: {e.strerror}")


def planted_before_start(out, precious):
    """Nothing happens during the job: the link was planted by an earlier run."""


ATTACKS = {"none": (no_attack, False), "relink during work": (relink_during_work, False),
           "link planted earlier": (planted_before_start, True)}

if __name__ == "__main__":
    for name, (attack, pre) in ATTACKS.items():
        for writer in (late_write, bound_write):
            ATTACK_NOTES.clear()
            r = scenario(writer, attack, pre)
            print(f"{name:21} {writer.__name__:12} settings={r['settings']!r:28} {r['result']} {ATTACK_NOTES}")
