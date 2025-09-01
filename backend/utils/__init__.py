# Utility functions and constants for agent tools
import re


def remove_square_brackets(text: str) -> str:
    out = []
    depth = 0
    need_space = False

    for i, ch in enumerate(text):
        if ch == '[':
            if depth == 0:
                left = out[-1] if out else ''
                right = text[i + 1] if i + 1 < len(text) else ''
                need_space = left.isalnum() and right.isalnum()
            depth += 1
        elif ch == ']':
            if depth > 0:
                depth -= 1
        else:
            if depth == 0:
                if need_space and ch.isalnum():
                    if out and not out[-1].isspace():
                        out.append(' ')
                    need_space = False
                out.append(ch)

    return re.sub(r'\s+', ' ', ''.join(out)).strip()
