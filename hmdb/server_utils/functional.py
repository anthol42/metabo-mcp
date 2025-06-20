import re

def regexp(pattern, string):
    if string is None:
        return False
    return re.search(pattern, string) is not None

def escape_like_specials(s):
    return s.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")