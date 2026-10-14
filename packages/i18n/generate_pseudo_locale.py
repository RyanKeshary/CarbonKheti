"""
Pseudo-Localization Generator for CarbonKheti.
Generates `qps-ploc.json` from `en.json`:
- Accents vowels (a->à, e->é, i->î, o->ô, u->û, etc.)
- Expands string length by ~40% to detect layout overflow at 360px viewport
- Wraps in bracket delimiters: [ !!! ... !!! ]
- Correctly parses and preserves ICU placeholders and complex plural expressions
"""

import json
import re
import os

ACCENT_MAP = {
    'a': 'à', 'A': 'Å',
    'b': 'ƀ', 'B': 'Ɓ',
    'c': 'ç', 'C': 'Ç',
    'd': 'đ', 'D': 'Ð',
    'e': 'é', 'E': 'É',
    'f': 'ƒ', 'F': 'Ƒ',
    'g': 'ğ', 'G': 'Ĝ',
    'h': 'ĥ', 'H': 'Ĥ',
    'i': 'î', 'I': 'Î',
    'j': 'ĵ', 'J': 'Ĵ',
    'k': 'ķ', 'K': 'Ķ',
    'l': 'ľ', 'L': 'Ľ',
    'm': 'ɱ', 'M': 'Ṁ',
    'n': 'ñ', 'N': 'Ñ',
    'o': 'ô', 'O': 'Ô',
    'p': 'þ', 'P': 'Þ',
    'q': 'ɋ', 'Q': 'Ǫ',
    'r': 'ř', 'R': 'Ř',
    's': 'š', 'S': 'Š',
    't': 'ţ', 'T': 'Ť',
    'u': 'û', 'U': 'Û',
    'v': 'ṽ', 'V': 'Ṽ',
    'w': 'ŵ', 'W': 'Ŵ',
    'x': 'ẋ', 'X': 'Ẋ',
    'y': 'ŷ', 'Y': 'Ŷ',
    'z': 'ž', 'Z': 'Ž'
}

def accent_word(text: str) -> str:
    transformed = "".join(ACCENT_MAP.get(c, c) for c in text)
    padding_len = max(1, int(len(transformed) * 0.4))
    return transformed + " " + ("~" * padding_len)

def pseudo_localize_string(s: str) -> str:
    # If the string contains an ICU plural construct, transform only the inner message text
    if "plural" in s and s.startswith("{") and s.endswith("}"):
        def replace_clause(match):
            clause_name = match.group(1)
            clause_content = match.group(2)
            transformed_content = "".join(ACCENT_MAP.get(c, c) for c in clause_content)
            padding = " " + ("~" * max(1, int(len(transformed_content) * 0.4)))
            return f"{clause_name} {{{transformed_content}{padding}}}"

        # Match =0 {...}, =1 {...}, other {...}
        transformed = re.sub(r'(=?\w+)\s*\{([^}]+)\}', replace_clause, s)
        return transformed

    # Standard string with simple {variables}
    tokens = re.split(r'(\{[a-zA-Z0-9_]+\})', s)
    result_parts = []
    for token in tokens:
        if token.startswith('{') and token.endswith('}'):
            result_parts.append(token)
        elif token:
            result_parts.append(accent_word(token))

    return f"[ !!! {''.join(result_parts)} !!! ]"

def transform_dict(d: dict) -> dict:
    new_d = {}
    for k, v in d.items():
        if isinstance(v, dict):
            new_d[k] = transform_dict(v)
        elif isinstance(v, str):
            new_d[k] = pseudo_localize_string(v)
        else:
            new_d[k] = v
    return new_d

def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    en_path = os.path.join(dir_path, "locales", "en.json")
    out_path = os.path.join(dir_path, "locales", "qps-ploc.json")

    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    ploc_data = transform_dict(en_data)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(ploc_data, f, ensure_ascii=False, indent=2)

    print(f"Generated pseudo-localization at {out_path}")

if __name__ == "__main__":
    main()
