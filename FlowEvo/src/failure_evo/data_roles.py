"""Host-reviewed provenance requirements for S1.2 independent confirmation."""
from .contracts import fingerprint

ROLES = ('discovery', 'design', 'gate', 'regression', 'test')
DIMENSIONS = ('problem_id', 'problem_family', 'source_lineage', 'generation_source')


def validate_data_roles(manifest):
    """Fail closed on unknown ancestry; different seeds/shards are insufficient.

    IDs are host-reviewed ancestry labels, not inferred from filenames. Historical
    audit material can develop candidates but cannot confirm them independently.
    """
    if set(manifest) != set(ROLES):
        raise ValueError('all five data roles required')
    seen = {name: {} for name in DIMENSIONS}
    shards = set()
    for role in ROLES:
        data = manifest[role]
        shard = data.get('shard_id')
        if not isinstance(shard, str) or not shard or shard in shards:
            raise ValueError('unique shard identity required')
        shards.add(shard)
        items = data.get('items')
        if not isinstance(items, list) or not items:
            raise ValueError('missing independent data: ' + role)
        groups = set()
        for item in items:
            if item.get('provenance_reviewed') is not True:
                raise ValueError('unreviewed provenance')
            if role in ('gate', 'regression', 'test') and item.get('development_exposed') is not False:
                raise ValueError('confirmation material already exposed or unknown')
            group = item.get('source_group')
            if not isinstance(group, str) or not group:
                raise ValueError('source group required')
            groups.add(group)
            for name in DIMENSIONS:
                value = item.get(name)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError('missing provenance: ' + name)
                owner = seen[name].setdefault(value, role)
                if owner != role:
                    raise ValueError('cross-role overlap: ' + name)
        if set(data.get('source_groups', [])) != groups:
            raise ValueError('source groups differ from reviewed items')
    return fingerprint(manifest)
