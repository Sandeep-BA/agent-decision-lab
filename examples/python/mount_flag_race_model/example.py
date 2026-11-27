"""Where does a read-only flag land when a path is resolved twice? Author: Sandeep Belgavi.

A small in-memory model of the docker cp mount setup described in GHSA-vfmq-r373-x89f and fixed in
moby/moby PR 54279 (backport of 54278, Docker Engine 29.10.1). Directories are inodes, mounts attach a
source to an inode, and a container process may rename two directories between any two daemon steps.
  before-fix: bind the source on the target opened by file descriptor, then readlink the descriptor and
              remount read-only by that path string (a second resolution the container can redirect)
  after-fix:  bind the source on a stub in a daemon-private directory, make the stub read-only there,
              then move the finished mount onto the target opened by file descriptor
This models the ordering only; it does not call mount(2) and is not a Docker test.
"""
import json, sys


class FS:
    def __init__(self):
        self.next_id = 0
        self.children = {}   # inode -> {name: inode}
        self.mounts = {}     # inode -> list of mount dicts, last is visible
        self.root = self.mkdir_inode()

    def mkdir_inode(self):
        self.next_id += 1
        self.children[self.next_id] = {}
        return self.next_id

    def mkdir(self, path):
        cur = self.root
        for part in path.strip('/').split('/'):
            cur = self.visible(cur)
            if part not in self.children[cur]:
                self.children[cur][part] = self.mkdir_inode()
            cur = self.children[cur][part]
        return cur

    def visible(self, inode):
        """Crossing a mount point shows the mounted source's root inode."""
        ms = self.mounts.get(inode)
        return ms[-1]['root'] if ms else inode

    def resolve(self, path):
        cur = self.root
        for part in path.strip('/').split('/'):
            cur = self.children[self.visible(cur)][part]
        return cur

    def path_of(self, inode, cur=None, prefix=''):
        """Current path of a directory inode, as readlink on /proc/self/fd would report it after renames."""
        cur = self.root if cur is None else cur
        for name, child in self.children[self.visible(cur)].items():
            path = prefix + '/' + name
            if child == inode:
                return path
            found = self.path_of(inode, child, path)
            if found:
                return found
        return None

    def bind(self, source, source_root, target_inode, writable=True):
        m = {'source': source, 'root': source_root, 'writable': writable}
        self.mounts.setdefault(target_inode, []).append(m)
        return m

    def remount_readonly(self, target_inode):
        self.mounts[target_inode][-1]['writable'] = False
        return self.mounts[target_inode][-1]['source']

    def rename_swap(self, parent_path, a, b):
        parent = self.visible(self.resolve(parent_path))
        kids = self.children[parent]
        kids[a], kids[b] = kids[b], kids[a]


def container_setup():
    """The container's view: /vol is a writable bind, /vol/a/ro a decoy writable bind, /vol/b/ro must be read-only."""
    fs = FS()
    host_vol, host_decoy, host_ro = fs.mkdir_inode(), fs.mkdir_inode(), fs.mkdir_inode()
    fs.children[host_vol] = {'a': fs.mkdir_inode(), 'b': fs.mkdir_inode()}
    for d in ('a', 'b'):
        fs.children[fs.children[host_vol][d]]['ro'] = fs.mkdir_inode()
    vol = fs.mkdir('/vol')
    fs.bind('host:/srv/vol', host_vol, vol)
    fs.bind('host:/srv/decoy', host_decoy, fs.resolve('/vol/a/ro'))
    return fs, host_ro


def run(order, swap_after):
    """Apply the setup steps for the /vol/b/ro read-only bind; the container swaps a and b after step swap_after."""
    fs, host_ro = container_setup()
    steps, trace = [], []
    if order == 'before-fix':
        state = {}
        def open_target():
            state['fd'] = fs.resolve('/vol/b/ro'); trace.append('daemon opens /vol/b/ro by descriptor')
        def bind():
            state['m'] = fs.bind('host:/srv/ro', host_ro, state['fd']); trace.append('daemon binds host:/srv/ro on the descriptor')
        def readlink():
            state['path'] = fs.path_of(state['fd']); trace.append(f"daemon reads the path back from the descriptor: {state['path']}")
        def remount():
            target = fs.resolve(state['path']); src = fs.remount_readonly(target)
            trace.append(f'daemon remounts read-only by path; flag lands on {src}')
        steps = [open_target, bind, readlink, remount]
    else:
        state = {}
        stub = fs.mkdir_inode()  # daemon-private staging directory, not reachable from the container
        def stage():
            state['m'] = fs.bind('host:/srv/ro', host_ro, stub); trace.append('daemon binds host:/srv/ro on a private stub')
        def flags():
            src = fs.remount_readonly(stub); trace.append(f'daemon makes the stub read-only; flag lands on {src}')
        def open_target():
            state['fd'] = fs.resolve('/vol/b/ro'); trace.append('daemon opens /vol/b/ro by descriptor')
        def move():
            m = fs.mounts[stub].pop(); fs.mounts.setdefault(state['fd'], []).append(m)
            trace.append('daemon moves the finished mount onto the descriptor (MS_MOVE)')
        steps = [stage, flags, open_target, move]
    for i, step in enumerate(steps):
        step()
        if i == swap_after:
            fs.rename_swap('/vol', 'a', 'b'); trace.append('container swaps /vol/a and /vol/b')
    writable = sorted({m['source'] for ms in fs.mounts.values() for m in ms if m['writable']})
    return {'order': order, 'swap_after_step': swap_after, 'ro_source_writable': 'host:/srv/ro' in writable,
            'decoy_made_readonly': 'host:/srv/decoy' not in writable, 'trace': trace}


def main():
    results = [run(order, k) for order in ('before-fix', 'after-fix') for k in (-1, 0, 1, 2, 3)]
    summary = {o: [r['swap_after_step'] for r in results if r['order'] == o and r['ro_source_writable']] for o in ('before-fix', 'after-fix')}
    out = {'interleavings_where_read_only_source_stays_writable': summary, 'results': results}
    json.dump(out, sys.stdout, indent=2); print()
    return out


if __name__ == '__main__':
    main()
