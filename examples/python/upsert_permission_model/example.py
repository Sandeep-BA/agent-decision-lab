"""Which permission does a create-or-replace request need? Author: Sandeep Belgavi.

A behavioural model of the repository create handler described in Argo CD advisory GHSA-mfgm-4p7x-3ccr
and fix commit 5b88885b40 (v3.6.3): before the fix, a create request with upsert=true replaced an existing,
different repository after checking only the create permission; after the fix it goes through the update
handler. The second half audits a synthetic API table for the same create-or-replace gap.
Synthetic records for the fictional Belgavi's Book Store. Not Argo CD code; no server is contacted.
"""
import json, sys

FIELDS = ('url', 'project', 'username', 'password', 'proxy', 'insecure')
STORED = {'url': 'https://git.bookstore.test/catalog-deploy.git', 'project': 'catalog', 'username': 'deploy-bot',
          'password': '<stored secret>', 'proxy': '', 'insecure': False}


def decide(version, operation, upsert, existing, requested, grants):
    """Return (allowed, status, stored_after, trace). version is 'vulnerable' or 'patched'."""
    trace = []
    if operation == 'update':
        need = ['update'] if existing else []
        if existing is None:
            return False, 'NotFound', None, ['update of a repository that does not exist']
        if 'update' not in grants:
            return False, 'PermissionDenied', existing, ['update requires repositories, update on the stored and requested repository']
        return True, 'Updated', replace(requested), ['update allowed; fields left out of the request are cleared']
    if 'create' not in grants:
        return False, 'PermissionDenied', existing, ['create requires repositories, create']
    trace.append('create permission checked')
    if existing is None:
        return True, 'Created', replace(requested), trace + ['no stored repository with this URL and project; created']
    if replace(requested) == existing:
        return True, 'Unchanged', existing, trace + ['stored repository is identical; returned as is']
    if not upsert:
        return False, 'InvalidArgument', existing, trace + ['stored repository differs; the request must set upsert to replace it']
    if version == 'vulnerable':
        return True, 'Replaced', replace(requested), trace + ['upsert replaced the stored repository without checking update (GHSA-mfgm-4p7x-3ccr)']
    trace.append('upsert routed through the update handler')
    if 'update' not in grants:
        return False, 'PermissionDenied', existing, trace + ['update permission missing; stored repository left unchanged']
    return True, 'Replaced', replace(requested), trace + ['update permission present; replaced']


def replace(requested):
    """A replace writes the whole record: omitted fields become empty, not 'unchanged'."""
    return {f: requested.get(f, '' if f != 'insecure' else False) for f in FIELDS}


def cleared_fields(before, after):
    return sorted(f for f in FIELDS if before and before.get(f) not in ('', False) and after and after.get(f) in ('', False))


API = [
    {'route': 'POST /repositories', 'effect': 'create', 'can_replace_existing': False, 'checks': ['create']},
    {'route': 'POST /repositories?upsert=true', 'effect': 'create-or-replace', 'can_replace_existing': True, 'checks': ['create']},
    {'route': 'PUT /stores/{id}', 'effect': 'create-or-replace', 'can_replace_existing': True, 'checks': ['create']},
    {'route': 'PUT /price-lists/{id}', 'effect': 'create-or-replace', 'can_replace_existing': True, 'checks': ['create', 'update']},
    {'route': 'POST /imports (merge mode)', 'effect': 'insert-or-update', 'can_replace_existing': True, 'checks': ['import']},
    {'route': 'PATCH /stores/{id}', 'effect': 'update', 'can_replace_existing': True, 'checks': ['update']},
]


def audit(api):
    """Flag every route that can change an existing object without requiring the update permission."""
    return [{'route': r['route'], 'finding': 'replaces existing objects but does not require update'}
            for r in api if r['can_replace_existing'] and 'update' not in r['checks']]


def main():
    attacker = {'url': STORED['url'], 'project': 'catalog', 'proxy': 'http://proxy.attacker.test:3128', 'insecure': True}
    cases = []
    for version in ('vulnerable', 'patched'):
        for grants in (['create'], ['create', 'update']):
            ok, status, after, trace = decide(version, 'create', True, dict(STORED), attacker, set(grants))
            cases.append({'version': version, 'grants': grants, 'allowed': ok, 'status': status,
                          'cleared': cleared_fields(STORED, after), 'proxy_after': after['proxy'], 'trace': trace})
    no_upsert = decide('vulnerable', 'create', False, dict(STORED), attacker, {'create'})
    out = {'upsert_cases': cases, 'create_without_upsert': {'allowed': no_upsert[0], 'status': no_upsert[1]},
           'identical_create': decide('patched', 'create', True, dict(STORED), dict(STORED), {'create'})[1],
           'audit': audit(API)}
    json.dump(out, sys.stdout, indent=2); print()
    return out


if __name__ == '__main__':
    main()
