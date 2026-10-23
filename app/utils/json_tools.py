import json
import re


class JsonNumber(str):
    pass


def reject_constant(value):
    raise ValueError(f"JSON 不支持 {value}")


def parse_json(text):
    return json.loads(text, parse_int=JsonNumber, parse_float=JsonNumber, parse_constant=reject_constant)


def format_json(text, indent=2, ensure_ascii=False):
    parse_json(text)
    tokens = re.finditer(r'"(?:\\.|[^"\\])*"|[^\s"{}\[\],:]+|[{}\[\],:]', text)
    output = []
    depth = 0
    previous = None
    for match in tokens:
        token = match.group()
        if token.startswith('"') and ensure_ascii:
            token = json.dumps(json.loads(token), ensure_ascii=True)
        if token in ("}", "]"):
            depth -= 1
            if indent and previous not in ("{", "["):
                output.append("\n" + " " * (depth * indent))
        elif indent and previous in ("{", "["):
            output.append("\n" + " " * (depth * indent))
        if token == ",":
            output.append("," + ("\n" + " " * (depth * indent) if indent else ""))
        elif token == ":":
            output.append(": " if indent else ":")
        else:
            output.append(token)
        if token in ("{", "["):
            depth += 1
        previous = token
    return "".join(output)


def json_fold_regions(text):
    regions = {}
    stack = []
    quoted = escaped = False
    line = 0
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "{[":
            stack.append(line)
        elif char in "}]" and stack:
            start = stack.pop()
            if line > start:
                regions[start] = line
        if char == "\n":
            line += 1
    return regions


def significant_position(text, position):
    offset = 0
    for match in re.finditer(r'"(?:\\.|[^"\\])*"|[^\s]', text):
        if match.start() >= position:
            break
        offset += min(position, match.end()) - match.start()
    return offset


def restore_position(text, offset):
    for match in re.finditer(r'"(?:\\.|[^"\\])*"|[^\s]', text):
        length = len(match.group())
        if offset < length:
            return match.start() + offset
        offset -= length
    return len(text)


def map_json_positions(source, result, positions):
    encoded = source.encode("utf-16-le", "surrogatepass")
    mapped = {}
    for position in set(positions):
        index = len(encoded[: position * 2].decode("utf-16-le", "surrogatepass"))
        target = restore_position(result, significant_position(source, index))
        mapped[position] = len(result[:target].encode("utf-16-le", "surrogatepass")) // 2
    return tuple(mapped[position] for position in positions)
