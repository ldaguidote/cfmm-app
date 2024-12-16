def count_levels(d):
    return max(count_levels(v) if isinstance(v,dict) else 0 for v in d.values()) + 1