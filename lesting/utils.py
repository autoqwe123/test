def format_map(obj, indent=0, new_line=False):
    if isinstance(obj, list):
        return ", ".join(obj) if obj else "Null"
    if isinstance(obj, dict):
        return ("\n" if new_line else "") + "\n".join((" " * indent) + "%s: %s" % (key, format_map(val, indent=indent + 4, new_line=True)) for key, val in obj.items()) if obj else "Null"
    return str(obj)