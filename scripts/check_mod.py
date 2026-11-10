#!/usr/bin/env python3
"""Pin the Build 7 mod contract deterministically.

The mod lives under hooks/ beside the portable core. This script
checks the mod's structural contract without a Claude Code host.
The contract it certifies is scoped to the shipped module's
structural family. A module standing outside that family is
refused with the family problem for the construct it carries,
and the readings below judge the contract only inside the
family, so no reading in this file claims to certify an
arbitrary module.
The hooks/hooks.json module list must name exactly the shipped
hooks module. The module must register its agent.spawn hook with
a string literal event name, must carry a .catch handler that
returns the deny shape, must read its environment variable
through the exact string literal name RECOGNITIO_PACKET_DIR and
its manifest through a path only file read, must never use the
struck onFailure
language or the withdrawn --mod flag, and must call no mods API
beyond the allowlist, so no model judgment can replace the
deterministic manifest check. The module exports register
and nothing else. The call site pins read the
module with its comments stripped, so a comment quoting a call
shape is not a call site. The mod brief at docs/mod-build7.md
must state the second layer fail open as a limit, the in session
gating boundary, the deployment gate check, the unset
disable-model-invocation, the version floor, and the seven
named residuals of the contract. At least one *.test.ts file
must exist for the host side test story.

The mod also ships as its own entry in the Claude marketplace
listing, sourced from the plugin folder at
plugins/recognitio-mod. That folder carries byte identical
copies of every file under hooks/ and of the root LICENSE,
and this gate pins the copies to the originals by directory
listing and by bytes, so the installed mod can never drift
from the module this gate certifies.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
BRIEF = ROOT / "docs" / "mod-build7.md"
MOD_PLUGIN_DIR = ROOT / "plugins" / "recognitio-mod"
MOD_PLUGIN_HOOKS = MOD_PLUGIN_DIR / "hooks"

ALLOWED_API_CALLS = {"$.fs.read", "$.env.get"}

LIMIT_SENTENCE = (
    "If the catch handler itself throws or times out, the host "
    "skips the hook as if it had no handler and the spawn proceeds"
)
BOUNDARY_SENTENCE = "The hook sees only in session agent spawns"
GATE_CHECK = "claude plugin validate --json"
FLAG_RECONCILIATION = "leaves `disable-model-invocation` at its default"


class DuplicateKeyError(ValueError):
    """A JSON object names one key twice."""


def strict_json_loads(text):
    """Parse JSON refusing a repeated key, like the other gates."""
    def reject(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                raise DuplicateKeyError("repeated key %r" % key)
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=reject)


def module_path():
    """The hooks module hooks/hooks.json names, or a problem."""
    if HOOKS_JSON.exists() and not HOOKS_JSON.is_file():
        return None, (
            "cannot read hooks/hooks.json, "
            "it is not a regular file"
        )
    try:
        data = strict_json_loads(HOOKS_JSON.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, "cannot read hooks/hooks.json, %s" % exc
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        return None, "hooks/hooks.json does not parse, %s" % exc
    modules = data.get("modules")
    if not isinstance(modules, list) or len(modules) != 1 \
            or not isinstance(modules[0], str):
        return None, "hooks/hooks.json names no single hooks module"
    path = (HOOKS_JSON.parent / modules[0]).resolve()
    try:
        path.relative_to((ROOT / "hooks").resolve())
    except ValueError:
        return None, "the hooks module %r is outside hooks/" % modules[0]
    if not path.is_file():
        return None, "the hooks module %r does not exist" % modules[0]
    return path, None


def _top_level_positions(text, chars):
    """The positions of chars standing at the top level of a text.

    A position counts when the character stands in code at
    bracket depth zero, outside every string, template and
    regex literal. Template text is inert and an
    interpolation is a nested range with its own depth, the
    reading the charged walkers hold.
    """
    found = []
    depth = 0
    state = "code"
    slash = _SlashContext()
    template_marks = []
    regex_class = False
    i = 0
    while i < len(text):
        ch = text[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                regex_class = False
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                if ch == "}" and template_marks \
                        and depth == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                    slash.feed(ch)
                    i += 1
                    continue
                depth -= 1
            elif depth == 0 and ch in chars:
                found.append((i, ch))
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                regex_class = True
            elif ch == "]":
                regex_class = False
            elif ch == "/" and not regex_class:
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state in ("single", "double"):
            if ch == "\\":
                i += 2
                continue
            if ch == ("'" if state == "single" else '"'):
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "template":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                state = "code"
                slash.mark_operand()
            elif ch == "$" and text[i + 1:i + 2] == "{":
                template_marks.append(depth)
                depth += 1
                state = "code"
                slash.open_interpolation()
                i += 2
                continue
            i += 1
            continue
    return found


def _decode_string_contents(text):
    """The value a string literal's raw contents spell.

    Decodes the escape forms the grammar allows in a
    string or plain template literal, unicode escapes in
    both spellings, hex escapes, the one letter escapes
    and an escaped character standing for itself, so a
    literal the host reads as one name can be judged by
    the name it reads. An escape the decoder cannot read
    keeps its raw spelling, so no name is fabricated.
    """
    simple = {
        "n": "\n", "t": "\t", "r": "\r", "b": "\b",
        "f": "\f", "v": "\v", "0": "\0",
    }
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != "\\" or i + 1 >= len(text):
            out.append(ch)
            i += 1
            continue
        nxt = text[i + 1]
        if nxt == "u":
            decoded = _unicode_escape_at(text, i)
            if decoded is not None:
                out.append(decoded[0])
                i = decoded[1]
                continue
            out.append(text[i:i + 2])
            i += 2
            continue
        if nxt == "x":
            digits = text[i + 2:i + 4]
            if len(digits) == 2 and all(
                    c in "0123456789abcdefABCDEF" for c in digits):
                out.append(chr(int(digits, 16)))
                i += 4
                continue
            out.append(text[i:i + 2])
            i += 2
            continue
        if nxt in simple:
            out.append(simple[nxt])
            i += 2
            continue
        if nxt in "\n\r\u2028\u2029":
            i += 2
            if nxt == "\r" and text[i:i + 1] == "\n":
                i += 1
            continue
        out.append(nxt)
        i += 2
    return "".join(out)


def _template_denotes(text):
    """The string a template literal denotes, or None.

    The literal parts decode as string contents do. An
    interpolation counts only where it is itself a string
    literal or a template that denotes a string, so the
    concatenation the parts spell is the value the host
    computes. Any other interpolation, a name, a call or
    an expression, leaves the template unread, and no
    string is fabricated from it.
    """
    s = text.strip()
    if not s.startswith("`"):
        return None
    parts = []
    raw = []
    i = 1
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            raw.append(s[i:i + 2])
            i += 2
            continue
        if ch == "`":
            if s[i + 1:].strip():
                return None
            parts.append(_decode_string_contents("".join(raw)))
            return "".join(parts)
        if ch == "$" and s[i + 1:i + 2] == "{":
            close = matching_close(s, i + 1)
            if close is None:
                return None
            inner = s[i + 2:close].strip()
            parts.append(_decode_string_contents("".join(raw)))
            raw = []
            literal = literal_at(inner, 0)
            if literal is not None \
                    and literal[1] == len(inner) \
                    and inner[:1] in ("'", '"'):
                parts.append(
                    _decode_string_contents(literal[0]))
            elif inner.startswith("`"):
                denoted = _template_denotes(inner)
                if denoted is None:
                    return None
                parts.append(denoted)
            else:
                return None
            i = close + 1
            continue
        raw.append(ch)
        i += 1
    return None


def _object_carries_deny(text, code, ranges, pos,
                         seen=frozenset(), fallback=None):
    """Whether an object literal carries a deny key in code.

    The key must stand in key position at the literal's top
    level, as a plain or quoted deny name or a bracketed
    deny literal in a quoted or plain template spelling,
    a template whose interpolations are themselves string
    literals spelling the name between them included. A
    spread counts when the value it spreads is a bound
    object whose own reading carries the deny key. The
    word deny inside a string value or a longer identifier
    that merely contains the letters names no key and
    counts for nothing.
    """
    s = text.strip()
    if not s.startswith("{"):
        return False
    close = matching_close(s, 0)
    if close is None:
        return False
    for prop in split_top_level(s[1:close]):
        prop = prop.strip()
        if not prop:
            continue
        if prop.startswith("..."):
            spread = prop[3:].strip()
            if _value_carries_deny(
                    spread, code, ranges, pos, seen, fallback):
                return True
            continue
        if prop.startswith("["):
            bracket_close = matching_close(prop, 0)
            if bracket_close is not None:
                inner = prop[1:bracket_close].strip()
                literal = literal_at(inner, 0)
                denoted = None
                if literal is not None \
                        and literal[1] == len(inner):
                    denoted = _decode_string_contents(literal[0])
                elif inner.startswith("`"):
                    denoted = _template_denotes(inner)
                if denoted == "deny":
                    rest = prop[bracket_close + 1:].lstrip()
                    if rest[:1] == ":":
                        return True
            continue
        named = re.match(
            r"(?:get\s+|set\s+)?"
            r"(deny|\"deny\"|'deny')(?![\w$])",
            prop)
        if named:
            rest = prop[named.end():].lstrip()
            if rest == "" or rest[:1] in (":", "(", "="):
                return True
    return False


def _binding_for_deny(code, ranges, name, pos, fallback):
    """The binding a deny judgement reads for a name.

    The one binding reading the gate holds, judged as at
    the position the name stands at. A name a handler
    text read on its own does not hold falls back to the
    module the handler stands in, judged as at the place
    the handler itself stands.
    """
    binding = _binding_value_at(code, ranges, name, pos)
    if binding is None and fallback is not None:
        fb_code, fb_ranges, anchor = fallback
        binding = _binding_value_at(fb_code, fb_ranges, name, anchor)
        if binding is not None:
            return binding, fb_code, fb_ranges
    return binding, code, ranges


def _register_entry_of(ranges):
    """The register entry the host calls at load, or None.

    The top level range named register, picked the way
    the registration judgement picks it.
    """
    candidates = [
        entry for entry in ranges if entry[2] == "register"]
    for entry in candidates:
        holders = [
            other for other in ranges
            if other is not entry
            and other[0] <= entry[0] and entry[1] <= other[1]
            and (other[0], other[1]) != (entry[0], entry[1])
        ]
        if not holders:
            return entry
    return candidates[0] if candidates else None


def _flow_class(code, entry, place):
    """Where a place stands in a body's flow.

    The reach reading of the register flow, applied to a
    binding's place, in the body of the entry that holds
    it, or over the module top level where no entry does.
    Returns reached where the place stands in the flow,
    branch where it stands on governed ground, and
    after_return where its sequence has already closed.
    """
    if entry is None:
        return _reach_in_sequence(code, 0, len(code), place)
    brace, close = _function_body_brace(code, entry)
    if brace is None:
        return "branch"
    if close is None:
        return _expression_verdict(
            code[brace:entry[1]], place - brace)
    return _reach_in_sequence(code, brace + 1, close, place)


def _called_unit_entries(code, ranges, entry, seen=frozenset()):
    """The units a function reaches through bare local calls.

    The calls are read in the unit's own code the way the
    gating reading reads them, and a call counts where
    its place classes as reached or as branch in the
    unit's flow, never where its sequence has closed.
    Returns the reached unit entries with the call's
    place and class, transitively, each unit once.
    """
    found = []
    if entry is None:
        return found
    span = (entry[0], entry[1] + 1)
    if span in seen:
        return found
    seen = seen | {span}
    intervals = _own_intervals(code, ranges, span, entry, set())
    for start, end in intervals:
        segment = code[start:end]
        for call in re.finditer(
                r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(", segment):
            place = start + call.start()
            if code[:place].rstrip().endswith("function"):
                continue
            call_class = _flow_class(code, entry, place)
            if call_class not in ("reached", "branch"):
                continue
            binding = _binding_value_at(
                code, ranges, call.group(1), place)
            if binding is None:
                continue
            kind, callee_entry, _, callee_span = binding
            if kind not in ("range", "text") or \
                    callee_span is None:
                continue
            unit_entry = callee_entry if kind == "range" else \
                _unit_entry(code, ranges, callee_span)
            if unit_entry is None:
                continue
            found.append((unit_entry, place, call_class))
            found.extend(_called_unit_entries(
                code, ranges, unit_entry, seen))
    return found


def _gating_entry_for_catch(code, ranges, catch_entry):
    """The gating entry of the registration a catch serves.

    Read from the module's own registration calls, the
    call whose chain's catch argument resolves to the
    catch handler's entry, whose handler argument is the
    gating handler the catch answers for. That handler
    runs on the spawn path before the catch handler can
    run, so the values it binds are values a name can
    hold when the catch handler runs.
    """
    if catch_entry is None:
        return None
    for call_start, _, args, close in _registration_calls(
            code, ranges):
        if len(args) < 2:
            continue
        catch_arg = _catch_argument(code, close + 1)
        if catch_arg is None:
            continue
        reading = _handler_reading(
            code, ranges, catch_arg[0], catch_arg[1], call_start)
        if reading is None or reading[2] is None:
            continue
        entry = _unit_entry(code, ranges, reading[2])
        if entry is None or \
                (entry[0], entry[1]) != \
                (catch_entry[0], catch_entry[1]):
            continue
        gating = _handler_reading(
            code, ranges, args[1][0], args[1][1], call_start)
        if gating is None or gating[2] is None:
            return None
        return _unit_entry(code, ranges, gating[2])
    return None


def _catch_feed_throw_texts(code, ranges, try_span):
    """The throw expressions a catch clause's try block feeds it.

    The throws standing in the try block itself, and the
    throws inside the local helpers the block calls,
    followed through further local calls with each
    helper read once, the same feed tracing the file
    read walk gives a catch binding.
    """
    start, end = try_span
    owner = enclosing_function(code, start, ranges)
    regions = [(start, end, owner)]
    visited = set()
    texts = []
    while regions:
        region_start, region_end, region_owner = regions.pop()
        texts.extend(_throw_texts_in(
            code, region_start, region_end, ranges,
            region_owner))
        for call in re.finditer(
                r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(",
                code[region_start:region_end]):
            callee = call.group(1)
            if code[:region_start + call.start()].rstrip(
                    ).endswith("function"):
                continue
            for entry in ranges:
                if entry[2] != callee:
                    continue
                if (entry[0], entry[1]) in visited:
                    continue
                visited.add((entry[0], entry[1]))
                brace, close = _function_body_brace(code, entry)
                if brace is not None and close is not None:
                    regions.append((brace, close, entry))
    return texts


def _deny_name_carries(code, ranges, name, pos, seen,
                       fallback=None, every=True):
    """Whether every value a name can hold carries deny.

    A deny name is judged at the moment the handler
    runs, so the bindings that can decide its value are
    the ones that have run by then, read in the order
    they run. The module top level runs first, in its
    written order, then the register function the host
    calls at load, in its written order, then the
    handler's own function in its written order up to
    the position the name stands at, where the handler
    declaring the name itself shadows every outer
    binding. The gating handler of the same registration
    runs on the spawn path before the catch handler can
    run, so its bindings, and the bindings of the
    functions it reaches, add values the name can hold
    without ever settling it, since the crash can come
    before any of them runs or after any of them. The
    functions the handler itself reaches before the
    position run as part of the handler's own run, at
    the place of the call that reaches them. In each
    run, a binding standing in the statement flow settles
    the value, a binding standing on governed ground, in
    a branch or behind a conditional, only adds a value
    the name can hold, and a binding after a closed
    sequence never runs and counts for nothing, the
    reach reading the register flow already holds.
    Bindings in any other function count for nothing,
    since that function runs neither at load, nor on the
    spawn path before the handler, nor in the handler.
    A name bound by a catch clause around the position
    is judged by the throws of that clause's try block,
    the feeds the file read walk traces for a catch
    binding, since the thrown value is the value the
    name holds there, shadowing every outer binding.
    The name carries the
    deny shape only where every value it can still hold
    does, aliases resolved through the shared binding
    reading, or, where the question is whether it can
    carry the shape, where any value it can still hold
    does.
    """
    events = _binding_events(code, ranges, name)
    here = enclosing_function(code, pos, ranges)
    catch_span = _catch_binding_at(code, name, pos)
    if catch_span is not None:
        throws = _catch_feed_throw_texts(
            code, ranges, catch_span)
        if not throws:
            return False
        verdicts = [
            _value_carries_deny(
                value, code, ranges, at, seen | {name},
                fallback)
            for at, value in throws]
        return all(verdicts) if every else any(verdicts)
    register_entry = _register_entry_of(ranges)
    top_events = []
    register_events = []
    own_events = []
    scoped_events = []
    for place, priority, value in events:
        exclude = None
        if value[0] == "range":
            exclude = (value[1][0], value[1][1])
        scope = _containing_scope(code, ranges, place, exclude)
        scoped_events.append((place, priority, value, scope))
        if scope is None:
            top_events.append((place, priority, value))
        elif here is not None and \
                (scope[0], scope[1]) == (here[0], here[1]):
            if place < pos:
                own_events.append((place, priority, value))
        elif register_entry is not None and \
                (scope[0], scope[1]) == (
                    register_entry[0], register_entry[1]):
            register_events.append((place, priority, value))
    shadowed = here is not None and \
        declares_name(code, name, here, pos)
    crash_values = []
    if not shadowed:
        gating_entry = _gating_entry_for_catch(code, ranges, here)
        crash_units = []
        if gating_entry is not None:
            crash_units.append(gating_entry)
            crash_units.extend(
                unit for unit, _, _ in _called_unit_entries(
                    code, ranges, gating_entry))
        for unit in crash_units:
            if declares_name(code, name, unit, unit[1]):
                continue
            for place, _, value, scope in scoped_events:
                if scope is not None and \
                        (scope[0], scope[1]) == \
                        (unit[0], unit[1]):
                    crash_values.append(value)
    own_items = []
    for place, priority, value in own_events:
        own_items.append((
            _binding_event_order(code, (place, priority, value)),
            here, place, value, False))
    if here is not None and not shadowed:
        for callee, call_place, call_class in \
                _called_unit_entries(code, ranges, here):
            if call_place >= pos:
                continue
            if declares_name(code, name, callee, callee[1]):
                continue
            callee_events = [
                (place, priority, value)
                for place, priority, value, scope in scoped_events
                if scope is not None and
                (scope[0], scope[1]) == (callee[0], callee[1])]
            for sub, (place, priority, value) in enumerate(
                    sorted(callee_events,
                           key=lambda event:
                           _binding_event_order(code, event))):
                own_items.append((
                    (call_place, 1, sub), callee, place, value,
                    call_class == "branch"))
    if not (top_events or register_events or own_events
            or crash_values or own_items):
        if fallback is not None:
            fb_code, fb_ranges, anchor = fallback
            return _deny_name_carries(
                fb_code, fb_ranges, name, anchor, seen, None,
                every)
        return False
    possible = []
    phases = []
    if not shadowed:
        phases.append([
            (_binding_event_order(code, event), None,
             event[0], event[2], False)
            for event in top_events])
        phases.append([
            (_binding_event_order(code, event), register_entry,
             event[0], event[2], False)
            for event in register_events])
    for group in phases:
        for _, entry, place, value, _ in sorted(
                group, key=lambda item: item[0]):
            if value[0] == "range" and \
                    _is_declaration(code, value[1]):
                place_class = "reached"
            else:
                place_class = _flow_class(code, entry, place)
            if place_class == "reached":
                possible = [value]
            elif place_class == "branch":
                possible.append(value)
    possible.extend(crash_values)
    for _, entry, place, value, force in sorted(
            own_items, key=lambda item: item[0]):
        if force:
            possible.append(value)
            continue
        if value[0] == "range" and \
                _is_declaration(code, value[1]):
            place_class = "reached"
        else:
            place_class = _flow_class(code, entry, place)
        if place_class == "reached":
            possible = [value]
        elif place_class == "branch":
            possible.append(value)
    if not possible:
        return False
    for value in possible:
        resolved = value
        guard = set()
        carries = False
        while resolved is not None and \
                resolved[0] == "alias" and \
                resolved[1] not in guard:
            guard.add(resolved[1])
            resolved = _binding_value_at(
                code, ranges, resolved[1], resolved[3][0])
        if resolved is not None:
            kind, _, rhs, span = resolved
            if kind == "other":
                carries = _value_carries_deny(
                    rhs, code, ranges, span[0], seen | {name},
                    fallback)
        if carries != every:
            return carries
    return every


def _always_truthy(text, code, ranges, pos,
                   seen=frozenset(), fallback=None):
    """Whether an expression is truthy on every outcome.

    An object or array literal is always truthy, as is a
    function value, and a bare name is as truthy as the
    value its binding under the shared reading holds.
    Anything else the reading cannot prove, so a call or
    a member read counts for nothing here.
    """
    s = text.strip()
    if s[:1] in ("{", "["):
        return True
    ident = re.fullmatch(r"[A-Za-z_$][\w$]*", s)
    if ident and s not in seen:
        binding, bcode, branges = _binding_for_deny(
            code, ranges, s, pos, fallback)
        if binding is None:
            return False
        kind, _, rhs, span = binding
        if kind in ("range", "text"):
            return True
        if kind == "other":
            return _always_truthy(
                rhs, bcode, branges, span[0], seen | {s},
                fallback)
    return False


def _always_falsy(text, code, ranges, pos,
                  seen=frozenset(), fallback=None):
    """Whether an expression is falsy on every outcome.

    Only the falsy literals prove it, or a bare name whose
    binding under the shared reading holds one.
    """
    s = text.strip()
    if s in ("false", "null", "undefined", "0", "''", '""'):
        return True
    ident = re.fullmatch(r"[A-Za-z_$][\w$]*", s)
    if ident and s not in seen:
        binding, bcode, branges = _binding_for_deny(
            code, ranges, s, pos, fallback)
        if binding is not None and binding[0] == "other":
            return _always_falsy(
                binding[2], bcode, branges, binding[3][0],
                seen | {s}, fallback)
    return False


def _always_nullish(text, code, ranges, pos,
                    seen=frozenset(), fallback=None):
    """Whether an expression is null or undefined always.

    Only the nullish literals prove it, or a bare name
    whose binding under the shared reading holds one.
    The nullish fallback reads its first operand through
    this fact, since a value that is merely falsy, an
    empty string or a zero, still stands as the value a
    nullish fallback produces.
    """
    s = text.strip()
    if s in ("null", "undefined"):
        return True
    ident = re.fullmatch(r"[A-Za-z_$][\w$]*", s)
    if ident and s not in seen:
        binding, bcode, branges = _binding_for_deny(
            code, ranges, s, pos, fallback)
        if binding is not None and binding[0] == "other":
            return _always_nullish(
                binding[2], bcode, branges, binding[3][0],
                seen | {s}, fallback)
    return False


def _logical_positions(s, operator):
    """The split points of one logical operator in a text.

    Only occurrences at the text's own top level count,
    read over its tokens, so an operator inside a bracket
    or a literal splits nothing.
    """
    tokens = _reach_tokens(s, 0, len(s), literal_spans(s))
    depth = 0
    points = []
    for _, token, tok_start, tok_end in tokens:
        if token in ("(", "[", "{"):
            depth += 1
        elif token in (")", "]", "}"):
            depth -= 1
        elif depth == 0 and token == operator:
            points.append((tok_start, tok_end))
    return points


def _value_carries_deny(text, code, ranges, pos,
                        seen=frozenset(), fallback=None):
    """Whether an outcome expression produces a deny object.

    Every outcome the expression can produce must carry
    the deny key, so a conditional outcome counts only
    when both of its branches do. A fallback outcome
    counts when its first operand carries the deny key,
    because a deny object is truthy and so is the value
    the fallback produces wherever the first operand
    stands, or when the first operand is falsy on every
    outcome and the rest of the fallback does. A nullish
    fallback counts the same way, with the nullish
    literals standing where the falsy ones stand for the
    truthy fallback, since a deny object is never
    nullish and a merely falsy first operand still
    stands as the value produced. A conjunction
    counts when its first operand is truthy on every
    outcome and its rest does. A bare name counts when
    the value it is bound to does, judged by the one
    binding reading as at the position the name stands
    at, so the scope, branch and written order discipline
    that reading holds decides, and never the last
    assignment standing anywhere in the module text. A
    bare call to a helper the module itself defines
    counts when every outcome of that helper produces a
    deny object by this same judgement, through as many
    levels of helpers as the module chains. Anything
    else, a member read or an empty object, produces no
    deny shape the pin can read. The fallback named in
    the arguments carries the module a handler text read
    on its own stands in, for the names that text does
    not itself hold.
    """
    s = text.strip()
    pos += len(text) - len(text.lstrip())
    while s.startswith("("):
        close = matching_close(s, 0)
        if close is None or s[close + 1:].strip():
            break
        pos += 1 + (len(s[1:close]) - len(s[1:close].lstrip()))
        s = s[1:close].strip()
    if _object_carries_deny(s, code, ranges, pos, seen, fallback):
        return True
    positions = _top_level_positions(s, "?:")
    qpos = None
    for index, ch in positions:
        if ch != "?":
            continue
        nxt = s[index + 1:index + 2]
        if nxt == "?" or (index > 0 and s[index - 1] == "?"):
            continue
        if nxt == "." and not s[index + 2:index + 3].isdigit():
            continue
        qpos = index
        break
    if qpos is not None:
        nested = 0
        for index, ch in positions:
            if index <= qpos:
                continue
            if ch == "?":
                nxt = s[index + 1:index + 2]
                if nxt == "?" or (index > 0
                        and s[index - 1] == "?") or (
                        nxt == "."
                        and not s[index + 2:index + 3].isdigit()):
                    continue
                nested += 1
            elif nested == 0:
                return _value_carries_deny(
                    s[qpos + 1:index], code, ranges,
                    pos + qpos + 1, seen, fallback) and \
                    _value_carries_deny(
                        s[index + 1:], code, ranges,
                        pos + index + 1, seen, fallback)
            else:
                nested -= 1
        return False
    or_points = _logical_positions(s, "||")
    if or_points:
        start, end = or_points[0]
        first = s[:start]
        if _value_carries_deny(
                first, code, ranges, pos, seen, fallback):
            return True
        return _always_falsy(
            first, code, ranges, pos, seen, fallback) and \
            _value_carries_deny(
                s[end:], code, ranges, pos + end, seen, fallback)
    qq_points = _logical_positions(s, "??")
    if qq_points:
        start, end = qq_points[0]
        first = s[:start]
        if _value_carries_deny(
                first, code, ranges, pos, seen, fallback):
            return True
        return _always_nullish(
            first, code, ranges, pos, seen, fallback) and \
            _value_carries_deny(
                s[end:], code, ranges, pos + end, seen, fallback)
    and_points = _logical_positions(s, "&&")
    if and_points:
        start, end = and_points[0]
        return _always_truthy(
            s[:start], code, ranges, pos, seen, fallback) and \
            _value_carries_deny(
                s[end:], code, ranges, pos + end, seen, fallback)
    ident = re.fullmatch(r"[A-Za-z_$][\w$]*", s)
    if ident and s not in seen:
        return _deny_name_carries(
            code, ranges, s, pos, seen, fallback)
    call = re.match(r"([A-Za-z_$][\w$]*)\s*\(", s)
    if call:
        open_paren = s.index("(", call.start())
        close = matching_close(s, open_paren)
        if close is not None and not s[close + 1:].strip() \
                and call.group(1) not in seen:
            return _helper_call_carries_deny(
                call.group(1), code, ranges, pos, seen, fallback)
    return False


def _object_can_carry_deny(text, code, ranges, pos,
                           seen=frozenset(), fallback=None):
    """Whether an object literal can carry a deny key.

    The companion of the object reading in the deny
    judgement, for the question whether one of the
    literal's outcomes carries the key, so a spread
    counts where the value it spreads can carry it.
    """
    s = text.strip()
    if not s.startswith("{"):
        return False
    close = matching_close(s, 0)
    if close is None:
        return False
    for prop in split_top_level(s[1:close]):
        prop = prop.strip()
        if not prop:
            continue
        if prop.startswith("..."):
            spread = prop[3:].strip()
            if _value_can_carry_deny(
                    spread, code, ranges, pos, seen, fallback):
                return True
            continue
        if prop.startswith("["):
            bracket_close = matching_close(prop, 0)
            if bracket_close is not None:
                inner = prop[1:bracket_close].strip()
                literal = literal_at(inner, 0)
                denoted = None
                if literal is not None \
                        and literal[1] == len(inner):
                    denoted = _decode_string_contents(literal[0])
                elif inner.startswith("`"):
                    denoted = _template_denotes(inner)
                if denoted == "deny":
                    rest = prop[bracket_close + 1:].lstrip()
                    if rest[:1] == ":":
                        return True
            continue
        named = re.match(
            r"(?:get\s+|set\s+)?"
            r"(deny|\"deny\"|'deny')(?![\w$])",
            prop)
        if named:
            rest = prop[named.end():].lstrip()
            if rest == "" or rest[:1] in (":", "(", "="):
                return True
    return False


def _value_can_carry_deny(text, code, ranges, pos,
                          seen=frozenset(), fallback=None):
    """Whether an outcome expression can produce a deny object.

    The companion of the deny judgement for the gating
    question, which asks whether one of a handler's
    outcomes produces the deny shape. A conditional can
    produce it where either branch can, a fallback where
    either side can, and a conjunction where its right
    side can. A bare name can where any value it can
    hold under the deny name reading carries it, read
    here as a possibility over the same bindings. A bare
    call to a helper the module itself defines can where
    one of the helper's own outcomes can, through as
    many levels of delegation as the module chains, so a
    handler that delegates its gating to a helper that
    delegates in turn reads as the gating handler it is.
    """
    s = text.strip()
    pos += len(text) - len(text.lstrip())
    while s.startswith("("):
        close = matching_close(s, 0)
        if close is None or s[close + 1:].strip():
            break
        pos += 1 + (len(s[1:close]) - len(s[1:close].lstrip()))
        s = s[1:close].strip()
    if _object_can_carry_deny(s, code, ranges, pos, seen,
                              fallback):
        return True
    positions = _top_level_positions(s, "?:")
    qpos = None
    for index, ch in positions:
        if ch != "?":
            continue
        nxt = s[index + 1:index + 2]
        if nxt == "?" or (index > 0 and s[index - 1] == "?"):
            continue
        if nxt == "." and not s[index + 2:index + 3].isdigit():
            continue
        qpos = index
        break
    if qpos is not None:
        nested = 0
        for index, ch in positions:
            if index <= qpos:
                continue
            if ch == "?":
                nxt = s[index + 1:index + 2]
                if nxt == "?" or (index > 0
                        and s[index - 1] == "?") or (
                        nxt == "."
                        and not s[index + 2:index + 3].isdigit()):
                    continue
                nested += 1
            elif nested == 0:
                return _value_can_carry_deny(
                    s[qpos + 1:index], code, ranges,
                    pos + qpos + 1, seen, fallback) or \
                    _value_can_carry_deny(
                        s[index + 1:], code, ranges,
                        pos + index + 1, seen, fallback)
            else:
                nested -= 1
        return False
    or_points = _logical_positions(s, "||")
    if or_points:
        start, end = or_points[0]
        return _value_can_carry_deny(
            s[:start], code, ranges, pos, seen, fallback) or \
            _value_can_carry_deny(
                s[end:], code, ranges, pos + end, seen,
                fallback)
    qq_points = _logical_positions(s, "??")
    if qq_points:
        start, end = qq_points[0]
        return _value_can_carry_deny(
            s[:start], code, ranges, pos, seen, fallback) or \
            _value_can_carry_deny(
                s[end:], code, ranges, pos + end, seen,
                fallback)
    and_points = _logical_positions(s, "&&")
    if and_points:
        start, end = and_points[0]
        return _value_can_carry_deny(
            s[end:], code, ranges, pos + end, seen, fallback)
    ident = re.fullmatch(r"[A-Za-z_$][\w$]*", s)
    if ident and s not in seen:
        return _deny_name_carries(
            code, ranges, s, pos, seen, fallback,
            every=False)
    call = re.match(r"([A-Za-z_$][\w$]*)\s*\(", s)
    if call:
        open_paren = s.index("(", call.start())
        close = matching_close(s, open_paren)
        if close is not None and not s[close + 1:].strip() \
                and call.group(1) not in seen:
            name = call.group(1)
            binding, bcode, branges = _binding_for_deny(
                code, ranges, name, pos, fallback)
            if binding is None:
                return False
            kind, entry, helper_text, _ = binding
            if kind == "range":
                items = _handler_outcome_items(
                    bcode, entry, branges)
                judge_code, judge_ranges = bcode, branges
            elif kind == "text":
                items = _inline_outcome_items(
                    helper_text.strip())
                if items is None:
                    return False
                judge_code = helper_text.strip()
                judge_ranges = function_ranges(judge_code)
            else:
                return False
            return any(
                item_kind == "value" and
                _value_can_carry_deny(
                    value, judge_code, judge_ranges, item_pos,
                    seen | {name}, fallback)
                for item_kind, value, item_pos in items)
    return False


def _helper_call_carries_deny(name, code, ranges, pos, seen,
                              fallback=None):
    """Whether every outcome of a named helper denies.

    The helper stands under a bound name, judged by its
    binding as at the call, by the same complete outcome
    judgement the catch pin applies to its own handler.
    A helper whose outcomes call a further helper is read
    through that helper by the same judgement, so the
    reading is transitive, and a name already under
    judgement on the chain answers nothing, so a helper
    that calls itself in a circle certifies nothing.
    """
    binding, bcode, branges = _binding_for_deny(
        code, ranges, name, pos, fallback)
    if binding is None:
        return False
    kind, entry, text, _ = binding
    if kind == "range":
        items = _handler_outcome_items(bcode, entry, branges)
        judge_code, judge_ranges = bcode, branges
    elif kind == "text":
        items = _inline_outcome_items(text.strip())
        if items is None:
            return False
        judge_code = text.strip()
        judge_ranges = function_ranges(judge_code)
    else:
        return False
    return bool(items) and all(
        item_kind == "value" and _value_carries_deny(
            value, judge_code, judge_ranges, item_pos,
            seen | {name}, fallback)
        for item_kind, value, item_pos in items)


def _unlabelled(text):
    """A statement text with any label prefixes stripped.

    A label names the statement it stands on and changes
    nothing about the statement's own shape, so the
    readings that dispatch on a statement's leading word
    read through the labels to the statement itself. A
    colon a conditional expression carries is no label,
    since the word before it is followed by the question
    mark first.
    """
    s = text
    while True:
        label = re.match(r"([A-Za-z_$][\w$]*)\s*:(?!:)", s)
        if label is None:
            return s
        s = s[label.end():].lstrip()
        if not s:
            return s


def _first_statement(text):
    """The first statement of a text, as its text and length.

    The scan is literal aware in the split_top_level
    spelling, so a semicolon or a brace inside a string,
    a template or a regex moves nothing. A statement ends
    at a top level semicolon, or at a top level closing
    brace whose next token is not a continuation of the
    statement, where else, catch and finally words and
    the operator characters count as continuations. A
    text that opens with a brace opens with a block
    statement, and its first statement is that block
    alone, since a leading brace is a block in the
    grammar and never an object literal.
    """
    stripped = text.lstrip()
    if stripped.startswith("{"):
        lead = len(text) - len(stripped)
        block_close = matching_close(text, lead)
        if block_close is not None:
            return text[:block_close + 1], block_close + 1
    frames = []
    state = "code"
    slash = _SlashContext()
    template_marks = []
    i = 0
    while i < len(text):
        ch = text[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in "([{":
                frames.append(ch)
            elif ch in ")]}":
                if frames:
                    frames.pop()
                if ch == "}" and template_marks \
                        and len(frames) == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                    slash.feed(ch)
                    i += 1
                    continue
                if ch == "}" and not frames:
                    j = i + 1
                    while j < len(text) and text[j].isspace():
                        j += 1
                    if j >= len(text):
                        return text[:i + 1], i + 1
                    if text[j] == ";":
                        return text[:j + 1], j + 1
                    ahead = re.match(
                        r"(else|catch|finally)(?![\w$])",
                        text[j:])
                    if ahead:
                        slash.feed(ch)
                        i += 1
                        continue
                    if text[j] in ".,([+-*/%<>=!&|?^~":
                        slash.feed(ch)
                        i += 1
                        continue
                    return text[:i + 1], i + 1
            elif ch == ";" and not frames:
                return text[:i + 1], i + 1
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                text[i + 1:i + 2] == "{":
            template_marks.append(len(frames))
            frames.append("{")
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    return text, len(text)


def _leading_word(text):
    """The word a stripped text opens with, and its end."""
    match = re.match(r"([A-Za-z_$][\w$]*)", text)
    if not match:
        return None, 0
    return match.group(1), match.end()


def _if_carries_else(statement):
    """Whether an if statement's text already holds its else.

    Reads the statement's own head and first arm the way
    the completion calculus does, so an else the text
    already carries is not glued twice.
    """
    s = statement.strip()
    _, end = _leading_word(s)
    open_paren = s.find("(", end)
    if open_paren == -1:
        return False
    close = matching_close(s, open_paren)
    if close is None:
        return False
    _, used = _first_statement(s[close + 1:])
    after = s[close + 1 + used:].strip()
    else_word, _ = _leading_word(after)
    return else_word == "else"


def _whole_statement(text):
    """The first statement of a text, with its else arm glued.

    The first statement scan ends an unbraced if at its
    arm's own semicolon, before the else arm the grammar
    binds to that if, so a statement read for its exits
    or its flow is glued back together here, arm by arm,
    an else if chain included. Every other statement is
    the scan's own.
    """
    statement, used = _first_statement(text)
    word, _ = _leading_word(_unlabelled(statement.strip()))
    if word != "if" or _if_carries_else(statement):
        return statement, used
    rest = text[used:]
    after = rest.lstrip()
    else_word, else_end = _leading_word(after)
    if else_word != "else":
        return statement, used
    _, arm_used = _whole_statement(after[else_end:])
    total = used + (len(rest) - len(after)) + else_end + arm_used
    return text[:total], total


def _switch_clauses(inner):
    """The clause statement texts of a switch block.

    Returns the clauses as text and flag pairs, the flag
    naming the default clause, read at the block's own
    level over its tokens, so a case word inside a nested
    block or a literal names no clause. A colon inside a
    case expression's own conditional is no label colon.
    """
    tokens = _reach_tokens(inner, 0, len(inner),
                           literal_spans(inner))
    labels = []
    depth = 0
    i = 0
    while i < len(tokens):
        kind, text, tok_start, tok_end = tokens[i]
        if text in ("(", "[", "{"):
            depth += 1
        elif text in (")", "]", "}"):
            depth -= 1
        elif depth == 0 and kind == "word" \
                and text in ("case", "default"):
            j = i + 1
            inner_depth = 0
            questions = 0
            colon_end = None
            while j < len(tokens):
                _, other, _, other_end = tokens[j]
                if other in ("(", "[", "{"):
                    inner_depth += 1
                elif other in (")", "]", "}"):
                    inner_depth -= 1
                elif inner_depth == 0 and other == "?":
                    questions += 1
                elif inner_depth == 0 and other == ":":
                    if questions:
                        questions -= 1
                    else:
                        colon_end = other_end
                        break
                j += 1
            if colon_end is not None:
                labels.append(
                    (tok_start, colon_end, text == "default"))
                i = j
        i += 1
    clauses = []
    for index, (label_start, colon_end, is_default) in \
            enumerate(labels):
        end = labels[index + 1][0] \
            if index + 1 < len(labels) else len(inner)
        clauses.append((inner[colon_end:end], is_default))
    return clauses, any(is_default for _, is_default in clauses)


def _statement_exits(text):
    """The ways control can leave one statement.

    The one completion calculus of this gate, read by the
    outcome walk for the end of a handler body and by the
    register reach walk for the flow a registration stands
    in. The exits are fall, where control reaches the end
    of the statement, return and throw, where it leaves
    the function, and break, where it leaves the nearest
    loop or switch the statement stands in. The simple
    shapes the judgements state. A block exits as its
    sequence does. An if with no else can always fall,
    and an if with an else exits as its two branches do
    between them. A try block's throw exit is answered by
    its catch block, whose exits then stand in its place,
    a catch whose block the try never throws into answers
    nothing, and a finally block that cannot fall decides
    the whole try, while one that can fall adds only its
    own abrupt exits. A do loop exits as its body does,
    with a break in the body standing for a fall. A loop
    whose condition can fail falls by its condition, and
    a loop with an empty or true condition falls only
    where its body reaches a break. A switch falls where
    it has no default clause, where a clause reaches a
    break, or where a clause falls through to the end,
    and its abrupt exits are the exits of its clauses.
    A labelled statement exits as the statement it
    labels does, with a break leaving the labelled
    statement itself standing for a fall where the
    statement is no loop or switch, since that break
    ends the statement and control continues after it.
    Every other statement falls.
    """
    s = text.strip()
    if not s:
        return {"fall"}
    peeled = _unlabelled(s)
    labelled = peeled != s
    exits = _statement_exits_unlabelled(peeled)
    if labelled:
        word, _ = _leading_word(peeled)
        if word not in ("while", "for", "do", "switch") \
                and "break" in exits:
            exits = (exits - {"break"}) | {"fall"}
    return exits


def _statement_exits_unlabelled(s):
    if s.startswith("{"):
        close = matching_close(s, 0)
        if close is not None and not s[close + 1:].strip():
            return _sequence_exits(s[1:close])
        return {"fall"}
    word, end = _leading_word(s)
    if word == "return":
        return {"return"}
    if word == "throw":
        return {"throw"}
    if word == "break":
        return {"break"}
    if word == "if":
        open_paren = s.find("(", end)
        if open_paren == -1:
            return {"fall"}
        close = matching_close(s, open_paren)
        if close is None:
            return {"fall"}
        rest = s[close + 1:]
        then_text, used = _whole_statement(rest)
        after = rest[used:].strip()
        else_word, else_end = _leading_word(after)
        if else_word != "else":
            return _statement_exits(then_text) | {"fall"}
        else_text, _ = _first_statement(after[else_end:])
        return _statement_exits(then_text) | \
            _statement_exits(else_text)
    if word == "try":
        rest = s[end:]
        block_text, used = _first_statement(rest)
        exits = _statement_exits(block_text)
        catch_exits = None
        finally_exits = None
        rest = rest[used:]
        while rest.strip():
            next_word, next_end = _leading_word(rest.strip())
            stripped = rest.strip()
            if next_word == "catch":
                inner = stripped[next_end:].strip()
                if inner.startswith("("):
                    paren_close = matching_close(inner, 0)
                    if paren_close is None:
                        break
                    inner = inner[paren_close + 1:]
                catch_text, catch_used = _first_statement(inner)
                catch_exits = _statement_exits(catch_text)
                rest = inner[catch_used:]
            elif next_word == "finally":
                inner = stripped[next_end:]
                finally_text, finally_used = \
                    _first_statement(inner)
                finally_exits = _statement_exits(finally_text)
                rest = inner[finally_used:]
            else:
                break
        if catch_exits is not None:
            if "throw" in exits:
                exits = (exits - {"throw"}) | catch_exits
            else:
                exits = exits - {"throw"}
        if finally_exits is not None:
            if "fall" not in finally_exits:
                return set(finally_exits)
            return exits | (finally_exits - {"fall"})
        return exits
    if word == "do":
        rest = s[end:]
        body_text, _ = _whole_statement(rest)
        exits = _statement_exits(body_text)
        out = exits - {"break"}
        if "break" in exits:
            out.add("fall")
        return out
    if word in ("while", "for"):
        open_paren = s.find("(", end)
        if open_paren == -1:
            return {"fall"}
        close = matching_close(s, open_paren)
        if close is None:
            return {"fall"}
        head = s[open_paren + 1:close]
        if word == "while":
            constant = head.strip() == "true"
        else:
            parts = []
            start = 0
            for pos, _ in _top_level_positions(head, ";"):
                parts.append(head[start:pos])
                start = pos + 1
            parts.append(head[start:])
            constant = len(parts) >= 3 and \
                parts[1].strip() in ("", "true")
        body_text, _ = _whole_statement(s[close + 1:])
        exits = _statement_exits(body_text)
        if constant:
            out = exits - {"break"}
            if "break" in exits:
                out.add("fall")
            return out
        return {"fall"} | (exits & {"return", "throw"})
    if word == "switch":
        open_paren = s.find("(", end)
        if open_paren == -1:
            return {"fall"}
        close = matching_close(s, open_paren)
        if close is None:
            return {"fall"}
        block_text, _ = _first_statement(s[close + 1:])
        block = block_text.strip()
        if not block.startswith("{"):
            return {"fall"}
        block_close = matching_close(block, 0)
        if block_close is None:
            return {"fall"}
        clauses, has_default = _switch_clauses(
            block[1:block_close])
        if not clauses:
            return {"fall"}
        clause_exits = [
            _sequence_exits(clause) for clause, _ in clauses]
        abrupt = set()
        for exits in clause_exits:
            abrupt |= exits & {"return", "throw"}
        reach_end = [False] * len(clauses)
        following = False
        for index in range(len(clauses) - 1, -1, -1):
            exits = clause_exits[index]
            reach_end[index] = "break" in exits or (
                "fall" in exits and (
                    index == len(clauses) - 1 or following))
            following = reach_end[index]
        if not has_default or any(reach_end):
            abrupt.add("fall")
        return abrupt
    return {"fall"}


def _sequence_exits(text):
    """The ways control can leave a statement list.

    Read statement by statement through _first_statement.
    A statement that cannot fall ends the list, so the
    statements after it contribute no exits, and a list
    every statement of which falls reaches its own end.
    """
    exits = set()
    rest = text
    while rest.strip():
        statement, used = _whole_statement(rest)
        if not used:
            break
        if statement.strip():
            statement_exits = _statement_exits(statement)
            exits |= statement_exits - {"fall"}
            if "fall" not in statement_exits:
                return exits
        rest = rest[used:]
    exits.add("fall")
    return exits


def _sequence_can_complete(text):
    """Whether control can reach the end of a statement list.

    One reading of the shared completion calculus, kept
    under the name the outcome judgement states it by.
    """
    return "fall" in _sequence_exits(text)


def _try_catch_intervals(text, start, end):
    """The try block spans in a range that a catch answers.

    A throw inside one of these spans is caught inside
    the function that holds it, so it is no exit from
    that function. A try with only a finally answers
    nothing, and its span stands outside the list.
    """
    intervals = []
    for match in re.finditer(
            r"(?<![\w$.])try(?![\w$])", text[start:end]):
        pos = start + match.start()
        i = pos + len("try")
        while i < end and text[i].isspace():
            i += 1
        if i >= end or text[i] != "{":
            continue
        close = matching_close(text, i)
        if close is None or close > end:
            continue
        j = close + 1
        while j < end and text[j].isspace():
            j += 1
        if re.match(r"catch(?![\w$])", text[j:]):
            intervals.append((i, close))
    return intervals


def _outcome_items_in_block(text, inner_start, inner_end,
                              entry_span, ranges):
    """Every exit outcome of a block body, in one list.

    Each return expression is a value outcome. A bare
    return is an undefined outcome and stands in the list
    as a bad outcome, as does a throw that no catch inside
    the body answers, since the live host probe in this
    lane's record shows a throwing catch handler letting
    the spawn proceed. The end of the body is a bad
    outcome where control can reach it under the simple
    completion shapes _sequence_can_complete states.
    Returns and throws count only where this function is
    their innermost function, or, where entry_span is
    None for a body read on its own, where no nested
    function in the body holds them.
    """
    items = []

    def holds(pos):
        holder = enclosing_function(text, pos, ranges)
        if entry_span is not None:
            return holder is not None and \
                (holder[0], holder[1]) == entry_span
        return holder is None

    for match in re.finditer(
            r"(?<![\w$.])return(?![\w$])",
            text[inner_start:inner_end]):
        at = inner_start + match.start()
        if not holds(at):
            continue
        value, _ = expression_at(text, at + len("return"))
        if value.strip():
            lead = len(value) - len(value.lstrip())
            gap = text[at + len("return"):
                       at + len("return") + lead]
            if any(mark in gap
                   for mark in "\n\r\u2028\u2029"):
                # A line terminator between the return word
                # and its expression ends the return under
                # the restricted production, the same fact
                # the slash tracker holds for the brace
                # after a return, so the expression on the
                # next line is a statement of its own and
                # the return is a bare one.
                items.append(("bad", "a bare return", at))
            else:
                items.append(
                    ("value", value, at + len("return")))
        else:
            items.append(("bad", "a bare return", at))
    protected = _try_catch_intervals(text, inner_start, inner_end)
    for match in re.finditer(
            r"(?<![\w$.])throw(?![\w$])",
            text[inner_start:inner_end]):
        at = inner_start + match.start()
        if not holds(at):
            continue
        if any(start <= at <= close for start, close in protected):
            continue
        items.append(("bad", "a throw", at))
    if _sequence_can_complete(text[inner_start:inner_end]):
        items.append(("bad", "the end of its body", inner_end))
    return items


def _function_body_brace(code, entry):
    """The body brace of a function range, or its expression.

    Returns a pair, the index of the opening brace of a
    block body and its closing index, or the start of an
    expression body and None for the second value.
    """
    i = entry[5] + 1
    while i < len(code) and code[i].isspace():
        i += 1
    if code[i:i + 2] == "=>":
        i += 2
        while i < len(code) and code[i].isspace():
            i += 1
        if i >= len(code) or code[i] != "{":
            return i, None
    if i >= len(code) or code[i] != "{":
        return None, None
    return i, matching_close(code, i)


def _handler_outcome_items(code, entry, ranges):
    """Every exit outcome a handler range can produce."""
    brace, close = _function_body_brace(code, entry)
    if brace is None:
        return []
    if close is None:
        return [("value", code[brace:entry[1]], brace)]
    return _outcome_items_in_block(
        code, brace + 1, close, (entry[0], entry[1]), ranges)


def _inline_outcome_items(arg):
    """Every exit outcome of an inline handler, or None.

    An inline function or arrow standing in the catch call
    itself is read from its own text when no range in the
    module stands under it, a block body by its complete
    outcomes and an expression body whole.
    """
    s = arg.strip()
    body = None
    body_offset = 0
    expression = None
    expression_offset = 0
    if s.startswith("function") or "=>" in s:
        arrow = _top_level_positions(s, ">")
        brace = s.find("{")
        if re.match(r"(?:async\s+)?function(?![\w$])", s):
            if brace == -1:
                return None
            body = s[brace:]
            body_offset = brace + 1
        elif arrow:
            rest_full = s[arrow[0][0] + 1:]
            rest = rest_full.strip()
            rest_offset = arrow[0][0] + 1 + (
                len(rest_full) - len(rest_full.lstrip()))
            if rest.startswith("{"):
                body = rest
                body_offset = rest_offset + 1
            else:
                expression = rest
                expression_offset = rest_offset
        else:
            return None
    else:
        return None
    if expression is not None:
        return [("value", expression, expression_offset)]
    close = matching_close(body, 0)
    if close is None:
        return None
    inner = body[1:close]
    return [
        (kind, value, pos + body_offset)
        for kind, value, pos in _outcome_items_in_block(
            inner, 0, len(inner), None, function_ranges(inner))
    ]


def _containing_scope(code, ranges, pos, exclude_span=None):
    """The function range holding a position, or None.

    A range can be excluded by its span, so a function
    standing in the ranges can be asked for the scope it
    itself stands in rather than for itself.
    """
    best = None
    for entry in ranges:
        if exclude_span is not None and \
                (entry[0], entry[1]) == exclude_span:
            continue
        if entry[0] <= pos <= entry[1] \
                and (best is None or entry[0] > best[0]):
            best = entry
    return best


def _classify_binding_value(code, ranges, name, rhs, rhs_start,
                              place):
    """The binding kind of one right hand side text.

    One classification for every binding spelling, a
    plain assignment, a declaration and a destructured
    value alike. A bare other name is an alias. A function
    standing in the ranges at the head of the text is a
    range. A function expression or an arrow the ranges
    do not name is its text. Anything else is another
    value, carried as its text.
    """
    rhs_end = rhs_start + len(rhs)
    stripped = rhs.strip()
    lead = len(rhs) - len(rhs.lstrip())
    abs_start = rhs_start + lead
    alias = re.fullmatch(r"([A-Za-z_$][\w$]*)", stripped)
    if alias and alias.group(1) != name:
        return ("alias", alias.group(1), None, (place, rhs_end))
    found = None
    for entry in ranges:
        if abs_start <= entry[0] < rhs_end and \
                code[abs_start:entry[0]].strip() in (
                    "", "async"):
            if entry[2] == name or found is None:
                found = entry
            if entry[2] == name:
                break
    if found is not None:
        return ("range", found, None, (found[0], found[1] + 1))
    if re.match(r"(?:async\s+)?function(?![\w$])",
                stripped) or "=>" in stripped:
        return ("text", None, rhs, (rhs_start, rhs_end))
    return ("other", None, rhs, (rhs_start, rhs_end))


def _destructuring_events(code, ranges, name):
    """The binding events a destructuring gives a name.

    A destructuring assignment and a destructuring
    declaration bind each name the pattern binds to the
    value standing at that name's own key path in the
    right hand side, so the one binding reading the plain
    spellings use judges the destructured spellings too.
    A name the right hand side names no value for, and a
    rest name, which binds a new object of the properties
    the named keys leave behind, read as a binding to
    another value. The patterns are found the way the
    file read walk finds them, under a declaration
    keyword or standing where a statement can stand.
    """
    events = []
    opens = set()
    for match in re.finditer(r"(?:const|let|var)\s*([\[{])", code):
        opens.add(match.end() - 1)
    tokens = _reach_tokens(code, 0, len(code), literal_spans(code))
    for index, (kind, word, _, _) in enumerate(tokens):
        if kind != "word" or word not in ("const", "let", "var"):
            continue
        depth = 0
        declarator = True
        for _, other, other_start, _ in tokens[index + 1:]:
            if other in ("(", "[", "{"):
                if declarator and depth == 0 and \
                        other in ("{", "["):
                    opens.add(other_start)
                depth += 1
                declarator = False
            elif other in (")", "]", "}"):
                depth -= 1
                if depth < 0:
                    break
            elif depth == 0 and other == ";":
                break
            elif depth == 0 and other == ",":
                declarator = True
            elif depth == 0 and other in (
                    "const", "let", "var", "in", "of"):
                break
            elif declarator and depth == 0:
                declarator = False
    for match in re.finditer(r"(?:^|[;()\n{}])\s*([\[{])", code):
        opens.add(match.end() - 1)
    for open_index in sorted(opens):
        close = matching_close(code, open_index)
        if close is None:
            continue
        rest = re.match(r"\s*=(?![=])\s*", code[close + 1:])
        if not rest:
            continue
        pattern = code[open_index:close + 1]
        keymap = pattern_key_map(pattern)
        if name not in [bound for bound, _ in keymap]:
            continue
        rhs_start = close + 1 + rest.end()
        rhs, _ = expression_at(code, rhs_start)
        for bound, keypath in keymap:
            if bound != name:
                continue
            if keypath and keypath[-1] == "..." + name:
                events.append((
                    open_index, 1,
                    ("other", None, rhs,
                     (rhs_start, rhs_start + len(rhs)))))
                continue
            current = rhs
            current_start = rhs_start
            walked = True
            for key in keypath:
                sub = object_property_value(current, key)
                if sub is None:
                    walked = False
                    break
                found_at = current.find(sub)
                if found_at != -1:
                    current_start += found_at
                current = sub
            if not walked:
                events.append((
                    open_index, 1,
                    ("other", None, rhs,
                     (rhs_start, rhs_start + len(rhs)))))
                continue
            events.append((
                open_index, 1,
                _classify_binding_value(
                    code, ranges, name, current, current_start,
                    open_index)))
    return events


def _binding_events(code, ranges, name):
    """Every binding event of a name, in the module text.

    Each event carries its place, a priority the range
    spellings hold over the assignment spellings at the
    same place, and its classified value, from the one
    collection the binding readings share, the function
    ranges, the plain assignments and the destructuring
    assignments and declarations between them.
    """
    events = []
    for entry in ranges:
        if entry[2] == name:
            events.append((
                entry[0], 2,
                ("range", entry, None, (entry[0], entry[1] + 1))))
    for match in _ASSIGNMENT.finditer(code):
        if match.group(1) != name:
            continue
        rhs, _ = expression_at(code, match.end())
        value = _classify_binding_value(
            code, ranges, name, rhs, match.end(), match.start())
        events.append((match.start(), 1, value))
    events.extend(_destructuring_events(code, ranges, name))
    return events


def _is_declaration(code, entry):
    """Whether a range entry is a function declaration.

    A declaration's head names the entry's own name after
    the function word, export and async spellings
    included, and the head stands where a statement can
    stand, after a brace, a semicolon, a closing brace or
    the start of the text, or under an export word. A
    function expression assigned to a name stands under
    that name in the ranges too, but its head follows an
    operator or a bracket, so it reads as the assignment
    it is, and a method's head carries no function word
    at all.
    """
    start, _, name = entry[0], entry[1], entry[2]
    if name is None:
        return False
    head = re.match(
        r"(?:export\s+(?:default\s+)?)?(?:async\s+)?"
        r"function\s*\*?\s*([A-Za-z_$][\w$]*)",
        code[start:])
    if head is None or head.group(1) != name:
        return False
    if code[start:start + 6] == "export":
        return True
    j = start - 1
    while j >= 0 and code[j].isspace():
        j -= 1
    if j < 0:
        return True
    if code[j] in "{;}":
        return True
    word_end = j + 1
    while j >= 0 and (code[j].isalnum() or code[j] in "_$"):
        j -= 1
    return code[j + 1:word_end] in ("export", "default")


def _binding_event_order(code, event):
    """The order key of one binding event in its scope.

    A function declaration binds when its scope is
    instantiated, before any statement of the scope runs,
    so a declaration event orders at the scope's start
    and every assignment spelling in the scope orders
    after it at its own place, wherever in the text the
    declaration stands. Two declarations order between
    themselves by their places, the later standing.
    """
    place, _, value = event
    if value[0] == "range" and _is_declaration(code, value[1]):
        return (0, 0, place)
    return (place, 1, place)


def _binding_value_at(code, ranges, name, pos, seen=frozenset()):
    """The function binding of a name as at a position.

    The rules are the file read walk's binding rules,
    stated for function values. A binding inside the
    function holding the position counts where it stands
    before the position, an assignment spelling at its
    written place and a function declaration wherever in
    the scope it stands, because a declaration binds when
    its scope is instantiated, and the pool is read in
    the order _binding_event_order states, where an
    assignment outranks a declaration and the later of
    two declarations stands. A module top level binding
    counts wherever it stands when the position stands
    inside a function, because the module loads whole
    before the host calls that function, and against a
    top level position a binding counts where it stands
    before that position under the same order, a
    declaration again wherever it stands. A binding in any other function
    counts for nothing. A binding inside a conditional
    branch of the holding function counts like any other
    binding in that function in its written order, the
    reading the file read walk gives assignments there.
    A destructuring assignment or declaration counts as
    a binding of each name its pattern binds, at the
    value standing at that name's key path in the right
    hand side, under these same rules. Returns a kind
    and its payload, a range entry for a
    function standing in the ranges, the text of a
    function expression or arrow bound by an assignment,
    or the text of a rebinding to a value that is no
    function, or None where no binding stands.
    """
    if name in seen:
        return None
    events = _binding_events(code, ranges, name)
    here = enclosing_function(code, pos, ranges)
    scoped = []
    top = []
    for place, priority, value in events:
        exclude = None
        if value[0] == "range":
            exclude = (value[1][0], value[1][1])
        scope = _containing_scope(code, ranges, place, exclude)
        if here is not None:
            if scope is not None and \
                    (scope[0], scope[1]) == (here[0], here[1]):
                if place < pos or (value[0] == "range" and
                        _is_declaration(code, value[1])):
                    scoped.append((place, priority, value))
            elif scope is None:
                top.append((place, priority, value))
        elif scope is None and \
                (place < pos or (value[0] == "range" and
                 _is_declaration(code, value[1]))):
            scoped.append((place, priority, value))
    pool = scoped or top
    if not pool:
        return None
    _, _, value = max(
        pool, key=lambda event: _binding_event_order(
            code, event))
    if value[0] == "alias":
        return _binding_value_at(
            code, ranges, value[1], value[3][0], seen | {name})
    return value


def _handler_reading(code, ranges, arg_start, arg_end, at=None):
    """The outcomes and body of the handler an argument names.

    The argument names a handler under a bound name, judged
    by its binding as at the position the caller names, or
    it stands as an inline function or arrow in the call,
    or a range inside the argument stands for it. Returns
    the outcome items, the handler body text and the span
    the handler text stands in, or None where no handler
    the pin can read stands behind the argument. A handler
    rebound to a value that is no function reads as an
    empty outcome list, which no judgement can certify.
    The reading also carries the text and ranges its
    outcomes are judged in, and the module reading a
    handler text read on its own falls back to for the
    names that text does not itself hold.
    """
    if at is None:
        at = arg_start
    arg = code[arg_start:arg_end]
    name = arg.strip()
    if re.fullmatch(r"[A-Za-z_$][\w$]*", name):
        binding = _binding_value_at(code, ranges, name, at)
        if binding is None:
            return None
        kind, entry, text, span = binding
        if kind == "range":
            return (
                _handler_outcome_items(code, entry, ranges),
                code[entry[0]:entry[1] + 1], span,
                code, ranges, None)
        if kind == "text":
            stripped = text.strip()
            return (
                _inline_outcome_items(stripped), text, span,
                stripped, function_ranges(stripped),
                (code, ranges, span[0]))
        return ([], text, span, code, ranges, None)
    inside = [
        candidate for candidate in ranges
        if arg_start <= candidate[0]
        and candidate[1] <= arg_end
    ]
    if inside:
        entry = min(inside, key=lambda c: (c[0], -c[1]))
        return (
            _handler_outcome_items(code, entry, ranges),
            code[entry[0]:entry[1] + 1],
            (entry[0], entry[1] + 1), code, ranges, None)
    stripped = arg.strip()
    items = _inline_outcome_items(stripped)
    if items is None:
        return None
    return (
        items, arg, (arg_start, arg_end),
        stripped, function_ranges(stripped),
        (code, ranges, arg_start))


def _catch_denies(code, ranges, arg_start, arg_end, at=None):
    """Whether the catch argument's handler returns deny.

    The argument names a handler the module defines, as a
    function declaration, a function expression or an arrow
    under a bound name, judged by its binding as at the
    registration call, or it stands as an inline function
    or arrow in the call. Every outcome the handler can
    produce must carry the deny shape, and every exit of
    the handler counts as an outcome, each return
    expression, each bare return, each throw no catch
    inside the handler answers, and the end of the body
    where control can reach it. Returns None when no
    handler the pin can read stands behind the argument.
    """
    reading = _handler_reading(
        code, ranges, arg_start, arg_end, at)
    if reading is None:
        return None
    outcomes, _, _, judge_code, judge_ranges, fallback = reading
    if outcomes is None:
        return None
    if not outcomes:
        return False
    return all(
        kind == "value" and _value_carries_deny(
            value, judge_code, judge_ranges, value_pos,
            fallback=fallback)
        for kind, value, value_pos in outcomes)


def _gating_problem(code, ranges, handler_span, at):
    """The problem with a registration's gating handler.

    The handler a registration registers must be the
    gating handler the call pins judge. It reads as one
    where the functions it reaches through bare local
    calls that actually stand in its own code, its own
    body included, between them call the environment
    read and the file read, and where one of its own
    outcomes produces the deny shape. A callee actually
    stands where the shared completion calculus classes
    the call's place as reached in its unit's flow, so a
    callee called only on a governed branch counts for
    nothing, and a call itself counts for the presence
    question where its place classes as reached or as
    branch in its unit, never where its sequence has
    closed or inside a nested function the unit does not
    reach, so calls standing dead after a callee's own
    return count for nothing, the reach questions the
    calculus exists to answer. The calls are
    judged the way the call pins judge them, as call
    sites standing in code position outside every
    literal span, in the unit's own code, so a call
    spelling quoted inside a string or a template text,
    or standing inside a nested function the handler
    never calls, counts for nothing. A handler that
    approves every spawn reaches none of those calls and
    produces no deny outcome. Returns None where the
    handler gates as the shipped one does.
    """
    arg_start, arg_end = handler_span
    reading = _handler_reading(
        code, ranges, arg_start, arg_end, at)
    message = (
        "the agent.spawn hook registers a handler that "
        "does not gate on the packet manifest, so a spawn "
        "over a packet the manifest does not verify would "
        "proceed ungated"
    )
    if reading is None:
        return message
    outcomes, _, span, judge_code, judge_ranges, fallback = \
        reading
    if span is None:
        return message

    def flow_class(unit_span, unit_entry, place):
        if unit_entry is None:
            return "reached"
        return _flow_class(code, unit_entry, place)

    collected = {span: _unit_entry(code, ranges, span)}
    changed = True
    while changed:
        changed = False
        for unit_span, unit_entry in list(collected.items()):
            intervals = _own_intervals(
                code, ranges, unit_span, unit_entry,
                set(collected))
            for start, end in intervals:
                segment = code[start:end]
                for call in re.finditer(
                        r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(",
                        segment):
                    place = start + call.start()
                    if code[:place].rstrip(
                            ).endswith("function"):
                        continue
                    if flow_class(
                            unit_span, unit_entry,
                            place) != "reached":
                        continue
                    binding = _binding_value_at(
                        code, ranges, call.group(1), place)
                    if binding is None:
                        continue
                    kind, entry, _, callee_span = binding
                    if kind in ("range", "text") and \
                            callee_span is not None and \
                            callee_span not in collected:
                        collected[callee_span] = entry \
                            if kind == "range" else \
                            _unit_entry(code, ranges, callee_span)
                        changed = True
    unit_intervals = {}
    for unit_span, unit_entry in collected.items():
        unit_intervals[unit_span] = _own_intervals(
            code, ranges, unit_span, unit_entry, set(collected))
    literal = literal_spans(code)

    def has_call(pattern):
        for unit_span, unit_entry in collected.items():
            for start, end in unit_intervals[unit_span]:
                for match in pattern.finditer(code, start, end):
                    if any(opening <= match.start() <= closing
                           for opening, closing in literal):
                        continue
                    if flow_class(
                            unit_span, unit_entry,
                            match.start()) in (
                            "reached", "branch"):
                        return True
        return False

    if not has_call(re.compile(
            r"\$\s*\.\s*env\s*\.\s*get\s*\(")) \
            or not has_call(re.compile(
                r"\$\s*\.\s*fs\s*\.\s*read\s*\(")):
        return message
    if outcomes is None or not any(
            kind == "value" and _value_can_carry_deny(
                value, judge_code, judge_ranges, value_pos,
                fallback=fallback)
            for kind, value, value_pos in outcomes):
        return message
    return None


def _unit_entry(code, ranges, span):
    """The range a unit span stands for, where one stands.

    A range unit's span is the range itself. A text unit's
    span is a right hand side whose head is the function
    the unit reads, so the range opening there is the
    unit's own. Any other span stands for no range.
    """
    for entry in ranges:
        if (entry[0], entry[1] + 1) == span:
            return entry
    for entry in ranges:
        if span[0] <= entry[0] and entry[1] < span[1] and \
                code[span[0]:entry[0]].strip() in ("", "async"):
            return entry
    return None


def _immediately_invoked(code, entry):
    """Whether a function is called at its own site.

    The walk is the one the parameter reading already
    holds for an unnamed function, from the function's
    end over an optional closing brace and one closing
    parenthesis to the call's opening parenthesis. A
    function standing as a declaration is never invoked
    by a parenthesis after it, since the parenthesis
    opens a separate statement there, so a declaration
    reads as not invoked whatever follows it, which the
    backwards scan for a statement position decides.
    """
    i = entry[0]
    j = i - 1
    while j >= 0 and code[j].isspace():
        j -= 1
    if j < 0 or code[j] in "{;}":
        return False
    word_end = j + 1
    while j >= 0 and (code[j].isalnum() or code[j] in "_$"):
        j -= 1
    if code[j + 1:word_end] in ("export", "default"):
        return False
    i = entry[1]
    while i < len(code) and code[i].isspace():
        i += 1
    if code[i:i + 1] == "}":
        i += 1
        while i < len(code) and code[i].isspace():
            i += 1
    if code[i:i + 1] == ")":
        i += 1
        while i < len(code) and code[i].isspace():
            i += 1
    return code[i:i + 1] == "("


def _own_intervals(code, ranges, unit_span, unit_entry,
                   collected_spans):
    """The intervals of a unit's own code.

    The unit's own code is its body, for a range the block
    between its braces or its expression body, and for a
    text with no range the text itself. The body of any
    other function standing inside it is not its own code,
    so the calls and call sites inside a nested function
    the unit never reaches through a bare local call count
    for nothing, and a nested function the walk does reach
    is a unit of its own, judged on its own intervals. A
    function the unit invokes at the very site where it
    stands is the exception, since its body runs as part
    of the unit's own execution, so its body stays in the
    unit's own code.
    """
    if unit_entry is not None:
        brace, close = _function_body_brace(code, unit_entry)
        if brace is None:
            base = [(unit_span[0], unit_span[1])]
        elif close is None:
            base = [(brace, unit_entry[1])]
        else:
            base = [(brace + 1, close)]
    else:
        base = [(unit_span[0], unit_span[1])]
    intervals = base
    for entry in ranges:
        entry_span = (entry[0], entry[1] + 1)
        if entry_span == unit_span or \
                entry_span in collected_spans:
            continue
        if unit_entry is not None and entry_span == (
                unit_entry[0], unit_entry[1] + 1):
            continue
        if _immediately_invoked(code, entry):
            continue
        start, end = entry[0], entry[1] + 1
        remaining = []
        for a, b in intervals:
            if end <= a or start >= b:
                remaining.append((a, b))
                continue
            if a < start:
                remaining.append((a, start))
            if end < b:
                remaining.append((end, b))
        intervals = remaining
    return intervals


_REACH_OPERATORS = (
    "===", "!==", ">>>", "<<=", ">>=", "**=", "&&=", "||=",
    "??=", "...", "=>", "==", "!=", "<=", ">=", "&&", "||",
    "??", "?.", "++", "--", "<<", ">>", "**", "+=", "-=",
    "*=", "/=", "%=", "&=", "|=", "^=",
)


def _reach_tokens(code, start, end, spans):
    """The significant tokens of a code range, in order.

    Literal spans are skipped whole, so a word or a brace
    inside a string, a template text or a regex is no
    token. Each token carries its kind, its text and its
    start and end positions.
    """
    span_ends = {opening: closing for opening, closing in spans}
    tokens = []
    i = start
    while i < end:
        if i in span_ends:
            i = span_ends[i] + 1
            continue
        ch = code[i]
        if ch.isspace():
            i += 1
            continue
        word = re.match(r"[A-Za-z_$][\w$]*", code[i:end])
        if word:
            tokens.append(
                ("word", word.group(0), i, i + word.end()))
            i += word.end()
            continue
        number = re.match(r"\d[\w.]*", code[i:end])
        if number:
            tokens.append(
                ("number", number.group(0), i, i + number.end()))
            i += number.end()
            continue
        operator = None
        for candidate in _REACH_OPERATORS:
            if code.startswith(candidate, i):
                if candidate == "?." and \
                        code[i + 2:i + 3].isdigit():
                    continue
                operator = candidate
                break
        if operator is not None:
            tokens.append(("op", operator, i, i + len(operator)))
            i += len(operator)
            continue
        tokens.append(("char", ch, i, i + 1))
        i += 1
    return tokens


def _governed_before(text):
    """Whether a governing operator stands at a text's top level.

    A conditional or logical operator at the top level of
    the text before a call governs what follows it, so a
    call behind one stands on the governed side. Operators
    inside brackets govern only what stands inside those
    brackets, and are read when the walk descends there.
    """
    tokens = _reach_tokens(text, 0, len(text), literal_spans(text))
    depth = 0
    for _, token, _, _ in tokens:
        if token in ("(", "[", "{"):
            depth += 1
        elif token in (")", "]", "}"):
            depth -= 1
        elif depth == 0 and token in ("?", "&&", "||", "??"):
            return True
    return False


def _expression_verdict(text, rel):
    """Where a call stands inside one expression text.

    The call's own comma separated segment is the text
    that governs it, because a comma ends the expression
    segment it stands in, so an operator in an earlier
    segment governs nothing in a later one. Inside the
    segment, a governing operator at the segment's top
    level before the call makes the call governed, and a
    call inside a bracketed part is judged inside that
    part by the same reading, to the innermost bracket.
    A call standing as a later call argument, a later
    object value or a later comma operand is reached.
    """
    parts = split_top_level(text)
    offset = 0
    segment = None
    segment_rel = rel
    for part in parts:
        if offset <= rel <= offset + len(part):
            segment = part
            segment_rel = rel - offset
            break
        offset += len(part) + 1
    if segment is None:
        segment = parts[-1] if parts else text
        segment_rel = rel - (len(text) - len(segment))
    if _governed_before(segment[:segment_rel]):
        return "branch"
    tokens = _reach_tokens(
        segment, 0, len(segment), literal_spans(segment))
    innermost = None
    for _, token, tok_start, _ in tokens:
        if tok_start >= segment_rel:
            break
        if token not in ("(", "[", "{"):
            continue
        close = matching_close(segment, tok_start)
        if close is not None and tok_start < segment_rel < close:
            if innermost is None or tok_start > innermost[0]:
                innermost = (tok_start, close)
    if innermost is not None:
        open_index, close_index = innermost
        return _expression_verdict(
            segment[open_index + 1:close_index],
            segment_rel - open_index - 1)
    return "reached"


def _reach_in_statement(code, start, end, call_start):
    """Where a call stands inside one statement.

    A plain block and a try block and a finally block are
    flow, read as the sequence they hold. An if or else
    branch, a loop body, a switch block and a catch block
    are governed ground, as is a call in the body of a
    with statement. A do body is flow, because a do body
    runs at least once before its condition is read. A
    call in a statement head, the condition of an if or a
    loop or the binding of a catch, is judged as an
    expression standing there. Every other statement is
    judged as the expression it carries.
    """
    text = code[start:end]
    stripped = text.lstrip()
    lead = len(text) - len(stripped)
    label = re.match(r"([A-Za-z_$][\w$]*)\s*:(?!:)", stripped)
    if label is not None:
        return _reach_in_statement(
            code, start + lead + label.end(), end, call_start)
    if stripped.startswith("{"):
        open_index = start + lead
        close = matching_close(code, open_index)
        if close is None:
            return "reached"
        return _reach_in_sequence(
            code, open_index + 1, close, call_start)
    word, word_end = _leading_word(stripped)
    word_start = start + lead
    if word in ("if", "for", "while", "switch", "with", "catch"):
        open_paren = code.find("(", word_start + word_end, end)
        if open_paren == -1:
            return "branch"
        close = matching_close(code, open_paren)
        if close is None:
            return "branch"
        if open_paren <= call_start <= close:
            return _expression_verdict(
                code[open_paren + 1:close],
                call_start - open_paren - 1)
        if word == "catch":
            return _reach_in_statement(
                code, close + 1, end, call_start)
        return "branch"
    if word == "do":
        rest_start = word_start + word_end
        _, used = _whole_statement(code[rest_start:end])
        if rest_start <= call_start < rest_start + used:
            return _reach_in_statement(
                code, rest_start, rest_start + used, call_start)
        return _expression_verdict(
            code[rest_start + used:end],
            call_start - rest_start - used)
    if word == "try":
        pos = word_start + word_end
        _, used = _first_statement(code[pos:end])
        if pos <= call_start < pos + used:
            return _reach_in_statement(
                code, pos, pos + used, call_start)
        pos += used
        while code[pos:end].strip():
            segment = code[pos:end]
            seg_word, seg_end = _leading_word(segment.strip())
            seg_lead = len(segment) - len(segment.lstrip())
            seg_start = pos + seg_lead + seg_end
            if seg_word == "catch":
                probe = seg_start
                while probe < end and code[probe].isspace():
                    probe += 1
                if probe < end and code[probe] == "(":
                    paren_close = matching_close(code, probe)
                    if paren_close is not None and \
                            probe <= call_start <= paren_close:
                        return _expression_verdict(
                            code[probe + 1:paren_close],
                            call_start - probe - 1)
                    if paren_close is not None:
                        seg_start = paren_close + 1
                _, seg_used = _first_statement(code[seg_start:end])
                if seg_start <= call_start < seg_start + seg_used:
                    return "branch"
                pos = seg_start + seg_used
            elif seg_word == "finally":
                _, seg_used = _first_statement(code[seg_start:end])
                if seg_start <= call_start < seg_start + seg_used:
                    return _reach_in_statement(
                        code, seg_start, seg_start + seg_used,
                        call_start)
                pos = seg_start + seg_used
            else:
                break
        return "reached"
    if word in ("function", "class"):
        return "nested"
    return _expression_verdict(text, call_start - start)


def _reach_in_sequence(code, start, end, call_start):
    """Where a call stands inside a statement sequence.

    Each statement before the one holding the call is
    read through the shared completion calculus, and a
    statement that cannot fall closes the flow, whether
    it closes by a return, by a throw, by both branches
    of an if, by a returning catch answering a throwing
    try, or by a switch whose clauses all close. The
    statement holding the call is judged by its own
    shape.
    """
    pos = start
    while pos < end:
        statement, used = _whole_statement(code[pos:end])
        if not used:
            break
        if pos <= call_start < pos + used:
            return _reach_in_statement(
                code, pos, pos + used, call_start)
        if statement.strip() and \
                "fall" not in _statement_exits(statement):
            return "after_return"
        pos += used
    return "reached"


def _registration_reach(code, ranges, register_entry, call_start):
    """Where a registration call stands in its register flow.

    The rules, as this judgement states them. The call
    must stand in the statement flow of the register
    entry itself, not inside a function nested in it and
    not outside it. Inside that flow it must not stand
    inside a conditional branch, an if or else branch, a
    loop body, a switch block, a catch block, or the
    governed side of a conditional or logical expression,
    and it must not stand after a statement that cannot
    fall in the sequence it stands in, read through the
    one completion calculus the outcome walk reads. A
    plain block counts as reached, a statement level try
    block counts as reached, and a finally block counts
    as reached, because each of those runs on the path
    register always takes, and a do body counts as
    reached because it runs at least once. A conditional
    return does not close the flow, because the path
    that skips it reaches what follows. Returns one of
    reached, branch, after_return, nested or outside.
    """
    holder = enclosing_function(code, call_start, ranges)
    if holder is None:
        return "outside"
    if (holder[0], holder[1]) != \
            (register_entry[0], register_entry[1]):
        return "nested"
    brace, close = _function_body_brace(code, register_entry)
    if brace is None:
        return "outside"
    if close is None:
        return _expression_verdict(
            code[brace:register_entry[1]],
            call_start - brace)
    return _reach_in_sequence(code, brace + 1, close, call_start)


def _catch_argument(code, start):
    """The catch argument span on a call's own chain.

    Walks from just after a call's closing parenthesis
    over the spaced catch spelling the brief allows, and
    returns the first argument's span where a catch
    stands on the chain, or None where none does. The
    one walk the registration judgement and the deny
    name derivation share.
    """
    i = start
    while i < len(code) and code[i].isspace():
        i += 1
    if i >= len(code) or code[i] != ".":
        return None
    j = i + 1
    while j < len(code) and code[j].isspace():
        j += 1
    if not code.startswith("catch", j) or (
            code[j + 5:j + 6].isalnum()
            or code[j + 5:j + 6] in "_$"):
        return None
    k = j + len("catch")
    while k < len(code) and code[k].isspace():
        k += 1
    if code[k:k + 1] != "(":
        return None
    catch_args = argument_spans(code, k)
    if not catch_args:
        return None
    return catch_args[0]


def _registration_calls(code, ranges):
    """The registration calls naming the agent.spawn literal.

    A call counts when its head is the registrar the module
    hands to its register function, or the plain on name
    the shipped register uses, standing in code outside
    every literal span, and its first argument is a string
    literal whose decoded contents are the agent.spawn
    event name, standing alone. An escaped spelling of the
    event name therefore counts as the event the host
    reads, as the host judges the literal by its decoded
    contents. Each entry carries the call's start, its
    opening parenthesis, its argument spans and its
    closing parenthesis index.
    """
    names = {"on"}
    for entry in ranges:
        if entry[2] == "register" and entry[3]:
            for bound, keypath in entry[3][0][3]:
                if not keypath:
                    names.add(bound)
    spans = literal_spans(code)
    found = []
    for name in sorted(names):
        for match in re.finditer(
                r"(?<![\w$.])" + re.escape(name) + r"\s*\(",
                code):
            if any(start <= match.start() <= end
                    for start, end in spans):
                continue
            open_paren = match.end() - 1
            args = argument_spans(code, open_paren)
            if args is None or len(args) < 1:
                continue
            first = code[args[0][0]:args[0][1]].strip()
            literal = literal_at(first, 0)
            if literal is None or _decode_string_contents(
                    literal[0]) != "agent.spawn" \
                    or literal[1] != len(first):
                continue
            close = matching_close(code, open_paren)
            if close is None:
                continue
            found.append((match.start(), open_paren, args, close))
    found.sort()
    return found


def registration_problems(code):
    """Problems with the spawn registration and its catch.

    The judgement reads the stripped, decoded code the
    other pins read, never the raw source, so a comment or
    a string carrying the registration, catch or deny
    spellings certifies nothing. Every registration call
    for the event is judged. Each one must stand in the
    statement flow of the register function, must register
    the gating handler, must be the only registration for
    the event, must carry a catch on its own chain, and
    the handler that catch names must produce a deny
    object on every outcome it can produce.
    """
    ranges = function_ranges(code)
    calls = _registration_calls(code, ranges)
    if not calls:
        return [
            "the hooks module registers no agent.spawn hook "
            "with a string literal event name"
        ]
    register_entry = None
    candidates = [
        entry for entry in ranges if entry[2] == "register"]
    for entry in candidates:
        holders = [
            other for other in ranges
            if other is not entry
            and other[0] <= entry[0] and entry[1] <= other[1]
            and (other[0], other[1]) != (entry[0], entry[1])
        ]
        if not holders:
            register_entry = entry
            break
    if register_entry is None and candidates:
        register_entry = candidates[0]
    problems = []

    def add(message):
        if message not in problems:
            problems.append(message)

    if len(calls) > 1:
        add(
            "the hooks module registers the agent.spawn "
            "hook more than once, so the host refuses the "
            "module at load and every spawn would pass "
            "ungated"
        )
    for call_start, open_paren, args, close in calls:
        if register_entry is None:
            reach = "outside"
        else:
            reach = _registration_reach(
                code, ranges, register_entry, call_start)
        if reach == "branch":
            add(
                "the agent.spawn registration stands inside "
                "a conditional branch in the register "
                "function, so it does not stand on the path "
                "the register function always takes and no "
                "spawn gate is registered on that path"
            )
        elif reach == "after_return":
            add(
                "the agent.spawn registration stands after "
                "a return in the register function, so the "
                "register function never reaches it and no "
                "spawn gate is registered"
            )
        elif reach != "reached":
            add(
                "the agent.spawn registration does not "
                "stand in the statement flow of the register "
                "function, so the host calling that function "
                "never performs it and no spawn gate is "
                "registered"
            )
        if len(args) >= 2:
            gating = _gating_problem(
                code, ranges,
                (args[1][0], args[1][1]), call_start)
            if gating is not None:
                add(gating)
        else:
            add(
                "the agent.spawn hook registers a handler that "
                "does not gate on the packet manifest, so a spawn "
                "over a packet the manifest does not verify would "
                "proceed ungated"
            )
        i = close + 1
        catch_arg = _catch_argument(code, i)
        caught = catch_arg is not None
        verdict = None
        if caught:
            verdict = _catch_denies(
                code, ranges,
                catch_arg[0], catch_arg[1],
                call_start)
        if not caught:
            add(
                "the agent.spawn hook carries no .catch handler, "
                "so a hook crash would fail open"
            )
        elif verdict is None:
            add(
                "the .catch handler stands in a form the "
                "structural reading cannot read, as a function "
                "declaration, a function expression or an arrow "
                "under a bound name, or an inline function or "
                "arrow in the call itself"
            )
        elif not verdict:
            add(
                "the .catch handler returns no deny shape, so a hook "
                "crash would not fail closed"
            )
    return problems


# Keywords after which an expression, and so a regex literal,
# is expected. The set holds every keyword an expression can
# directly follow in the grammar, the expression operators
# and the statement heads that take an expression or a
# statement, with default for the export default form whose
# value is an expression and extends for the class heritage
# expression. Any other word, a number, a member name spelled
# after a dot (where a keyword spelling is a plain property
# name) and the operand keywords this, super, true, false and
# null end an expression, so a slash after one is division.
_REGEX_AFTER_KEYWORDS = frozenset({
    "await", "case", "default", "delete", "do", "else",
    "export", "extends", "in", "instanceof", "new", "of",
    "return", "throw", "typeof", "void", "yield",
})


# Words that open a parenthesised head a statement or a block
# answers, so the parenthesis closing one leaves a statement
# to start and a slash after it opens a regex, where a
# parenthesis closing an expression is an operand and a slash
# after it is division.
_CONTROL_HEAD_WORDS = frozenset({
    "catch", "for", "if", "switch", "while", "with",
})

# Words after which a brace opens a block rather than an
# object literal, because the brace is the body the word
# governs and no expression stands there.
_BLOCK_WORDS = frozenset({"do", "else"})


class _SlashContext:
    """Whether a slash opens a regex, by previous token.

    The one judgement every walk in this gate shares, the
    stripper, the decoder and the span walk among the charged
    pins and the argument, splitting, matching, expression
    and parameter walks behind them, so no walk in the file
    judges a slash by a private character reading. A slash
    is judged by the previous significant token, by the kind
    of the bracket it stands inside, and by four wider
    facts the grammar decides from beyond the previous
    token. A colon is judged by the construct it stands in,
    so the brace after a colon heading a label, a case or a
    default block is a block, while the brace after a value
    colon, inside an object, a parenthesis, a bracket, an
    interpolation or a conditional branch, is an object. A
    dot that closes a decimal number token is part of the
    number, so a slash after a trailing dot number is
    division. A function or class word is judged by the
    position it stands in, so the brace closing a function
    or class expression is an operand while the brace
    closing a declaration is a block end. A line terminator
    after the return word or the yield word ends the
    expression that word opens, so a brace after one is a
    block. The throw word carries no such fact, because a
    line terminator after throw is an error in the grammar
    rather than the end of its expression. A slash opens a regex only
    where an expression can start. After an expression
    ending token, an identifier or number, a string,
    template or regex literal, a closing bracket, or a
    postfix ++ or --, a slash is division. After an
    operator, or after a keyword that expects an
    expression, a slash opens a regex. A closing
    parenthesis is judged by the parenthesis it closes, so
    one ending a control head from if, while, for, with,
    switch or catch leaves a statement to start and a slash
    after it opens a regex, and one ending an expression is
    an operand and a slash after it is division. A closing
    brace is judged by the brace it closes, so one ending
    an object literal or a function or class expression is
    an operand and a slash after it is division, and one
    ending a block leaves a statement to start and a slash
    after it opens a regex. A brace opens an object literal
    where it stands in expression position, after an
    operator, an opening parenthesis or bracket, a comma, a
    value colon, an equals sign or a keyword that expects
    an expression, and it opens a block where it stands in
    statement position, after a statement word, a closing
    bracket of any kind, an operand, an arrow, a colon
    heading a label or a case or default block, or a line
    terminated return or yield. The tracker therefore keeps a stack
    of the brackets it stands inside recording the kind
    each one opened as and the conditional branches each
    level carries, it keeps the pending word whole, so
    return reads as the keyword and a longer identifier
    does not, and it pairs two signs into one postfix token
    where the token before them ended an expression and
    into a prefix token where it did not, so a single sign
    character never decides on its own the way the old
    previous character set did.
    """

    def __init__(self):
        self.kind = "operator"
        self.word = ""
        self._word_member = False
        self._after_dot = False
        self._pending_sign = None
        self._brackets = []
        self._prev = ("start",)
        self._prev_char = ""
        self._equals_single = False
        self._word_prev = ("start",)
        self._word_kind = "operator"
        self._word_colon = False
        self._async_ctx = (("start",), "operator", False)
        self._colon_value = False
        self._top_ternary = 0
        self._q_pending = False
        self._q_dot_pending = False
        self._after_restricted = False
        self._restricted_asi = False
        self._pending_expr_bodies = []

    def _ternary(self):
        if self._brackets:
            return self._brackets[-1][2]
        return self._top_ternary

    def _bump_ternary(self, delta):
        if self._brackets:
            frame = self._brackets[-1]
            frame[2] = max(0, frame[2] + delta)
        else:
            self._top_ternary = max(0, self._top_ternary + delta)

    def _resolve_questions(self, ch):
        """Settle a pending question mark against its next token.

        A question mark directly followed by a dot is an
        optional chain step unless a digit follows the dot,
        where the pair is a conditional head and a decimal
        number. A question mark pair is the nullish
        operator and counts no branch. Any other next token
        leaves the mark standing as a conditional head.
        """
        if self._q_dot_pending:
            if not (ch and ch.isdigit()):
                self._bump_ternary(-1)
            self._q_dot_pending = False
        if ch != ".":
            self._q_pending = False

    def _expression_position(self):
        """Whether a function or class word here is an expression.

        The word's own standing decides, read from the token
        recorded before the word started. A declaration
        position, the start of the walk, a semicolon, a
        block opening, a control head close, a block colon
        or a word the word follows as a statement, answers
        no. An operator, an opening bracket, an arrow, a
        value colon or a keyword that expects an expression
        answers yes. The word async hands its own standing
        on to the function word after it, and an export or
        default word before either makes a declaration.
        """
        prev, kind, colon = \
            self._word_prev, self._word_kind, self._word_colon
        if prev[0] == "word" and prev[1] == "async" and not prev[2]:
            prev, kind, colon = self._async_ctx
        if prev[0] == "word":
            if prev[2]:
                return False
            if prev[1] in ("export", "default"):
                return False
            return prev[1] in _REGEX_AFTER_KEYWORDS
        if prev[0] in ("open_paren", "open_bracket", "open_interp"):
            return True
        if prev[0] == "open_brace":
            return prev[1]
        if prev[0] == "arrow":
            return True
        if prev[0] == "char":
            if prev[1] == ":":
                return colon
            return prev[1] != ";"
        return False

    def _finish_word(self):
        if not self.word:
            return
        if self._word_member or \
                self.word not in _REGEX_AFTER_KEYWORDS:
            self.kind = "operand"
        else:
            self.kind = "operator"
        self._prev = ("word", self.word, self._word_member)
        if self.word == "async" and not self._word_member:
            self._async_ctx = (
                self._word_prev, self._word_kind, self._word_colon)
        if self.word in ("return", "yield") and not self._word_member:
            self._after_restricted = True
            self._restricted_asi = False
        else:
            self._after_restricted = False
        if not self._word_member and \
                self.word in ("function", "class"):
            self._pending_expr_bodies.append((
                len(self._brackets), self._expression_position()))
        self.word = ""
        self._word_member = False

    def opens_regex(self):
        """Whether a slash at the current position opens one."""
        if self.word:
            return not self._word_member and \
                self.word in _REGEX_AFTER_KEYWORDS
        return self.kind != "operand"

    def mark_operand(self):
        """Record a literal that has just closed."""
        self._resolve_questions("")
        self._finish_word()
        self.kind = "operand"
        self._pending_sign = None
        self._after_dot = False
        self._after_restricted = False
        self._restricted_asi = False
        self._prev = ("literal",)
        self._prev_char = ""

    def feed_separator(self, newline=False):
        """Record whitespace or a comment between tokens.

        A line terminator in the run is the one fact the
        restricted production judgement needs, so the walks
        name it where the run carries one, in whitespace
        itself or inside a comment the run spans.
        """
        if self._q_dot_pending:
            self._bump_ternary(-1)
            self._q_dot_pending = False
        self._q_pending = False
        self._finish_word()
        if newline and self._after_restricted:
            self._restricted_asi = True
        self._pending_sign = None
        self._prev_char = ""

    def _brace_is_object(self):
        """Whether a brace opening here opens an object.

        The position the brace stands in decides, read from
        the previous significant token the tracker recorded.
        A colon answers by the value flag the colon itself
        recorded in its construct, and a return or yield
        word answers by whether a line terminator followed
        it.
        """
        prev = self._prev
        if prev[0] == "word":
            if prev[2] or prev[1] in _BLOCK_WORDS:
                return False
            if prev[1] in ("return", "yield"):
                return not self._restricted_asi
            return prev[1] in _REGEX_AFTER_KEYWORDS
        if prev[0] in ("open_paren", "open_bracket",
                       "open_interp"):
            return True
        if prev[0] == "char":
            if prev[1] == ":":
                return self._colon_value
            return prev[1] not in ";."
        return False

    def open_interpolation(self):
        """Record the brace a template interpolation opens.

        The brace holds an expression, so a brace opening
        inside it stands in expression position, and the
        brace closing it returns the walk to the template
        text the literal close then records as an operand.
        The walkers announce the opening through here rather
        than feeding a plain brace, so the one shared stack
        stays balanced without any walker reading brackets
        on its own.
        """
        self._finish_word()
        self._brackets.append(["interp", False, 0, False])
        self.kind = "operator"
        self._pending_sign = None
        self._after_dot = False
        self._prev = ("open_interp",)
        self._prev_char = "{"

    def feed(self, ch):
        """Record one significant character standing in code."""
        if ch.isspace():
            self.feed_separator(
                ch in "\n\r\u2028\u2029")
            return
        if ch.isalpha() or ch.isdigit() or ch in "_$" \
                or ord(ch) > 127:
            if not self.word:
                self._resolve_questions(ch)
                self._word_member = self._after_dot \
                    and not ch.isdigit()
                self._word_prev = self._prev
                self._word_kind = self.kind
                self._word_colon = self._colon_value
                self._after_restricted = False
                self._restricted_asi = False
            self.word += ch
            self._pending_sign = None
            self._after_dot = False
            self._prev_char = ""
            return
        if ch == "." and self.word and all(
                c.isdigit() or c == "_" for c in self.word):
            # A dot closing a decimal number token is part
            # of the number, so the number stands whole as
            # an operand and a slash after it is division. A
            # name after the dot is a member name, the same
            # reading a member dot hands on, and a second dot
            # after digits is a member dot again.
            self._resolve_questions(ch)
            self._finish_word()
            self.kind = "operand"
            self._pending_sign = None
            self._after_dot = True
            self._prev = ("numberdot",)
            self._prev_char = ch
            self._after_restricted = False
            self._restricted_asi = False
            return
        self._resolve_questions(ch)
        self._finish_word()
        if ch in "+-":
            if self._pending_sign is not None \
                    and self._pending_sign[0] == ch:
                self.kind = "operand" \
                    if self._pending_sign[1] == "operand" \
                    else "operator"
                self._prev = ("postfix",) \
                    if self.kind == "operand" else ("prefix",)
                self._pending_sign = None
            else:
                self._pending_sign = (ch, self.kind)
                self.kind = "operator"
                self._prev = ("char", ch)
            self._after_dot = False
            self._prev_char = ch
            self._after_restricted = False
            self._restricted_asi = False
            return
        self._pending_sign = None
        self._after_dot = False
        if ch == "(":
            control = self._prev[0] == "word" \
                and not self._prev[2] \
                and self._prev[1] in _CONTROL_HEAD_WORDS
            self._brackets.append(["paren", control, 0, False])
            self.kind = "operator"
            self._prev = ("open_paren", control)
            self._prev_char = ch
        elif ch == ")":
            control = False
            if self._brackets \
                    and self._brackets[-1][0] == "paren":
                control = self._brackets.pop()[1]
            self.kind = "operator" if control else "operand"
            self._prev = ("close_paren", control)
            self._prev_char = ch
        elif ch == "[":
            self._brackets.append(["bracket", False, 0, False])
            self.kind = "operator"
            self._prev = ("open_bracket",)
            self._prev_char = ch
        elif ch == "]":
            if self._brackets \
                    and self._brackets[-1][0] == "bracket":
                self._brackets.pop()
            self.kind = "operand"
            self._prev = ("close_bracket",)
            self._prev_char = ch
        elif ch == "{":
            is_object = self._brace_is_object()
            expr_body = False
            for index in range(
                    len(self._pending_expr_bodies) - 1, -1, -1):
                if self._pending_expr_bodies[index][0] == \
                        len(self._brackets):
                    expr_body = \
                        self._pending_expr_bodies[index][1]
                    del self._pending_expr_bodies[index]
                    break
            self._brackets.append(
                ["brace", is_object, 0, expr_body])
            self.kind = "operator"
            self._prev = ("open_brace", is_object)
            self._prev_char = ch
        elif ch == "}":
            is_object = False
            expr_body = False
            if self._brackets \
                    and self._brackets[-1][0] == "brace":
                frame = self._brackets.pop()
                is_object = frame[1]
                expr_body = frame[3]
                self.kind = "operand" if is_object or expr_body \
                    else "operator"
                self._prev = ("close_brace", is_object)
            elif self._brackets \
                    and self._brackets[-1][0] == "interp":
                self._brackets.pop()
                self.kind = "operator"
                self._prev = ("close_interp",)
            else:
                self.kind = "operator"
                self._prev = ("close_brace", False)
            self._prev_char = ch
        elif ch == ".":
            if self._q_pending:
                self._q_pending = False
                self._q_dot_pending = True
            self.kind = "operator"
            self._after_dot = True
            self._prev = ("char", ch)
            self._prev_char = ch
        elif ch == "?":
            if self._q_pending:
                self._bump_ternary(-1)
                self._q_pending = False
            else:
                self._bump_ternary(1)
                self._q_pending = True
            self.kind = "operator"
            self._prev = ("char", ch)
            self._prev_char = ch
        elif ch == ":":
            top = self._brackets[-1] if self._brackets else None
            self._colon_value = (
                top is not None and (
                    top[0] in ("paren", "bracket", "interp")
                    or (top[0] == "brace" and top[1]))
            ) or self._ternary() > 0
            if self._ternary() > 0:
                self._bump_ternary(-1)
            self.kind = "operator"
            self._prev = ("char", ch)
            self._prev_char = ch
        elif ch == ">" and self._prev_char == "=" \
                and self._equals_single:
            self.kind = "operator"
            self._prev = ("arrow",)
            self._prev_char = ch
        else:
            if ch == "=":
                self._equals_single = \
                    self._prev_char not in "=<>!"
            self.kind = "operator"
            self._prev = ("char", ch)
            self._prev_char = ch
        self._after_restricted = False
        self._restricted_asi = False


def strip_comments(source):
    """The source with every comment blanked to spaces.

    String literals, template literals and regex literals keep
    their bytes, so a call shape quoted inside a comment stops
    looking like a call site while the real call sites stand
    unchanged. Newlines survive, so the stripped text lines up
    with the source it came from. A comment opens wherever
    its slashes stand outside a string or a regex, and a
    single slash opens a regex literal where the previous
    significant token, judged by _SlashContext, leaves an
    expression to start.
    """
    out = []
    i = 0
    state = "code"
    slash = _SlashContext()
    brace_depth = 0
    template_marks = []
    regex_class = False
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == "/" and nxt in "/*":
                state = "line" if nxt == "/" else "block"
                slash.feed_separator()
                out.append("  ")
                i += 2
                continue
            if ch == "/" and slash.opens_regex():
                state = "regex"
                regex_class = False
                out.append(ch)
                i += 1
                continue
            resumed = False
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if template_marks and brace_depth == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                    resumed = True
            out.append(ch)
            # A brace closing a template interpolation is fed
            # too, so the shared bracket stack stays balanced.
            slash.feed(ch)
            i += 1
            continue
        if state in ("single", "double"):
            out.append(ch)
            if ch == "\\" and i + 1 < len(source):
                out.append(source[i + 1])
                i += 2
                continue
            if ch == ("'" if state == "single" else '"'):
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "template":
            out.append(ch)
            if ch == "\\" and i + 1 < len(source):
                out.append(source[i + 1])
                i += 2
                continue
            if ch == "`":
                state = "code"
                slash.mark_operand()
            elif ch == "$" and nxt == "{":
                out.append(nxt)
                template_marks.append(brace_depth)
                brace_depth += 1
                state = "code"
                slash.open_interpolation()
                i += 2
                continue
            i += 1
            continue
        if state == "regex":
            out.append(ch)
            if ch == "\\" and i + 1 < len(source):
                out.append(source[i + 1])
                i += 2
                continue
            if ch == "[":
                regex_class = True
            elif ch == "]":
                regex_class = False
            elif ch == "/" and not regex_class:
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "line":
            out.append("\n" if ch == "\n" else " ")
            if ch == "\n":
                state = "code"
                slash.feed_separator(True)
            i += 1
            continue
        if state == "block":
            if ch == "*" and nxt == "/":
                out.append("  ")
                i += 2
                state = "code"
                continue
            out.append("\n" if ch == "\n" else " ")
            if ch == "\n":
                slash.feed_separator(True)
            i += 1
            continue
    return "".join(out)


def _unicode_escape_at(code, start):
    """The character a unicode escape at code[start] spells.

    Handles the plain four digit form and the braced form.
    Returns the decoded character and the index just past
    the escape, or None where code[start] opens no unicode
    escape or names no character.
    """
    if code[start:start + 2] != "\\u":
        return None
    if code[start + 2:start + 3] == "{":
        close = code.find("}", start + 3)
        if close < 0:
            return None
        digits = code[start + 3:close]
        if not digits or any(
                ch not in "0123456789abcdefABCDEF" for ch in digits):
            return None
        value = int(digits, 16)
        end = close + 1
    else:
        digits = code[start + 2:start + 6]
        if len(digits) != 4 or any(
                ch not in "0123456789abcdefABCDEF" for ch in digits):
            return None
        value = int(digits, 16)
        end = start + 6
    if value > 0x10FFFF:
        return None
    return chr(value), end


def _is_identifier_start(ch):
    """Whether ch can open a JavaScript identifier."""
    return ch in "_$" or ch.isidentifier()


def _is_identifier_continue(ch):
    """Whether ch can stand inside a JavaScript identifier."""
    return ch in "_$" or ch in "\u200c\u200d" \
        or ("a" + ch).isidentifier()


def _is_identifier_char(ch):
    """Whether ch can stand in a JavaScript identifier at all."""
    return _is_identifier_start(ch) or _is_identifier_continue(ch)


def _decode_member_string(text):
    """A bracket key's contents with unicode escapes decoded."""
    out = []
    i = 0
    while i < len(text):
        decoded = _unicode_escape_at(text, i) if text[i] == "\\" \
            else None
        if decoded is not None:
            out.append(decoded[0])
            i = decoded[1]
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def decode_identifier_escapes(code):
    """Code with unicode escapes in identifiers decoded.

    The host's parser reads an identifier escape as the
    character it spells, so an escaped member name is the
    plain member, and every scan that reads a member name
    must judge the decoded name or it judges nothing. The
    walk mirrors the comment stripper's states, so escapes
    inside string, template and regex literals keep their
    raw spelling, which the environment literal pin judges
    as written, and only escapes standing in code, in an
    identifier or inside a template interpolation, decode.
    An escape decodes only where the character it spells
    can stand in an identifier at that position, a start
    character where no identifier is under way and a
    continue character where one is, so an out of range,
    empty, non hex, lone surrogate or punctuation or digit
    valued escape at a name's head, and any escape spelling
    a character that cannot stand where it stands, stays
    undecoded and is judged as written, and the decoder
    never fabricates a member chain the source does not
    contain. Decoding is idempotent, so a scan may apply
    it to code a caller already decoded.
    """
    out = []
    i = 0
    state = "code"
    slash = _SlashContext()
    brace_depth = 0
    template_marks = []
    regex_class = False
    while i < len(code):
        ch = code[i]
        nxt = code[i + 1] if i + 1 < len(code) else ""
        if state == "code":
            if ch == "\\":
                decoded = _unicode_escape_at(code, i)
                if decoded is not None:
                    spelled = decoded[0]
                    before = out[-1] if out else ""
                    if before and _is_identifier_char(before):
                        valid = _is_identifier_continue(spelled)
                    else:
                        valid = _is_identifier_start(spelled)
                    if valid:
                        out.append(spelled)
                        slash.feed(spelled)
                        i = decoded[1]
                        continue
            if ch == "/" and nxt in "/*":
                state = "line" if nxt == "/" else "block"
                slash.feed_separator()
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            if ch == "/" and slash.opens_regex():
                state = "regex"
                regex_class = False
                out.append(ch)
                i += 1
                continue
            resumed = False
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if template_marks and brace_depth == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                    resumed = True
            out.append(ch)
            # A brace closing a template interpolation is fed
            # too, so the shared bracket stack stays balanced.
            slash.feed(ch)
            i += 1
            continue
        if state in ("single", "double"):
            out.append(ch)
            if ch == "\\" and i + 1 < len(code):
                out.append(code[i + 1])
                i += 2
                continue
            if ch == ("'" if state == "single" else '"'):
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "template":
            out.append(ch)
            if ch == "\\" and i + 1 < len(code):
                out.append(code[i + 1])
                i += 2
                continue
            if ch == "`":
                state = "code"
                slash.mark_operand()
            elif ch == "$" and nxt == "{":
                out.append(nxt)
                template_marks.append(brace_depth)
                brace_depth += 1
                state = "code"
                slash.open_interpolation()
                i += 2
                continue
            i += 1
            continue
        if state == "regex":
            out.append(ch)
            if ch == "\\" and i + 1 < len(code):
                out.append(code[i + 1])
                i += 2
                continue
            if ch == "[":
                regex_class = True
            elif ch == "]":
                regex_class = False
            elif ch == "/" and not regex_class:
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "line":
            out.append(ch)
            if ch == "\n":
                state = "code"
                slash.feed_separator(True)
            i += 1
            continue
        if state == "block":
            out.append(ch)
            if ch == "*" and nxt == "/":
                out.append(nxt)
                i += 2
                state = "code"
                continue
            if ch == "\n":
                slash.feed_separator(True)
            i += 1
            continue
    return "".join(out)


ENV_NAME = "RECOGNITIO_PACKET_DIR"


def literal_at(code, start):
    """The string literal opening at code[start], or None.

    Returns the literal's raw contents and the index just past
    its closing quote. The contents keep their escape spellings,
    so only the exact plain name reads back. A template literal
    carrying an interpolation is no plain literal and returns
    None, as does any opening that is not a string literal.
    """
    if start >= len(code) or code[start] not in "\"'`":
        return None
    quote = code[start]
    chars = []
    i = start + 1
    while i < len(code):
        ch = code[i]
        if ch == "\\":
            chars.append(code[i:i + 2])
            i += 2
            continue
        if quote == "`" and code.startswith("${", i):
            return None
        if ch == quote:
            return "".join(chars), i + 1
        chars.append(ch)
        i += 1
    return None


def trailing_comma(code, at, parens):
    """Whether the comma after a literal is a trailing comma.

    A comma with only the call's own closing parentheses
    after it adds no argument, so what follows the comma
    decides. The scan skips the parentheses the literal
    was unwrapped from and then the whitespace after them.
    """
    i = at
    while i < len(code) and code[i].isspace():
        i += 1
    if code[i:i + 1] != ",":
        return False
    i += 1
    skipped = 0
    while skipped < parens:
        while i < len(code) and code[i].isspace():
            i += 1
        if code[i:i + 1] == ")":
            i += 1
            skipped += 1
        else:
            return False
    while i < len(code) and code[i].isspace():
        i += 1
    return code[i:i + 1] == ")"


def template_interpolates(code, start):
    """Whether the template literal at code[start] interpolates."""
    i = start + 1
    while i < len(code):
        ch = code[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "`":
            return False
        if code.startswith("${", i):
            return True
        i += 1
    return False


def _bracket_member(code, start):
    """The member a bracket access at code[start] names.

    Returns the member name and the index just past the
    closing bracket. A plain string or template key names
    that member, and any other key, a joined or interpolated
    or dynamic key, names no member the pin can read and
    returns None for the name. An unclosed bracket returns
    None for the end as well.
    """
    depth = 0
    quote = ""
    i = start
    while i < len(code):
        ch = code[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'`":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                inner = code[start + 1:i].strip()
                literal = literal_at(inner, 0)
                if literal is not None and literal[1] == len(inner):
                    return _decode_member_string(literal[0]), i + 1
                return None, i + 1
        i += 1
    return None, None


def _receiver_steps(code, pos):
    """The member steps of the chain headed by the $ at pos.

    Each step carries its spelling, dot, bracket or
    optional, beside the member it names, or None where a
    bracket key names no member the pin can read. The walk
    reads the spelling as written, before any normalisation,
    because the distinction it judges is the one the
    normaliser erases.
    """
    steps = []
    i = pos + 1
    while True:
        j = i
        while j < len(code) and code[j].isspace():
            j += 1
        if code.startswith("?.", j) and not code[j + 2:j + 3].isdigit():
            k = j + 2
            while k < len(code) and code[k].isspace():
                k += 1
            if code[k:k + 1] == "[":
                member, end = _bracket_member(code, k)
                if end is None:
                    break
                steps.append(("optional", member))
                i = end
                continue
            named = re.match(r"[A-Za-z_$][\w$]*", code[k:])
            if not named:
                break
            steps.append(("optional", named.group(0)))
            i = k + named.end()
            continue
        if code[j:j + 1] == ".":
            k = j + 1
            while k < len(code) and code[k].isspace():
                k += 1
            named = re.match(r"[A-Za-z_$][\w$]*", code[k:])
            if not named:
                break
            steps.append(("dot", named.group(0)))
            i = k + named.end()
            continue
        if code[j:j + 1] == "[":
            member, end = _bracket_member(code, j)
            if end is None:
                break
            steps.append(("bracket", member))
            i = end
            continue
        break
    return steps, i


def receiver_spelling_problems(code, noun=None):
    """Problems with a computed or optional receiver spelling.

    The scan reads code with its comments already stripped
    and its member spellings exactly as written. A bracket
    member or an optional chain step on $ itself, on $.env
    or on $.fs, and an optional call step on the method,
    are a computed or optional member access on $, which
    the host refuses at load. The normaliser rewrites those
    spellings to the dot spelling for the argument scans,
    so this scan judges the receiver before that rewrite
    can erase it. A bracket or optional step on any other
    receiver, an argument object among them, is ordinary
    code and stands untouched. The noun argument keeps
    each pin to its own receiver, env for the environment
    pin and fs for the file read pin. Identifier escapes
    in a member name decode before the walk, so an escaped
    noun or method is judged as the member the host reads,
    while the bracket or optional spelling that carries it
    still stands as written for this scan.
    """
    code = decode_identifier_escapes(code)
    problems = []
    literals = literal_spans(code)
    for match in re.finditer(r"(?<![\w$.])\$(?![\w$])", code):
        pos = match.start()
        if any(start <= pos <= end for start, end in literals):
            continue
        steps, end = _receiver_steps(code, pos)
        if not steps:
            continue
        members = [member for style, member in steps]
        if noun == "env" and not any(
                member in ("env", "get", "set") for member in members):
            continue
        if noun == "fs" and not any(
                member in ("fs", "read") for member in members):
            continue
        receiver = None
        if steps[0][0] != "dot":
            receiver = "$"
        elif len(steps) >= 2 and steps[0][1] in ("env", "fs") \
                and steps[1][0] != "dot":
            receiver = "$." + steps[0][1]
        else:
            # An optional call step, $.env.get?.(...), is an
            # optional access on the method the receiver
            # chain heads, and the host refuses it the same.
            tail = end
            while tail < len(code) and code[tail].isspace():
                tail += 1
            if len(steps) >= 2 and steps[0][1] in ("env", "fs") \
                    and code.startswith("?.", tail) \
                    and code[tail + 2:].lstrip()[:1] == "(":
                receiver = "$.%s.%s" % (steps[0][1], steps[1][1])
        if receiver is None:
            continue
        message = (
            "the hooks module reaches the mods API through a "
            "computed or optional member access on %s in %s, "
            "where the host requires the plain dot spelling "
            "at every call site and refuses that access at "
            "load, so the module would not load in a session "
            "and every spawn would pass ungated"
            % (receiver, code[pos:end])
        )
        if message not in problems:
            problems.append(message)
    return problems


def env_call_problems(code):
    """Problems with the module's environment call sites.

    The scan reads code with its comments already stripped, so
    whitespace and comments between the callee, the parenthesis
    and the argument are all tolerated and only the argument
    itself is judged. The host lists the variables a module
    reads from the literal at each call site and refuses to
    load a module whose name is not the literal it lists. The
    pin requires the exact literal RECOGNITIO_PACKET_DIR
    standing alone at every $.env.get and $.env.set call site,
    spelled plainly, a stricter spelling than the host's
    decoded comparison, so the name a reviewer reads is the
    name the host lists. The receiver spelling is judged as
    written, before normalisation, and a computed or
    optional member access on $, $.env or the method is
    refused, as the host refuses it at load. A call shape
    standing inside a string, template or regex literal is
    quoted text and not a call site, so the scan skips a
    match whose head stands inside a literal span, the
    spans literal_spans computes on the normalised code.
    Code inside a template interpolation stands outside
    the spans and is judged as before.
    """
    code = decode_identifier_escapes(code)
    problems = receiver_spelling_problems(code, "env")
    code = normalise_member_spellings(code)
    spans = literal_spans(code)
    for match in _ENV_CALL.finditer(code):
        if any(start <= match.start() <= end
                for start, end in spans):
            continue
        call = re.match(r"\s*\(\s*", code[match.end():])
        if not call:
            problems.append(
                "the hooks module names $.env.%s without calling "
                "it, so no call site names the variable it reads "
                "in a literal the host can list" % match.group(1)
            )
            continue
        start = match.end() + call.end()
        parens = 0
        while code[start:start + 1] == "(":
            parens += 1
            start += 1
            while start < len(code) and code[start].isspace():
                start += 1
        if code[start:start + 1] == "`" \
                and template_interpolates(code, start):
            problems.append(
                "the hooks module names its environment variable "
                "through an interpolated template literal, so the "
                "name at the call site is not the exact literal "
                "RECOGNITIO_PACKET_DIR the host can list"
            )
            continue
        literal = literal_at(code, start)
        if literal is None:
            problems.append(
                "the hooks module reads an environment variable "
                "through a name that is not a string literal, so "
                "the host cannot list the variables it reads and "
                "refuses to load the module"
            )
            continue
        value, end = literal
        following_at = end
        skipped = 0
        while skipped < parens:
            while following_at < len(code) \
                    and code[following_at].isspace():
                following_at += 1
            if code[following_at:following_at + 1] == ")":
                following_at += 1
                skipped += 1
            else:
                break
        following = code[following_at:].lstrip()[:1]
        if following == "+":
            problems.append(
                "the hooks module joins literals to build its "
                "environment variable name, so the name at the "
                "call site is not the exact literal "
                "RECOGNITIO_PACKET_DIR and the host refuses to "
                "load the module"
            )
        elif value != ENV_NAME:
            problems.append(
                "the hooks module reads an environment variable "
                "through the literal %r, not the exact name "
                "RECOGNITIO_PACKET_DIR the contract pins, so the "
                "module would load reading a variable nobody "
                "sets and stand inert while spawns pass ungated"
                % value
            )
        elif match.group(1) == "get" and following == "," \
                and not trailing_comma(
                    code, following_at, parens - skipped):
            problems.append(
                "the hooks module passes $.env.get a second "
                "argument beside its variable name, so the call "
                "site does not name the variable in the exact "
                "literal RECOGNITIO_PACKET_DIR standing alone"
            )
        elif following not in (",", ")", ""):
            problems.append(
                "the hooks module builds on its environment "
                "variable name at the call site, so the name is "
                "not the exact literal RECOGNITIO_PACKET_DIR "
                "standing alone and the host refuses to load "
                "the module"
            )
    return problems


def literal_spans(code):
    """The spans of the string, template and regex literals.

    A $ inside a literal is text, not the mods object, so
    the value scan reads only the code outside these spans.
    Code inside a template interpolation stands outside
    the spans and is judged, since it runs as code. The
    walk mirrors the comment stripper's states.
    """
    spans = []
    i = 0
    state = "code"
    slash = _SlashContext()
    start = 0
    brace_depth = 0
    template_marks = []
    regex_class = False
    while i < len(code):
        ch = code[i]
        nxt = code[i + 1] if i + 1 < len(code) else ""
        if state == "code":
            if ch == "/" and nxt in "/*":
                state = "line" if nxt == "/" else "block"
                slash.feed_separator()
                i += 2
                continue
            if ch == "/" and slash.opens_regex():
                state = "regex"
                regex_class = False
                start = i
                i += 1
                continue
            resumed = False
            if ch in "'\"`":
                state = {"'": "single", '"': "double"}.get(ch, "template")
                start = i
            elif ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if template_marks and brace_depth == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                    start = i
                    resumed = True
            # A brace closing a template interpolation is fed
            # too, so the shared bracket stack stays balanced.
            slash.feed(ch)
            i += 1
            continue
        if state in ("single", "double"):
            if ch == "\\":
                i += 2
                continue
            if ch == ("'" if state == "single" else '"'):
                spans.append((start, i))
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "template":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                spans.append((start, i))
                state = "code"
                slash.mark_operand()
            elif ch == "$" and nxt == "{":
                # The text segment ends at the interpolation
                # marker itself, so the marker's own $ stays
                # inside the span while the interpolated code
                # stands outside every span and is judged.
                spans.append((start, i))
                template_marks.append(brace_depth)
                brace_depth += 1
                state = "code"
                slash.open_interpolation()
                i += 2
                continue
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                regex_class = True
            elif ch == "]":
                regex_class = False
            elif ch == "/" and not regex_class:
                spans.append((start, i))
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "line":
            if ch == "\n":
                state = "code"
                slash.feed_separator(True)
            i += 1
            continue
        if state == "block":
            if ch == "*" and nxt == "/":
                i += 2
                state = "code"
                continue
            if ch == "\n":
                slash.feed_separator(True)
            i += 1
            continue
    return spans


_ENV_CALL = re.compile(r"\$\s*\.\s*env\s*\.\s*(get|set)(?![\w$])")
_FS_CALL = re.compile(r"\$\s*\.\s*fs\s*\.\s*read(?![\w$])")
_ASSIGNMENT = re.compile(
    r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*(?:\?\?|\|\||&&)?=(?![=>])\s*")


def normalise_member_spellings(code):
    """Member spellings rewritten to the dot spelling.

    A bracket member whose key is a plain identifier
    string, and an optional chain dot, name the same
    member as the dot spelling, so the scans read every
    spelling in the one spelling they judge. The rewrite
    runs on the comment stripped source the scans already
    read. An optional chain dot ahead of a digit is a
    conditional expression instead and stands untouched.
    """
    code = re.sub(
        r"\[\s*\"([A-Za-z_$][\w$]*)\"\s*\]", r".\1", code)
    code = re.sub(
        r"\[\s*'([A-Za-z_$][\w$]*)'\s*\]", r".\1", code)
    code = re.sub(r"\?\.(?!\d)", ".", code)
    return code


def dollar_value_problems(code, ranges, written=None):
    """Problems with a use of the mods object as a value.

    The host spells the object $. at every call site and
    refuses to load a module that binds it to another name
    in a declaration or an assignment. A standalone $ in
    the stripped source is therefore judged by where it
    stands. It may head a member chain, it may stand as a
    parameter named $ itself, and it may stand as an
    argument where the module's own function names that
    parameter $. Anywhere else it is a value bound,
    passed, spread, returned or read under another name.
    The host refuses the returned form, a $ spread into a
    call and a $ passed inside an object at load and
    leaves only the pure read forms, an interpolation, a
    comparison, a typeof read, a negation, a template tag
    and an array literal placing, alone, and the gate
    refuses both halves, since a call behind any of them
    stands where no pin can read it. The optional call
    spelling is judged on the source as written, in the
    written argument, because the normalised code this
    scan otherwise reads has already rewritten an
    optional step on $ to a dot, which made a called $
    read as the head of a member chain and pass.
    """
    problems = []

    def flag(message):
        if message not in problems:
            problems.append(message)

    if written is not None:
        written = decode_identifier_escapes(written)
        written_literals = literal_spans(written)
        for match in re.finditer(r"(?<![\w$.])\$(?![\w$])", written):
            pos = match.start()
            if any(start <= pos <= end
                    for start, end in written_literals):
                continue
            if re.match(r"\s*\?\s*\.\s*\(", written[match.end():]):
                flag(
                    "the hooks module calls $ itself through "
                    "an optional call spelling, where the host "
                    "requires the $. spelling at every call "
                    "site and refuses a called $ at load, so "
                    "the module would not load in a session "
                    "and every spawn would pass ungated"
                )
                break

    bound_message = (
        "the hooks module binds $ itself to another name, "
        "where the host requires the $. spelling at every "
        "call site, so a call behind the alias would stand "
        "where no pin can read it"
    )
    if re.search(r"\$\s*\[", code):
        flag(
            "the hooks module reaches $ through a bracket "
            "spelling, where the host requires the $. spelling "
            "at every call site, so the call stands where no "
            "pin can read it"
        )
    call_args = []
    for entry in ranges:
        if entry[2] is None:
            continue
        for match in re.finditer(
                r"(?<![\w$.])" + re.escape(entry[2]) + r"(?![\w$])",
                code):
            if code[:match.start()].rstrip().endswith("function"):
                continue
            call = re.match(r"\s*\(", code[match.end():])
            if not call:
                continue
            open_paren = match.end() + call.end() - 1
            spans = argument_spans(code, open_paren)
            if spans is None:
                continue
            for index, (start, end) in enumerate(spans):
                call_args.append((start, end, entry, index))
    literals = literal_spans(code)
    for match in re.finditer(r"(?<![\w$])\$(?![\w$])", code):
        pos = match.start()
        if any(start <= pos <= end for start, end in literals):
            continue
        following = code[pos + 1:].lstrip()[:1]
        if following == ".":
            if re.search(
                    r"(?:^|[;{}]\s*)(?:const\s+|let\s+|var\s+)?"
                    r"(?:\{[^{}]*\}|\[[^\[\]]*\]"
                    r"|[A-Za-z_$][\w$]*)\s*=\s*$",
                    code[:pos]):
                # A member chain bound onward, into a
                # declaration, a destructuring or an
                # assignment, hands the noun to calls no
                # pin can read, where a chain called in
                # place stands at a judged call site.
                flag(
                    "the hooks module binds a noun of $ to "
                    "another name, where the host requires "
                    "the $. spelling at every call site and "
                    "refuses a noun of $ bound, passed or "
                    "read, so a call behind the binding "
                    "would stand where no pin can read it"
                )
            continue
        if re.search(r"(?<![\w$.])catch\s*\(\s*$", code[:pos]):
            # A catch clause binding named $ binds the error
            # under that name, a parameter in everything but
            # spelling, and the name occurrence itself is no
            # value use of the mods object.
            continue
        holder = enclosing_function(code, pos, ranges)
        if holder is not None and holder[4] <= pos <= holder[5]:
            named = False
            for segment in holder[3]:
                if segment[0] <= pos <= segment[1] \
                        and segment[3] == [("$", ())]:
                    text = segment[2]
                    offset = segment[0] + (
                        len(text) - len(text.lstrip()))
                    if text.lstrip().startswith("..."):
                        offset += 3
                    named = pos == offset
            if not named:
                flag(bound_message)
            continue
        passed = False
        for start, end, entry, index in call_args:
            if start <= pos <= end and index < len(entry[3]):
                if entry[3][index][3] == [("$", ())] \
                        and code[start:end].strip() == "$":
                    passed = True
        if not passed:
            flag(bound_message)
    return problems


def alien_receiver_problems(code):
    """Problems with mods API calls through another receiver.

    The environment and file calls belong to the mods
    object, and every pin reads them at a $. call site. A
    call through any other receiver, an alias, a renamed
    parameter, a destructured member or a container, stands
    where those pins cannot judge it, so the gate refuses
    the receiver itself. A call shape standing inside a
    string, template or regex literal is quoted text and
    not a call site, so the scan skips a match whose head
    stands inside a literal span, the spans literal_spans
    computes on the normalised code. Code inside a template
    interpolation stands outside the spans and is judged.
    """
    code = normalise_member_spellings(decode_identifier_escapes(code))
    problems = []
    spans = literal_spans(code)
    message = (
        "the hooks module reaches the mods API through a "
        "receiver other than $, so the call does not stand "
        "at a $. call site the pins can judge"
    )
    for match in re.finditer(
            r"\.\s*(?:env|fs)\s*\.\s*(?:get|set|read)(?![\w$])",
            code):
        if any(start <= match.start() <= end
                for start, end in spans):
            continue
        before = code[:match.start()].rstrip()
        if before.endswith("$") and (
                len(before) == 1 or before[-2] not in
                "abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789_$."):
            continue
        if message not in problems:
            problems.append(message)
    for match in re.finditer(
            r"(?<![\w$.])(?:env|fs)\s*\.\s*(?:get|set|read)(?![\w$])",
            code):
        if any(start <= match.start() <= end
                for start, end in spans):
            continue
        if message not in problems:
            problems.append(message)
    return problems


def call_arguments(code, open_paren):
    """The top level arguments of a call, or None.

    Splits the argument list whose opening parenthesis
    stands at code[open_paren] on its top level commas.
    String and template literals count as opaque, so a
    comma inside one never splits. A trailing comma adds
    no argument. Returns None when the call never closes.
    """
    spans = argument_spans(code, open_paren)
    if spans is None:
        return None
    return [code[start:end] for start, end in spans]


def argument_spans(code, open_paren):
    """The spans of a call's top level arguments, or None.

    The companion to call_arguments, carrying the start
    and end index of each argument beside its text.
    """
    args = []
    depth = 0
    state = "code"
    slash = _SlashContext()
    template_marks = []
    start = open_paren + 1
    i = open_paren
    while i < len(code):
        ch = code[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
                if depth == 0:
                    if not code[open_paren + 1:i].strip():
                        return []
                    args.append((start, i))
                    if len(args) > 1 \
                            and not code[args[-1][0]:args[-1][1]].strip():
                        args.pop()
                    return args
            elif ch == "," and depth == 1:
                args.append((start, i))
                start = i + 1
            if ch == "}" and template_marks and \
                    depth == template_marks[-1]:
                template_marks.pop()
                state = "template"
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                code[i + 1:i + 2] == "{":
            template_marks.append(depth)
            depth += 1
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    return None


def split_top_level(text):
    """The comma separated parts of text at its top level.

    String and template literals count as opaque, so a comma
    inside one never splits.
    """
    parts = []
    depth = 0
    state = "code"
    slash = _SlashContext()
    template_marks = []
    start = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(text[start:i])
                start = i + 1
            if ch == "}" and template_marks and \
                    depth == template_marks[-1]:
                template_marks.pop()
                state = "template"
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                text[i + 1:i + 2] == "{":
            template_marks.append(depth)
            depth += 1
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    parts.append(text[start:])
    return parts


def matching_close(code, open_index):
    """The index of the bracket closing code[open_index]."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    state = "code"
    slash = _SlashContext()
    template_marks = []
    i = open_index
    while i < len(code):
        ch = code[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in pairs:
                stack.append(pairs[ch])
            elif ch in ")]}":
                if not stack or stack[-1] != ch:
                    return None
                stack.pop()
                if ch == "}" and template_marks and \
                        len(stack) == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                if not stack:
                    return i
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                code[i + 1:i + 2] == "{":
            template_marks.append(len(stack))
            stack.append("}")
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    return None


def expression_at(code, start):
    """The expression opening at a position, as text and end.

    Reads to the first comma or semicolon at the
    expression's own level, or to the bracket that closes
    the context it stands in. String and template literals
    count as opaque.
    """
    depth = 0
    state = "code"
    slash = _SlashContext()
    template_marks = []
    i = start
    while i < len(code):
        ch = code[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif ch in ";," and depth == 0:
                break
            if ch == "}" and template_marks and \
                    depth == template_marks[-1]:
                template_marks.pop()
                state = "template"
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                code[i + 1:i + 2] == "{":
            template_marks.append(depth)
            depth += 1
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    return code[start:i], i


def argument_stands_object(arg):
    """Whether an argument expression can stand an object.

    True when an object literal can be the value the argument
    passes, standing at the head of the expression, in one of
    its top level branches, in the array a spread opens, or
    at the index an array literal is read through. An object
    literal read through a member, as in the .path of an
    options object, evaluates to that member and is not the
    argument itself. String, template and regex literals
    count as opaque, so a brace inside one never moves the
    depth the branches are judged at.
    """
    s = arg.strip()
    spread = s.startswith("...")
    if spread:
        s = s[3:].lstrip()
    if re.match(r"Object(?:\.assign|\.create)?\s*\(", s):
        # The Object calls return an object whatever they
        # are handed, so the argument stands as one.
        return True
    while s.startswith("("):
        close = matching_close(s, 0)
        if close is None:
            break
        rest = s[close + 1:].strip()
        if not rest:
            s = s[1:close].strip()
            continue
        if rest.startswith("[") or rest.startswith("."):
            s = s[1:close].strip() + rest
            continue
        break
    if s.startswith("["):
        close = matching_close(s, 0)
        if close is None:
            return False
        elements = split_top_level(s[1:close])
        rest = s[close + 1:].strip()
        if spread:
            return any(
                argument_stands_object(element)
                for element in elements)
        if rest.startswith("["):
            index_close = matching_close(rest, 0)
            if index_close is None:
                return False
            index = rest[1:index_close].strip()
            if index.isdigit() and int(index) < len(elements):
                return argument_stands_object(elements[int(index)])
            return any(
                argument_stands_object(element)
                for element in elements)
        return False
    depth = 0
    state = "code"
    prev = ""
    slash = _SlashContext()
    template_marks = []
    i = 0
    while i < len(s):
        ch = s[i]
        if state == "code":
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            elif ch == "{" and depth == 0 and prev in (
                    "", "?", ":", "|", "&", "=", ","):
                close = matching_close(s, i)
                if close is not None \
                        and s[close + 1:].lstrip()[:1] not in (".", "["):
                    return True
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            if not ch.isspace():
                prev = ch
            if ch == "}" and template_marks and \
                    depth == template_marks[-1]:
                template_marks.pop()
                state = "template"
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                prev = "/"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                s[i + 1:i + 2] == "{":
            template_marks.append(depth)
            depth += 1
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    return False


def rhs_stands_object(code, start):
    """Whether the expression at a position can stand an object.

    An Object call, an Object.assign call and an
    Object.create call each return an object whatever
    they are handed, so those heads stand on their own.
    Every other head is judged as the argument it stands
    for.
    """
    text, _ = expression_at(code, start)
    if re.match(r"\s*Object(?:\.assign|\.create)?\s*\(", text):
        return True
    return argument_stands_object(text)


def pattern_bound_names(pattern):
    """The names a destructuring pattern binds, at any depth."""
    s = pattern.strip()
    names = []
    if s[:1] == "[" or s[:1] == "{":
        close = matching_close(s, 0)
        inner = s[1:close] if close is not None else s[1:]
        for part in split_top_level(inner):
            if s[0] == "{":
                key, mark, rest = part.partition(":")
                names.extend(pattern_bound_names(rest if mark else key))
            else:
                names.extend(pattern_bound_names(part))
        return names
    head = s.split("=")[0].strip()
    if head.startswith("..."):
        head = head[3:].strip()
    if re.fullmatch(r"[A-Za-z_$][\w$]*", head):
        names.append(head)
    return names


def pattern_key_map(pattern, prefix=()):
    """The names a pattern binds, each with its key path.

    The key path names the properties and indexes a value
    walks to reach the name, so a call site feeding the
    pattern can be judged at the name itself. An elision
    in an array pattern binds nothing, and its empty part
    is read as no pattern at all rather than as a bracket
    the empty string would spell.
    """
    s = pattern.strip()
    out = []
    if s[:1] == "[" or s[:1] == "{":
        close = matching_close(s, 0)
        inner = s[1:close] if close is not None else s[1:]
        for index, part in enumerate(split_top_level(inner)):
            if s[0] == "{":
                key, mark, rest = part.partition(":")
                key = key.strip().strip("\"'")
                out.extend(pattern_key_map(
                    rest if mark else key, prefix + (key,)))
            else:
                out.extend(pattern_key_map(part, prefix + (index,)))
        return out
    for name in pattern_bound_names(s):
        out.append((name, prefix))
    return out


def pattern_bindings(pattern, value, pos, out):
    """Names a pattern binds to an object in a value.

    Walks the pattern and the value together, so a name
    binds only where its own place in the value stands an
    object, at any depth of either side.
    """
    s = pattern.strip()
    v = value.strip()
    while v.startswith("("):
        close = matching_close(v, 0)
        if close is None or v[close + 1:].strip():
            break
        v = v[1:close].strip()
    if s[:1] in "[{" and v[:1] == s[:1]:
        pclose = matching_close(s, 0)
        vclose = matching_close(v, 0)
        if pclose is None or vclose is None:
            return
        if s[0] == "[":
            for ppart, vpart in zip(
                    split_top_level(s[1:pclose]),
                    split_top_level(v[1:vclose])):
                pattern_bindings(ppart, vpart, pos, out)
        else:
            values = {}
            for prop in split_top_level(v[1:vclose]):
                key, mark, val = prop.partition(":")
                if mark:
                    values[key.strip().strip("\"'")] = val
                else:
                    ident = re.match(r"\s*([A-Za-z_$][\w$]*)", prop)
                    if ident:
                        values[ident.group(1)] = prop
            for part in split_top_level(s[1:pclose]):
                if part.strip().startswith("..."):
                    # A rest element binds the properties
                    # the named keys leave behind as a new
                    # object of its own, so the name stands
                    # bound to an object wherever the value
                    # it rests from is an object literal.
                    for name in pattern_bound_names(part):
                        out.append((name, pos))
                    continue
                key, mark, rest = part.partition(":")
                key = key.strip().strip("\"'")
                if key in values:
                    pattern_bindings(
                        rest if mark else key, values[key], pos, out)
        return
    if argument_stands_object(v):
        for name in pattern_bound_names(s):
            out.append((name, pos))


def parse_params(code, open_paren):
    """A parameter list as segments.

    Each segment carries its start and end in the source,
    its text, the names it binds with their key paths, and
    its default text or None. A plain segment binds its own
    name with an empty key path.
    """
    close = matching_close(code, open_paren)
    if close is None:
        return [], None
    text = code[open_paren + 1:close]
    segments = []
    depth = 0
    state = "code"
    slash = _SlashContext()
    template_marks = []
    start = 0
    spans = []
    i = 0
    while i < len(text):
        ch = text[i]
        if state == "code":
            if ch == "/" and slash.opens_regex():
                state = "regex"
                i += 1
                continue
            if ch == "'":
                state = "single"
            elif ch == '"':
                state = "double"
            elif ch == "`":
                state = "template"
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                spans.append((start, i))
                start = i + 1
            if ch == "}" and template_marks and \
                    depth == template_marks[-1]:
                template_marks.pop()
                state = "template"
            slash.feed(ch)
            i += 1
            continue
        if state == "regex":
            if ch == "\\":
                i += 2
                continue
            if ch == "[":
                state = "regexclass"
            elif ch == "/":
                state = "code"
                slash.mark_operand()
            i += 1
            continue
        if state == "regexclass":
            if ch == "\\":
                i += 2
                continue
            if ch == "]":
                state = "regex"
            i += 1
            continue
        if state == "template" and ch == "$" and \
                text[i + 1:i + 2] == "{":
            template_marks.append(depth)
            depth += 1
            state = "code"
            slash.open_interpolation()
            i += 2
            continue
        if ch == "\\":
            i += 2
            continue
        if (state == "single" and ch == "'") or \
                (state == "double" and ch == '"') or \
                (state == "template" and ch == "`"):
            state = "code"
            slash.mark_operand()
        i += 1
    spans.append((start, len(text)))
    for seg_start, seg_end in spans:
        seg_text = text[seg_start:seg_end]
        if not seg_text.strip():
            continue
        default = None
        bind_text = seg_text
        depth = 0
        state = "code"
        slash = _SlashContext()
        template_marks = []
        j = 0
        while j < len(seg_text):
            ch = seg_text[j]
            if state == "code":
                if ch == "/" and slash.opens_regex():
                    state = "regex"
                    j += 1
                    continue
                if ch == "'":
                    state = "single"
                elif ch == '"':
                    state = "double"
                elif ch == "`":
                    state = "template"
                elif ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                elif ch == "=" and depth == 0 \
                        and seg_text[j + 1:j + 2] not in ("=", ">"):
                    bind_text = seg_text[:j]
                    default = seg_text[j + 1:].strip()
                    break
                if ch == "}" and template_marks and \
                        depth == template_marks[-1]:
                    template_marks.pop()
                    state = "template"
                slash.feed(ch)
                j += 1
                continue
            if state == "regex":
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    state = "regexclass"
                elif ch == "/":
                    state = "code"
                    slash.mark_operand()
                j += 1
                continue
            if state == "regexclass":
                if ch == "\\":
                    j += 2
                    continue
                if ch == "]":
                    state = "regex"
                j += 1
                continue
            if state == "template" and ch == "$" and \
                    seg_text[j + 1:j + 2] == "{":
                template_marks.append(depth)
                depth += 1
                state = "code"
                slash.open_interpolation()
                j += 2
                continue
            if ch == "\\":
                j += 2
                continue
            if (state == "single" and ch == "'") or \
                    (state == "double" and ch == '"') or \
                    (state == "template" and ch == "`"):
                state = "code"
                slash.mark_operand()
            j += 1
        bind = bind_text.strip()
        if bind[:1] in "[{":
            bindings = pattern_key_map(bind)
        else:
            bindings = [
                (name, ()) for name in pattern_bound_names(bind)]
        segments.append((
            open_paren + 1 + seg_start, open_paren + 1 + seg_end,
            seg_text, bindings, default))
    return segments, close


_FUNCTION_DECL = re.compile(
    r"(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)?\s*\(")
_METHOD_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "return", "function",
    "else", "do", "typeof", "new", "delete", "void", "in", "of",
}


def function_ranges(code):
    """The functions in the module, as ranges.

    Each entry carries the function's start, the index of
    its closing brace or the end of its expression body,
    its name or None for an unnamed function, its parameter
    segments from parse_params, and the span of its
    parameter list text. Plain declarations, function
    expressions, generators, method shorthand and arrow
    functions all count, since a parameter binds the mods
    object in any of them. A function expression assigned
    to a name stands under both its declared name and the
    assigned one, since its call sites use the second.
    """
    found = {}

    def add(start, name, open_paren):
        segments, close_paren = parse_params(code, open_paren)
        if close_paren is None:
            return
        i = close_paren + 1
        while i < len(code) and code[i].isspace():
            i += 1
        if code[i:i + 2] == "=>":
            i += 2
            while i < len(code) and code[i].isspace():
                i += 1
            if i < len(code) and code[i] == "{":
                end = matching_close(code, i)
            else:
                _, end = expression_at(code, i)
            if end is None:
                return
        elif i < len(code) and code[i] == "{":
            end = matching_close(code, i)
            if end is None:
                return
        else:
            return
        found[(start, name)] = (
            start, end, name, segments, open_paren + 1, close_paren)

    for match in _FUNCTION_DECL.finditer(code):
        add(match.start(), match.group(1), match.end() - 1)
        # A function expression assigned to a name is called
        # through that name, so the range also stands under
        # the assigned name beside its declared one.
        before = code[:match.start()].rstrip()
        named = re.search(
            r"([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?$", before)
        if named and named.group(1) != match.group(1):
            add(match.start(), named.group(1), match.end() - 1)
    for match in re.finditer(r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(", code):
        name = match.group(1)
        if name in _METHOD_KEYWORDS:
            continue
        before = code[:match.start()].rstrip()
        if not before or before[-1] not in "{,;}":
            continue
        if before.endswith("function"):
            continue
        add(match.start(), name, match.end() - 1)
    for match in re.finditer(r"\(", code):
        close = matching_close(code, match.end() - 1)
        if close is None:
            continue
        i = close + 1
        while i < len(code) and code[i].isspace():
            i += 1
        if code[i:i + 2] != "=>":
            continue
        before = code[:match.start()].rstrip()
        named = re.search(
            r"([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?$", before)
        add(match.start(), named.group(1) if named else None,
            match.end() - 1)
    for match in re.finditer(
            r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*=>", code):
        # A parenthesis free arrow binds its one parameter
        # with no list to parse, so its range is built here
        # with a single synthetic segment for that name.
        param = match.group(1)
        if param in _METHOD_KEYWORDS:
            continue
        i = match.end()
        while i < len(code) and code[i].isspace():
            i += 1
        if i < len(code) and code[i] == "{":
            end = matching_close(code, i)
        else:
            _, end = expression_at(code, i)
        if end is None:
            continue
        before = code[:match.start()].rstrip()
        named = re.search(
            r"([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?$", before)
        segments = [(
            match.start(1), match.end(1), param,
            [(param, ())], None)]
        found[(match.start(), named.group(1) if named else None)] = (
            match.start(), end,
            named.group(1) if named else None,
            segments, match.start(1), match.end(1))
    return [entry for key, entry in sorted(
        found.items(), key=lambda item: item[0][0])]


def enclosing_function(code, pos, ranges):
    """The innermost function range holding pos.

    A range runs from the function's own start, ahead of
    its parameter list, through the end of its body, so a
    position inside the parameter list itself counts as
    held, which the binding scans rely on when they judge
    a default value.
    """
    best = None
    for entry in ranges:
        if entry[0] <= pos <= entry[1] \
                and (best is None or entry[0] > best[0]):
            best = entry
    return best


def assignment_rhs(code, name, pos):
    """The right hand side of a name's latest assignment.

    Reads assignments before the position, in any scope,
    and returns the latest one's expression text, or None
    when the name is never assigned there.
    """
    latest = None
    for match in _ASSIGNMENT.finditer(code, 0, pos):
        if match.group(1) == name:
            latest = match
    if latest is None:
        return None
    text, _ = expression_at(code, latest.end())
    return text


def indirect_object_bindings(code):
    """Names bound to an object without a plain assignment.

    Covers the destructuring and loop spellings an
    assignment scan cannot see, with or without a
    declaration keyword, judged by pattern_bindings at
    the name's own place in the value, and a for of loop
    over an array literal or a name bound to one holding
    an object. Each entry carries the name and the
    binding's position.
    """
    bindings = []
    patterns = []
    for match in re.finditer(r"(?:const|let|var)\s*([\[{])", code):
        patterns.append((match.start(), match.end() - 1, True))
    for match in re.finditer(r"(?:^|[;()\n{}])\s*([\[{])", code):
        patterns.append((match.start(), match.end() - 1, False))
    for _, open_index, _ in patterns:
        close = matching_close(code, open_index)
        if close is None:
            continue
        rest = re.match(r"\s*=\s*", code[close + 1:])
        if not rest:
            continue
        value, _ = expression_at(code, close + 1 + rest.end())
        pattern_bindings(
            code[open_index:close + 1], value, open_index, bindings)
        named = value.strip()
        while named.startswith("("):
            named_close = matching_close(named, 0)
            if named_close is None or \
                    named[named_close + 1:].strip():
                break
            named = named[1:named_close].strip()
        ident = re.fullmatch(r"([A-Za-z_$][\w$]*)", named)
        if ident:
            # A pattern resting from a bound name binds as
            # the pattern resting from that name's own
            # binding does, so the walk traces the binding
            # the way it traces a literal standing there.
            bound = assignment_rhs(
                code, ident.group(1), open_index)
            if bound is not None:
                pattern_bindings(
                    code[open_index:close + 1], bound,
                    open_index, bindings)
    for match in re.finditer(
            r"for\s*\(\s*(?:const|let|var)\s+"
            r"([A-Za-z_$][\w$]*)\s+of\s+", code):
        start = match.end()
        text = None
        if code[start:start + 1] == "[":
            close = matching_close(code, start)
            if close is not None:
                text = code[start:close + 1]
        else:
            ident = re.match(r"([A-Za-z_$][\w$]*)", code[start:])
            if ident:
                text = assignment_rhs(code, ident.group(1), match.start())
        if text:
            stripped = text.strip()
            while stripped.startswith("("):
                close = matching_close(stripped, 0)
                if close is None or stripped[close + 1:].strip():
                    break
                stripped = stripped[1:close].strip()
            if stripped.startswith("["):
                close = matching_close(stripped, 0)
                if close is not None and any(
                        argument_stands_object(element)
                        for element in split_top_level(
                            stripped[1:close])):
                    bindings.append((match.group(1), match.start()))
    for match in re.finditer(
            r"for\s*\(\s*(?:const|let|var)\s*([\[{])", code):
        # A destructured loop variable binds from each
        # element in turn, so the pattern is judged against
        # every element the iterated value can produce.
        open_index = match.end() - 1
        close = matching_close(code, open_index)
        if close is None:
            continue
        rest = re.match(r"\s+of\s+", code[close + 1:])
        if not rest:
            continue
        value, _ = expression_at(code, close + 1 + rest.end())
        value = value.strip()
        while value.startswith("("):
            vclose = matching_close(value, 0)
            if vclose is None or value[vclose + 1:].strip():
                break
            value = value[1:vclose].strip()
        elements = [value]
        if value.startswith("["):
            vclose = matching_close(value, 0)
            if vclose is not None:
                elements = split_top_level(value[1:vclose])
        else:
            ident = re.fullmatch(r"([A-Za-z_$][\w$]*)", value)
            if ident:
                bound = assignment_rhs(
                    code, ident.group(1), match.start())
                if bound and bound.strip().startswith("["):
                    btext = bound.strip()
                    bclose = matching_close(btext, 0)
                    if bclose is not None:
                        elements = split_top_level(
                            btext[1:bclose])
        for element in elements:
            pattern_bindings(
                code[open_index:close + 1], element,
                match.start(), bindings)
    return bindings


def declares_name(code, name, here, pos):
    """Whether a function declares a name before a position.

    Plain and destructured declarations both count, since
    either binds the name inside the function.
    """
    body = code[here[0]:pos]
    if re.search(
            r"(?:const|let|var)\s+" + re.escape(name) + r"(?![\w$])",
            body):
        return True
    for match in re.finditer(r"(?:const|let|var)\s*([\[{])", body):
        open_index = match.end() - 1
        close = matching_close(body, open_index)
        if close is None:
            continue
        if name in pattern_bound_names(body[open_index:close + 1]):
            return True
    return False


def binding_state_at(code, name, pos, extras, ranges, seen=frozenset()):
    """Whether a name holds an object at a position.

    The latest binding of the name in the same scope
    decides, so a name reassigned to a string after its
    object binding no longer counts. A binding inside the
    function holding the position counts in its written
    order. A module top level binding counts wherever it
    stands, because the module loads whole before any
    spawn fires a hook, and it stops counting where the
    holding function declares the name itself. A binding
    through another name takes that name's state at the
    binding. Destructuring and loop bindings from
    indirect_object_bindings count as object bindings.
    """
    if name in seen:
        return False
    seen = seen | {name}
    here = enclosing_function(code, pos, ranges)
    scoped = []
    top = []

    def add(place, is_object):
        scope = enclosing_function(code, place, ranges)
        if scope is here:
            if place < pos:
                scoped.append((place, is_object))
        elif scope is None and here is not None:
            top.append((place, is_object))

    for bound, place in extras:
        if bound == name:
            add(place, True)
    for match in _ASSIGNMENT.finditer(code):
        if match.group(1) != name:
            continue
        if rhs_stands_object(code, match.end()):
            add(match.start(), True)
            continue
        text, _ = expression_at(code, match.end())
        ident = re.fullmatch(r"\s*([A-Za-z_$][\w$]*)\s*", text)
        if ident and ident.group(1) != name:
            add(match.start(), binding_state_at(
                code, ident.group(1), match.start(), extras,
                ranges, seen))
        elif call_to_local_function(code, text, ranges):
            add(match.start(), value_text_stands_object(
                code, text, match.start(), extras, ranges, seen))
        else:
            add(match.start(), False)
    if scoped:
        scoped.sort()
        return scoped[-1][1]
    if top and not declares_name(code, name, here, pos):
        top.sort()
        return top[-1][1]
    return False


def call_to_local_function(code, text, ranges):
    """The callee name when a text is a bare local call.

    The call must span the whole text, so a member call or
    a call inside a larger expression does not count. A
    callee the module itself defines, under any name the
    function stands under, counts.
    """
    match = re.match(r"\s*([A-Za-z_$][\w$]*)\s*\(", text)
    if not match:
        return None
    open_paren = text.index("(", match.start())
    close = matching_close(text, open_paren)
    if close is None or text[close + 1:].strip():
        return None
    name = match.group(1)
    if any(entry[2] == name for entry in ranges):
        return name
    return None


def function_return_texts(code, name, ranges):
    """The return expression texts of a local function.

    A return counts when the named function is its
    innermost enclosing function, so a nested function's
    returns stay its own.
    """
    texts = []
    for entry in ranges:
        if entry[2] != name:
            continue
        for match in re.finditer(
                r"(?<![\w$.])return(?![\w$])",
                code[entry[0]:entry[1] + 1]):
            at = entry[0] + match.start()
            if enclosing_function(code, at, ranges) is not entry:
                continue
            text, _ = expression_at(code, at + len("return"))
            if text.strip():
                texts.append(text)
    return texts


def value_text_stands_object(code, text, pos, extras, ranges,
                             seen=frozenset()):
    """Whether a value expression can stand an object.

    The judgement follows the provenance the module itself
    writes. A literal stands as the argument scan reads
    it, a member read stands as the member walk reads it,
    a bare name takes its binding state, and a call to a
    module local function stands when one of its returns
    stands, whether the call stands alone or heads a
    member chain. A value with no provenance in the
    module's own literals, a parse or a call the module
    does not define, does not stand.
    """
    if argument_stands_object(text):
        return True
    if call_head_member_stands(code, text, pos, extras, ranges, seen):
        return True
    member = split_member(text)
    if member:
        head, keys = member
        return member_value_stands_object(
            code, head, keys, pos, extras, ranges)
    ident = re.fullmatch(r"\s*([A-Za-z_$][\w$]*)\s*", text)
    if ident:
        return binding_state_at(
            code, ident.group(1), pos, extras, ranges, seen)
    callee = call_to_local_function(code, text, ranges)
    if callee and callee not in seen:
        return any(
            value_text_stands_object(
                code, returned, pos, extras, ranges,
                seen | {callee})
            for returned in function_return_texts(
                code, callee, ranges))
    return False


def call_head_member_stands(code, arg, pos, extras, ranges,
                            seen=frozenset()):
    """Whether a member read on a local call's result can
    stand an object.

    The result takes the callee's return expressions in
    turn, and the member chain is walked on each one.
    """
    match = re.match(r"\s*([A-Za-z_$][\w$]*)\s*\(", arg)
    if not match:
        return False
    open_paren = arg.index("(", match.start())
    close = matching_close(arg, open_paren)
    if close is None:
        return False
    rest = arg[close + 1:].strip()
    if not rest.startswith((".", "[")):
        return False
    callee = match.group(1)
    if callee in seen or not any(
            entry[2] == callee for entry in ranges):
        return False
    for returned in function_return_texts(code, callee, ranges):
        joined = returned.strip() + rest
        member = split_member(joined)
        if member and member_value_stands_object(
                code, member[0], member[1], pos, extras, ranges):
            return True
        if value_text_stands_object(
                code, joined, pos, extras, ranges,
                seen | {callee}):
            return True
    return False


def object_property_value(text, key):
    """The value a key names in an object or array literal.

    Returns the value's text, or None when the literal does
    not name the key in a shape this scan can read.
    """
    s = text.strip()
    while s.startswith("("):
        close = matching_close(s, 0)
        if close is None or s[close + 1:].strip():
            break
        s = s[1:close].strip()
    if isinstance(key, int):
        if not s.startswith("["):
            return None
        close = matching_close(s, 0)
        if close is None:
            return None
        elements = split_top_level(s[1:close])
        if key < len(elements):
            return elements[key]
        return None
    if not s.startswith("{"):
        return None
    close = matching_close(s, 0)
    if close is None:
        return None
    for prop in split_top_level(s[1:close]):
        getter = re.match(
            r"\s*get\s+([A-Za-z_$][\w$]*|\"[^\"]*\"|'[^']*')"
            r"\s*\(", prop)
        if getter and getter.group(1).strip("\"'") == key:
            # A getter's value is what its body returns, so
            # the walk continues on the return expressions.
            brace = prop.find("{", getter.end())
            if brace == -1:
                return None
            bclose = matching_close(prop, brace)
            if bclose is None:
                return None
            body = prop[brace + 1:bclose]
            returns = []
            for ret in re.finditer(
                    r"(?<![\w$.])return(?![\w$])", body):
                rtext, _ = expression_at(body, ret.end())
                if rtext.strip():
                    returns.append("(%s)" % rtext.strip())
            if not returns:
                return None
            if len(returns) == 1:
                return returns[0]
            return "(%s)" % ", ".join(returns)
        name, mark, value = prop.partition(":")
        if mark and name.strip().strip("\"'") == key:
            return value
        if not mark and name.strip() == key:
            return prop
    return None


def fed_value_stands_object(code, fed, keypath, pos, extras, ranges):
    """Whether the value a key path reaches in an argument
    can stand an object."""
    value = fed
    for key in keypath:
        value = object_property_value(value, key)
        if value is None:
            return False
    return value_text_stands_object(
        code, value, pos, extras, ranges)


def call_feeds_object(code, name, index, keypath, extras, ranges,
                      seen=frozenset()):
    """Whether a call site feeds an object to a parameter.

    A parameter stands for whatever the module's own call
    sites pass, so a parameter read as the file path is an
    options object read when a call site hands the function
    an object at that place, under the function's own name
    or a simple alias of it. A call site feeding the place
    through its own parameter is judged at that parameter's
    call sites in turn.
    """
    if name is None or name in seen:
        return False
    seen = seen | {name}
    targets = {name}
    for match in _ASSIGNMENT.finditer(code):
        text, _ = expression_at(code, match.end())
        if text.strip() == name:
            targets.add(match.group(1))
    for target in targets:
        for match in re.finditer(
                r"(?<![\w$])(?:[A-Za-z_$][\w$]*\s*\.\s*)?"
                + re.escape(target) + r"(?![\w$])",
                code):
            if code[:match.start()].rstrip().endswith("function"):
                continue
            call = re.match(r"\s*\(", code[match.end():])
            if not call:
                continue
            args = call_arguments(code, match.end() + call.end() - 1)
            if not args or index >= len(args):
                continue
            fed = args[index]
            if fed_value_stands_object(
                    code, fed, keypath, match.start(), extras, ranges):
                return True
            if keypath:
                continue
            caller = enclosing_function(code, match.start(), ranges)
            if caller is None or caller[2] is None:
                continue
            ident = re.fullmatch(r"\s*([A-Za-z_$][\w$]*)\s*", fed)
            if not ident:
                continue
            for other, segment in enumerate(caller[3]):
                if any(bound == ident.group(1) and not path
                        for bound, path in segment[3]):
                    if call_feeds_object(
                            code, caller[2], other, (), extras,
                            ranges, seen):
                        return True
    return False


def split_member(arg):
    """A member expression as its head and its key path.

    Returns the head text and the list of keys and indexes
    the expression walks, or None when the expression is
    not a member read. Dot, bracket and optional chain
    spellings all count as the same walk.
    """
    s = arg.strip()
    while s.startswith("("):
        close = matching_close(s, 0)
        if close is None:
            return None
        if s[close + 1:].strip():
            head, rest = s[1:close].strip(), s[close + 1:]
            break
        s = s[1:close].strip()
    else:
        head = None
        rest = None
    if rest is None:
        if s[:1] in "[{":
            close = matching_close(s, 0)
            if close is None:
                return None
            head, rest = s[:close + 1], s[close + 1:]
        else:
            ident = re.match(r"[A-Za-z_$][\w$]*", s)
            if not ident:
                return None
            head, rest = ident.group(0), s[ident.end():]
    keys = []
    rest = rest.strip()
    while rest:
        if rest.startswith("?."):
            rest = rest[2:].lstrip()
            ident = re.match(r"[A-Za-z_$][\w$]*", rest)
            if not ident:
                return None
            keys.append(ident.group(0))
            rest = rest[ident.end():].strip()
            continue
        if rest.startswith(".at("):
            close = matching_close(rest, 3)
            if close is None:
                return None
            inner = rest[4:close].strip()
            if not inner.isdigit():
                return None
            keys.append(int(inner))
            rest = rest[close + 1:].strip()
            continue
        if rest.startswith("."):
            ident = re.match(r"[A-Za-z_$][\w$]*", rest[1:].lstrip())
            if not ident:
                return None
            keys.append(ident.group(0))
            rest = rest[1:].lstrip()[ident.end():].strip()
            continue
        if rest.startswith("["):
            close = matching_close(rest, 0)
            if close is None:
                return None
            inner = rest[1:close].strip()
            if inner.isdigit():
                keys.append(int(inner))
            elif len(inner) >= 2 and inner[0] in "\"'" \
                    and inner[-1] == inner[0]:
                keys.append(inner[1:-1])
            elif re.fullmatch(r"[A-Za-z_$][\w$]*", inner):
                # An index held in a name, resolved by the
                # walk from the name's own binding.
                keys.append(("@", inner))
            else:
                return None
            rest = rest[close + 1:].strip()
            continue
        return None
    if not keys:
        return None
    return head, keys


def member_value_stands_object(code, head, keys, pos, extras, ranges):
    """Whether the value a member expression reaches can
    stand an object.

    The walk reads the head's own literal, or the literal
    the head name is latest bound to, one key at a time.
    A module top level binding of the head counts wherever
    it stands, as it does for the bound name walk, so a
    holder defined after the read answers the same as one
    defined before it. A step the literals cannot answer
    ends the walk as not standing, since the gate judges
    only what the module's own literals hold.
    """
    def resolve(key):
        # An index held in a name answers from the name's
        # latest binding before the walk, a number or a
        # quoted string, and anything else cannot answer.
        if not isinstance(key, tuple):
            return key
        bound = assignment_rhs(code, key[1], pos)
        if bound is None:
            return None
        bound = bound.strip()
        if bound.isdigit():
            return int(bound)
        if len(bound) >= 2 and bound[0] in "\"'" \
                and bound[-1] == bound[0]:
            return bound[1:-1]
        return None

    resolved = []
    for key in keys:
        key = resolve(key)
        if key is None:
            return False
        resolved.append(key)
    keys = resolved
    if re.fullmatch(r"[A-Za-z_$][\w$]*", head):
        # A member assignment after the head's own binding
        # can put the object in place, as in a holder whose
        # member is assigned an options object, and the
        # latest such assignment on the walked path decides.
        head_place = -1
        for plain in _ASSIGNMENT.finditer(code, 0, pos):
            if plain.group(1) == head:
                head_place = plain.start()
        chain_re = re.compile(
            r"(?<![\w$.])" + re.escape(head)
            + r"((?:\s*(?:\?\.|\.)\s*[A-Za-z_$][\w$]*"
            r"|\s*\[\s*(?:\"[^\"]*\"|'[^']*'|\d+"
            r"|[A-Za-z_$][\w$]*)\s*\])+)"
            r"\s*=(?![=>])")
        verdict = None
        for match in chain_re.finditer(code, 0, pos):
            if match.start() < head_place:
                continue
            chain = []
            for step in re.finditer(
                    r"\.\s*([A-Za-z_$][\w$]*)"
                    r"|\[\s*(?:\"([^\"]*)\"|'([^']*)'|(\d+)"
                    r"|([A-Za-z_$][\w$]*))\s*\]",
                    match.group(1)):
                groups = step.groups()
                if groups[4] is not None:
                    chain.append(("@", groups[4]))
                else:
                    chain.append(next(
                        group for group in groups[:4]
                        if group is not None))
            chain = [
                int(step) if isinstance(step, str)
                and step.isdigit() else step
                for step in chain
            ]
            chain = [resolve(step) for step in chain]
            if None in chain or chain != list(keys[:len(chain)]):
                continue
            current, _ = expression_at(code, match.end())
            ok = True
            for key in keys[len(chain):]:
                nxt = object_property_value(current, key)
                if nxt is None:
                    ok = False
                    break
                current = nxt
            if not ok:
                verdict = False
                continue
            verdict = argument_stands_object(current)
            if not verdict:
                ident = re.fullmatch(
                    r"\s*([A-Za-z_$][\w$]*)\s*", current)
                if ident:
                    verdict = binding_state_at(
                        code, ident.group(1), pos, extras, ranges)
        if verdict is not None:
            return verdict
        value = assignment_rhs(code, head, pos)
        if value is None:
            # A module top level binding counts wherever it
            # stands, the rule the bound name walk already
            # holds, so a holder the module defines after the
            # read still answers for the member walk, unless
            # the holding function declares the name itself.
            here = enclosing_function(code, pos, ranges)
            if here is not None and not declares_name(
                    code, head, here, pos):
                latest = None
                for match in _ASSIGNMENT.finditer(code):
                    if match.group(1) != head:
                        continue
                    if enclosing_function(
                            code, match.start(),
                            ranges) is None:
                        latest = match
                if latest is not None:
                    value, _ = expression_at(code, latest.end())
            if value is None:
                return False
    else:
        value = head
    for key in keys:
        value = object_property_value(value, key)
        if value is None:
            return False
    if argument_stands_object(value):
        return True
    ident = re.fullmatch(r"\s*([A-Za-z_$][\w$]*)\s*", value)
    if ident:
        return binding_state_at(
            code, ident.group(1), pos, extras, ranges)
    return False


def _parameter_read_problem(code, function, fed, at, extras, ranges):
    """The problem with a read through a parameter, or None.

    A parameter whose default stands an object is refused.
    A named function's parameter is refused where one of
    the function's own call sites feeds it an object, under
    any name the function stands under. An unnamed
    function's parameter is refused where the invocation
    at its own close feeds it an object, and refused
    outright where no invocation stands there, since
    nothing in the module then shows what feeds it.
    """
    index, keypath, default = fed
    if default is not None and fed_value_stands_object(
            code, default, keypath, at, extras, ranges):
        return (
            "the hooks module calls $.fs.read with a "
            "parameter whose default is an options "
            "object, where the host takes the path as "
            "its one argument, so the read would throw "
            "in a session and no verified packet could "
            "ever pass the gate"
        )
    names = [
        entry[2] for entry in ranges
        if entry[0] == function[0] and entry[1] == function[1]
        and entry[2] is not None
    ]
    if names:
        for name in names:
            if call_feeds_object(
                    code, name, index, keypath, extras, ranges):
                return (
                    "the hooks module calls $.fs.read with a "
                    "parameter its own call sites feed an options "
                    "object, where the host takes the path as its "
                    "one argument, so the read would throw in a "
                    "session and no verified packet could ever "
                    "pass the gate"
                )
        return None
    i = function[1]
    while i < len(code) and code[i].isspace():
        i += 1
    if code[i:i + 1] == "}":
        i += 1
        while i < len(code) and code[i].isspace():
            i += 1
    if code[i:i + 1] == ")":
        i += 1
        while i < len(code) and code[i].isspace():
            i += 1
    if code[i:i + 1] == "(":
        spans = argument_spans(code, i)
        if spans is not None and index < len(spans):
            s, e = spans[index]
            if fed_value_stands_object(
                    code, code[s:e], keypath, at, extras, ranges):
                return (
                    "the hooks module calls $.fs.read with a "
                    "parameter its own call sites feed an options "
                    "object, where the host takes the path as its "
                    "one argument, so the read would throw in a "
                    "session and no verified packet could ever "
                    "pass the gate"
                )
            return None
    return (
        "the hooks module calls $.fs.read with a "
        "parameter of an unnamed function, whose feeds "
        "no call site in the module shows, where the "
        "host takes the path as its one argument"
    )


def _catch_binding_at(code, name, pos):
    """The catch clause binding a name at a position.

    Returns the span of the try block whose catch clause
    binds the name around the position, or None where no
    catch clause does. A catch clause is read by its try
    block standing directly before it, so a method that
    happens to carry the catch name is no binding here.
    """
    found = None
    for match in re.finditer(r"(?<![\w$.])catch\s*\(", code):
        open_paren = match.end() - 1
        close_paren = matching_close(code, open_paren)
        if close_paren is None:
            continue
        param = code[open_paren + 1:close_paren].strip()
        if param != name and name not in pattern_bound_names(
                param):
            continue
        i = close_paren + 1
        while i < len(code) and code[i].isspace():
            i += 1
        if i >= len(code) or code[i] != "{":
            continue
        block_close = matching_close(code, i)
        if block_close is None or not (i < pos <= block_close):
            continue
        j = match.start() - 1
        while j >= 0 and code[j].isspace():
            j -= 1
        if j < 0 or code[j] != "}":
            continue
        try_open = None
        for opening in range(j):
            if code[opening] == "{" and \
                    matching_close(code, opening) == j:
                try_open = opening
        if try_open is None:
            continue
        before = code[:try_open].rstrip()
        if not re.search(r"(?<![\w$.])try$", before):
            continue
        if found is None or i > found[0]:
            found = (i, block_close, (try_open, j))
    if found is None:
        return None
    return found[2]


def _throw_texts_in(code, start, end, ranges, owner):
    """The throw expressions in a range owned by a function.

    A throw counts only where the given function is its
    innermost function and no catch inside the range
    answers it, the same protection the outcome reading
    gives a throw inside its own handler.
    """
    texts = []
    protected = _try_catch_intervals(code, start, end)
    for match in re.finditer(
            r"(?<![\w$.])throw(?![\w$])", code[start:end]):
        at = start + match.start()
        holder = enclosing_function(code, at, ranges)
        if owner is None:
            if holder is not None:
                continue
        elif holder is None or \
                (holder[0], holder[1]) != (owner[0], owner[1]):
            continue
        if any(opening <= at <= closing
               for opening, closing in protected):
            continue
        value, _ = expression_at(code, at + len("throw"))
        if value.strip():
            texts.append((at, value))
    return texts


def _catch_feed_stands_object(code, ranges, extras, try_span):
    """Whether a catch clause's try block throws an object.

    The feeds of a catch binding are the throws of its
    try block, judged the way a parameter's feeds are
    judged at its call sites. A throw in the block itself
    counts by its own expression, and a throw inside a
    local helper the block calls counts by that helper's
    throw expressions, followed through further local
    calls with each helper read once.
    """
    start, end = try_span
    owner = enclosing_function(code, start, ranges)
    regions = [(start, end, owner)]
    visited = set()
    while regions:
        region_start, region_end, region_owner = regions.pop()
        for at, value in _throw_texts_in(
                code, region_start, region_end, ranges,
                region_owner):
            if value_text_stands_object(
                    code, value, at, extras, ranges) or \
                    argument_stands_object(value):
                return True
        for call in re.finditer(
                r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(",
                code[region_start:region_end]):
            callee = call.group(1)
            if code[:region_start + call.start()].rstrip(
                    ).endswith("function"):
                continue
            for entry in ranges:
                if entry[2] != callee:
                    continue
                if (entry[0], entry[1]) in visited:
                    continue
                visited.add((entry[0], entry[1]))
                brace, close = _function_body_brace(code, entry)
                if brace is not None and close is not None:
                    regions.append((brace, close, entry))
    return False


def fs_read_problems(code):
    """Problems with the module's file read call sites.

    The scan reads code with its comments already stripped.
    The host takes the read's path as its one argument and
    never checks the shape at validation, so an options object
    reaches the read and throws in a session. The pin refuses
    an options object at every $.fs.read call site, standing
    in the call itself or in one of its branches, in
    parentheses inside the call, behind a name the module
    binds to an object literal in any
    binding spelling, where a module top level binding
    counts wherever it stands and a binding inside a
    function counts in its written order, behind a member
    holding one, behind a value bound by a catch clause
    where its try block throws an object the walk traces,
    behind an object produced by a rest destructuring of
    an object literal, or
    behind a parameter its own call sites feed an object,
    and it refuses any argument count but one, since the
    contract is the path as the read's one argument. The
    receiver spelling is judged as written, before
    normalisation, and a computed or optional member
    access on $, $.fs or the method is refused, as the
    host refuses it at load. A call shape standing inside
    a string, template or regex literal is quoted text and
    not a call site, so the scan skips a match whose head
    stands inside a literal span, the spans literal_spans
    computes on the normalised code. Code inside a template
    interpolation stands outside the spans and is judged.
    """
    code = decode_identifier_escapes(code)
    problems = receiver_spelling_problems(code, "fs")
    code = normalise_member_spellings(code)
    spans = literal_spans(code)
    ranges = function_ranges(code)
    extras = indirect_object_bindings(code)
    for match in _FS_CALL.finditer(code):
        if any(start <= match.start() <= end
                for start, end in spans):
            continue
        call = re.match(r"\s*\(", code[match.end():])
        if not call:
            problems.append(
                "the hooks module names $.fs.read without "
                "calling it, so its manifest read is not the "
                "path only call the contract pins"
            )
            continue
        open_paren = match.end() + call.end() - 1
        args = call_arguments(code, open_paren)
        if args is None:
            problems.append(
                "the hooks module calls $.fs.read in a call the "
                "gate cannot read to its closing parenthesis, "
                "so the read does not stand as the path only "
                "call the contract pins"
            )
            continue
        if len(args) != 1:
            problems.append(
                "the hooks module calls $.fs.read with %d top "
                "level arguments, where the contract pins the "
                "path as its one argument, so the call stands "
                "outside the path only read the gate certifies"
                % len(args)
            )
            continue
        if argument_stands_object(args[0]):
            problems.append(
                "the hooks module calls $.fs.read with an options "
                "object, where the host takes the path as its one "
                "argument, so the read would throw in a session and "
                "no verified packet could ever pass the gate"
            )
            continue
        arg = args[0].strip()
        if arg.startswith("..."):
            arg = arg[3:].lstrip()
        member = split_member(arg)
        if member:
            head, keys = member
            if member_value_stands_object(
                    code, head, keys, match.start(), extras, ranges):
                problems.append(
                    "the hooks module calls $.fs.read with an "
                    "options object held in a member, where the "
                    "host takes the path as its one argument, so "
                    "the read would throw in a session and no "
                    "verified packet could ever pass the gate"
                )
            continue
        if call_head_member_stands(
                code, arg, match.start(), extras, ranges):
            problems.append(
                "the hooks module calls $.fs.read with an "
                "options object held in a member, where the "
                "host takes the path as its one argument, so "
                "the read would throw in a session and no "
                "verified packet could ever pass the gate"
            )
            continue
        while arg.startswith("("):
            arg = arg[1:].lstrip()
        if arg.startswith("{"):
            # An object literal read through a member, as in
            # an options object's own .path, passes that member
            # and not the object, and split_member has already
            # judged the walk.
            continue
        callee = call_to_local_function(code, arg, ranges)
        if callee and any(
                value_text_stands_object(
                    code, returned, match.start(), extras, ranges)
                for returned in function_return_texts(
                    code, callee, ranges)):
            problems.append(
                "the hooks module calls $.fs.read with an options "
                "object, where the host takes the path as its one "
                "argument, so the read would throw in a session and "
                "no verified packet could ever pass the gate"
            )
            continue
        ident = re.match(r"[A-Za-z_$][\w$]*", arg)
        if ident:
            name = ident.group(0)
            function = enclosing_function(code, match.start(), ranges)
            fed = None
            if function is not None:
                for index, segment in enumerate(function[3]):
                    for bound, keypath in segment[3]:
                        if bound == name:
                            fed = (index, keypath, segment[4])
            catch_try = _catch_binding_at(
                code, name, match.start())
            if catch_try is not None and \
                    _catch_feed_stands_object(
                        code, ranges, extras, catch_try):
                problems.append(
                    "the hooks module calls $.fs.read with a "
                    "value bound by a catch clause to an "
                    "options object its try block throws, "
                    "where the host takes the path as its "
                    "one argument, so the read would throw "
                    "in a session and no verified packet "
                    "could ever pass the gate"
                )
            elif fed is not None:
                problem = _parameter_read_problem(
                    code, function, fed, match.start(), extras,
                    ranges)
                if problem is not None:
                    problems.append(problem)
            elif binding_state_at(
                    code, name, match.start(), extras, ranges):
                problems.append(
                    "the hooks module calls $.fs.read with a "
                    "variable bound in the module to an "
                    "options object, where the host takes the "
                    "path as its one argument, so the read would "
                    "throw in a session and no verified packet "
                    "could ever pass the gate"
                )
    return problems



# The structural family the gate certifies.
#
# The gate certifies the shipped module and the modules
# standing in its structural family, and it refuses a
# module standing outside the family rather than judge
# it. The family is the construct space the shipped
# module and the variants this programme has priced as
# legitimate exercise, with the shapes the repair
# programme proved the readings cannot judge standing
# outside it by name, and the shapes the brief
# names as residuals of the narrowed contract standing
# recorded there rather than refused here. The census
# below reads tokens and classifies constructs. It
# judges no outcome, traces no value and walks no flow,
# so widening the family is a matter of naming another
# construct in the brief beside the line here, never of
# teaching a reading a new shape.

_FAMILY_CONDITION_WORDS = frozenset({
    "await", "const", "delete", "false", "in",
    "instanceof", "let", "new", "null", "of", "true",
    "typeof", "undefined", "var", "void", "yield",
})

_FAMILY_ASSIGN_OPS = frozenset({
    "=", "+=", "-=", "*=", "/=", "%=", "**=", "<<=",
    ">>=", "&=", "|=", "^=", "&&=", "||=", "??=",
})

_FAMILY_OBJECT_WRITES = frozenset({
    "assign", "defineProperties", "defineProperty",
    "setPrototypeOf",
})

_FAMILY_REFLECT_WRITES = frozenset({
    "defineProperty", "deleteProperty", "set",
})

_FAMILY_HEAD_OK_WORDS = frozenset({
    "await", "case", "default", "delete", "do", "else",
    "export", "in", "instanceof", "new", "of", "return",
    "typeof", "void", "yield",
})

_FAMILY_REFUSAL = (
    "stands outside the structural family the mod gate "
    "certifies, so the gate refuses the module rather "
    "than certify a shape outside that family"
)


def _family_problem(construct):
    """The refusal problem for one out of family construct."""
    return "the hooks module carries %s, which %s" % (
        construct, _FAMILY_REFUSAL)


def _family_matching_open(tokens, index):
    """The index of the token opening the bracket one closes."""
    closer = tokens[index][1]
    opener = {"}": "{", ")": "(", "]": "["}[closer]
    depth = 0
    j = index
    while j >= 0:
        text = tokens[j][1]
        if text == closer:
            depth += 1
        elif text == opener:
            depth -= 1
            if depth == 0:
                return j
        j -= 1
    return None


_FAMILY_OBJECT_WORDS = frozenset({
    "await", "case", "default", "delete", "export",
    "import", "in", "instanceof", "new", "return",
    "throw", "typeof", "void", "yield",
})


def _family_brace_kind(tokens, index, colon_was_value,
                       after_literal=False):
    """The frame kind a brace token opens in the census walk.

    The previous significant token decides, the reading
    the slash judgement makes of the same position. A
    brace after a closing parenthesis opens the block the
    parenthesis headed, a switch block where the head is
    the switch word standing clear of a dot. A brace
    after one of the words catch, do, else, finally, try
    or static, after any other name, after a number,
    after a closing square bracket or after a postfix
    step opens a block, the statement position those
    endings leave, since no expression continues across
    one into a brace, and a brace standing after a
    literal the previous statement ended on opens a
    block the same way, the literal being an operand end
    the token walk skips. A brace after one of the
    object words, the words that demand an expression
    after them, opens an object. A brace after a value
    colon opens the object the colon's value stands as,
    and one after a case colon opens the clause's block.
    A brace after a semicolon, a closing brace, an
    opening brace or an arrow opens a block. Any other
    operator or opening bracket stands in expression
    position, so the brace opens an object.
    """
    if index == 0:
        return "block"
    prev = tokens[index - 1]
    if after_literal:
        return "block"
    if prev[1] == ")":
        open_index = _family_matching_open(tokens, index - 1)
        if open_index is not None and open_index >= 2:
            head = tokens[open_index - 1]
            before = tokens[open_index - 2]
            if head[1] == "switch" and \
                    before[1] not in (".", "?."):
                return "switch"
        return "block"
    if prev[0] == "word":
        if prev[1] in _FAMILY_OBJECT_WORDS:
            return "object"
        return "block"
    if prev[1] == ":":
        return "object" if colon_was_value else "block"
    if prev[1] in (";", "}", "{", "=>"):
        return "block"
    if prev[0] == "number" or prev[1] in ("]", "++", "--"):
        return "block"
    return "object"


def _family_method_position(tokens, index, frames):
    """Whether a word stands where a member names a method.

    A word standing in an object brace or a class body
    can name a method of that member list, where the
    same spelling in statement position is the construct
    itself. The word stands in method position where the
    token before it opens the member list, closes or
    separates one of its members, or stands as one of
    the modifier words get, set, static or async or as
    the generator star before the name.
    """
    if not frames or frames[-1][0] not in ("object", "class"):
        return False
    prev = tokens[index - 1] if index else None
    if prev is None:
        return False
    if prev[1] in ("{", "}", ",", ";", "*"):
        return True
    return prev[0] == "word" and prev[1] in (
        "async", "get", "set", "static")


def _family_matching_close(tokens, index):
    """The index of the token closing the bracket one opens."""
    opener = tokens[index][1]
    closer = {"{": "}", "(": ")", "[": "]"}[opener]
    depth = 0
    j = index
    while j < len(tokens):
        text = tokens[j][1]
        if text == opener:
            depth += 1
        elif text == closer:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return None


def _family_method_call(tokens, index, frames):
    """Whether a name at an index heads a method definition.

    A method definition stands in an object or a class
    frame, with its body's brace after the closing
    parenthesis of its own parenthesis pair, where a
    call of the same name is followed by anything else.
    A call standing in a statement, followed by a block
    of its own, matches the shape and is no method, so
    the frame the name stands in decides beside the
    brace, and a member name in that shape is a name and
    never the construct it spells, after a field or
    after a modifier alike.
    """
    if not frames or \
            frames[-1][0] not in ("object", "class"):
        return False
    if index + 1 >= len(tokens) or \
            tokens[index + 1][1] != "(":
        return False
    close = _family_matching_close(tokens, index + 1)
    return close is not None and \
        close + 1 < len(tokens) and \
        tokens[close + 1][1] == "{"


def _family_member_name(tokens, index, frames):
    """Whether a construct word stands as a member name.

    A word stands as a member name where it keys an
    object member, where it heads a method definition,
    or where it names a class field. A class field
    stands followed by an assignment sign, a semicolon
    or the class body's closing brace, or, where the
    word itself stands at an element boundary in the
    class body, behind its opening brace, a closing
    brace, a semicolon or a modifier word standing at
    one, by the class element that follows it. The
    boundary spelling asks for the boundary because a
    word standing behind an assignment sign stands
    inside a field initialiser's expression, where
    its constructs are constructs still. In those
    places the word is a name, never the construct
    it spells.
    """
    following = tokens[index + 1] \
        if index + 1 < len(tokens) else None
    if following is not None and \
            following[1] == ":" and \
            frames[-1][0] == "object":
        return True
    if _family_method_call(tokens, index, frames):
        return True
    if frames[-1][0] != "class" or following is None:
        return False
    if following[1] in ("=", ";", "}"):
        return True
    prev = tokens[index - 1] if index else None
    boundary = prev is not None and \
        prev[1] in ("{", "}", ";")
    if not boundary and prev is not None and \
            prev[0] == "word" and prev[1] in (
                "async", "get", "set", "static") and \
            index >= 2:
        boundary = tokens[index - 2][1] in ("{", "}", ";")
    return boundary and (
        following[0] == "word" or
        following[1] in ("[", "*"))


def _family_nested(frames):
    """Whether the census walk stands inside a nested block.

    A block, switch or class frame standing over the
    innermost function frame, or over the module top
    level where no function frame stands, makes the
    standing place nested. Object braces and the grouping
    brackets never do, since no declaration stands inside
    them.
    """
    for frame in reversed(frames):
        if frame[0] == "function":
            return False
        if frame[0] in ("block", "class", "switch"):
            return True
    return False


def _family_declarators(code, tokens, index, in_for_head=False):
    """The declarators of the declaration at a keyword token.

    Each entry carries the names one declarator binds and
    whether its target is a destructuring pattern. The
    walk stops at the semicolon ending the statement, at
    the closing bracket of the head the declaration
    stands in, or at a fresh declaration keyword. The in
    or of word opening a for head's right side stops the
    walk only where the declaration stands in a for head,
    which the caller states, and only where that word is
    no member name. In a plain declaration the same words
    are the in operator or a member name inside an
    earlier declarator's initialiser, and the walk reads
    past them, the fact the destructuring collection
    missed when its own walk stopped at the operator
    spelling.
    """
    declarators = []
    current = []
    depth = 0
    j = index + 1
    while j < len(tokens):
        kind, text = tokens[j][0], tokens[j][1]
        if text in ("(", "[", "{"):
            depth += 1
            current.append(tokens[j])
        elif text in (")", "]", "}"):
            if depth == 0:
                break
            depth -= 1
            current.append(tokens[j])
        elif depth == 0 and text == ";":
            break
        elif depth == 0 and text == ",":
            declarators.append(current)
            current = []
        elif depth == 0 and kind == "word" and (
                text in ("const", "let", "var") or (
                    in_for_head and text in ("in", "of"))) and (
                not current or current[-1][1] not in (".", "?.")):
            break
        else:
            current.append(tokens[j])
        j += 1
    declarators.append(current)
    out = []
    for declarator in declarators:
        if not declarator:
            out.append(([], False))
            continue
        first = declarator[0]
        if first[1] in ("{", "["):
            depth = 0
            pattern = []
            for token in declarator:
                pattern.append(token)
                if token[1] in ("{", "["):
                    depth += 1
                elif token[1] in ("}", "]"):
                    depth -= 1
                    if depth == 0:
                        break
            text = code[pattern[0][2]:pattern[-1][3]]
            names = [bound for bound, _ in pattern_key_map(text)]
            out.append((names, True))
        elif first[0] == "word":
            out.append(([first[1]], False))
        else:
            out.append(([], False))
    return out


def _family_member_segments(tokens, index):
    """The member steps of the chain ending at a token.

    Counts the dot and bracket steps behind the token, so
    an assignment or a postfix step standing after a
    chain with a step in it writes through a member,
    where a plain name writes through nothing. A bracket
    step counts as the step it is before the walk reads
    what stands behind its opening bracket, so a chain
    whose head step is a bracket on a bare name still
    counts, the lookback the census missed when it
    answered nothing for that chain.
    """
    segments = 0
    j = index
    while j >= 0:
        text = tokens[j][1]
        if text == "]":
            segments += 1
            j = _family_matching_open(tokens, j)
            if j is None:
                return segments
            j -= 1
            continue
        if text == ")":
            j = _family_matching_open(tokens, j)
            if j is None:
                return segments
            j -= 1
            if j >= 0 and tokens[j][1] in (".", "?."):
                segments += 1
                j -= 1
                continue
            return segments
        if tokens[j][0] in ("word", "number"):
            if j >= 1 and tokens[j - 1][1] in (".", "?."):
                segments += 1
                j -= 2
                continue
            return segments
        return segments
    return segments


def _family_loop_condition(tokens, index):
    """The condition tokens of the loop head at an index.

    A while head answers the whole of its parenthesised
    text. A for head answers its middle segment, the
    condition standing between its two semicolons, and a
    for head with fewer than two semicolons, the of and
    in forms among them, answers None, since those heads
    carry no condition a flow reading could misread.
    """
    if index + 1 >= len(tokens) or tokens[index + 1][1] != "(":
        return None
    depth = 0
    head = []
    j = index + 1
    while j < len(tokens):
        text = tokens[j][1]
        if text == "(":
            depth += 1
            if depth > 1:
                head.append(tokens[j])
        elif text == ")":
            depth -= 1
            if depth == 0:
                break
            head.append(tokens[j])
        else:
            head.append(tokens[j])
        j += 1
    if tokens[index][1] == "while":
        return head
    parts = [[]]
    depth = 0
    for token in head:
        text = token[1]
        if text in ("(", "[", "{"):
            depth += 1
        elif text in (")", "]", "}"):
            depth -= 1
        if text == ";" and depth == 0:
            parts.append([])
        else:
            parts[-1].append(token)
    if len(parts) < 3:
        return None
    return parts[1]


def _family_in_for_head(tokens, index):
    """Whether a declaration keyword stands in a for head.

    The keyword stands in a for head where the token
    before it is the head's opening parenthesis and the
    word for stands before that parenthesis, behind the
    await word of a for await head where one stands,
    clear of a dot.
    """
    j = index - 1
    if j < 1 or tokens[j][1] != "(":
        return False
    head = j - 1
    if tokens[head][1] == "await":
        head -= 1
    if head < 0 or tokens[head][1] != "for":
        return False
    return head < 1 or tokens[head - 1][1] not in (".", "?.")


def _family_class_braces(tokens):
    """The start positions of the braces opening class bodies.

    A class body brace is the first brace standing at
    bracket depth zero after the class word, the extends
    expression riding inside its own brackets until
    then. A brace the walk would otherwise read by its
    previous token alone, the class name word before it,
    opens the member list the census frames as a class,
    so a declaration inside a static block in that body
    stands in a frame the nested reading counts.
    """
    starts = set()
    for i, token in enumerate(tokens):
        if token[0] != "word" or token[1] != "class":
            continue
        if i and tokens[i - 1][1] in (".", "?."):
            continue
        depth = 0
        j = i + 1
        while j < len(tokens):
            text = tokens[j][1]
            if text in ("(", "[", "{"):
                if text == "{" and depth == 0:
                    starts.add(tokens[j][2])
                    break
                depth += 1
            elif text in (")", "]", "}"):
                if depth == 0:
                    break
                depth -= 1
            elif text == ";" and depth == 0:
                break
            j += 1
    return starts


def _family_template_hole_end(text, index):
    """The index of the brace closing a template hole."""
    depth = 0
    i = index
    while i < len(text):
        ch = text[i]
        if ch in "'\"`":
            quote = ch
            i += 1
            while i < len(text) and text[i] != quote:
                if text[i] == "\\":
                    i += 1
                i += 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _family_wraps_whole(text):
    """Whether a text's first parenthesis closes at its end."""
    depth = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "'\"`":
            quote = ch
            i += 1
            while i < len(text) and text[i] != quote:
                if text[i] == "\\":
                    i += 1
                i += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i == len(text) - 1
        i += 1
    return False


def _family_one_literal(text):
    """The value one string or template literal spells.

    A string literal answers by the gate's own contents
    decoder, every escape spelling it allows. A template
    literal answers the same way where each of its holes
    stands as one string literal itself, the decoded
    values joining the text around them, and a hole
    standing as anything else spells no plain name.
    Parentheses grouping the literal alone unwrap first,
    since a grouped literal spells the name it spells.
    """
    text = text.strip()
    while len(text) >= 2 and text[0] == "(" and \
            _family_wraps_whole(text):
        text = text[1:-1].strip()
    if len(text) < 2:
        return None
    if text[0] in "'\"" and text[-1] == text[0]:
        return _decode_string_contents(text[1:-1])
    if text[0] == "`" and text[-1] == "`":
        body = text[1:-1]
        out = []
        i = 0
        while i < len(body):
            if body[i] == "\\":
                out.append(body[i:i + 2])
                i += 2
                continue
            if body[i] == "$" and body[i + 1:i + 2] == "{":
                end = _family_template_hole_end(body, i + 1)
                if end is None:
                    return None
                value = _family_one_literal(
                    body[i + 2:end].strip())
                if value is None:
                    return None
                out.append(value)
                i = end + 1
                continue
            out.append(body[i])
            i += 1
        return _decode_string_contents("".join(out))
    return None


def _family_literal_value(raw):
    """The name a literal or a join of literals spells.

    The text is one literal, or literals joined by the
    plus sign at its own level, the spellings a bracket
    member name can stand in. Anything else standing
    between the brackets, a name, a call, a number,
    spells no name the census can read.
    """
    parts = []
    depth = 0
    start = 0
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch in "'\"`":
            quote = ch
            i += 1
            while i < len(raw) and raw[i] != quote:
                if raw[i] == "\\":
                    i += 1
                i += 1
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "+" and depth == 0:
            parts.append(raw[start:i])
            start = i + 1
        i += 1
    parts.append(raw[start:])
    out = []
    for part in parts:
        value = _family_one_literal(part.strip())
        if value is None:
            return None
        out.append(value)
    return "".join(out)


def _family_bracket_literal(code, open_token, close_token):
    """The text of the literal standing between two tokens.

    A bracket member spelling names its member with a
    literal the token walk skips whole, so the name is
    read back from the raw text standing between the
    bracket tokens and judged by the value it spells.
    """
    raw = code[open_token[3]:close_token[2]].strip()
    return _family_literal_value(raw)


def _family_handler_names(code, ranges):
    """The handler names the registration calls bind.

    The names are read from the calls the registration
    reading reads, where an argument standing as one
    plain identifier names the handler it registers. An
    inline handler names nothing, so no declaration can
    stand in its place and the block scope census has no
    name to guard for that registration.
    """
    names = set()
    for _, _, args, close in _registration_calls(code, ranges):
        if len(args) >= 2:
            text = code[args[1][0]:args[1][1]].strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", text):
                names.add(text)
        caught = _catch_argument(code, close + 1)
        if caught is not None:
            text = code[caught[0]:caught[1]].strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", text):
                names.add(text)
    return names


def _family_head_problems(code, tokens, spans):
    """The refusal for a head after a statement no semicolon ends.

    A function declaration binds at its scope's
    instantiation only where its head stands where a
    statement can stand. A head whose previous
    significant token is an operand end, a name, a
    number, a closing square bracket or a postfix step,
    is a declaration standing after a statement the
    grammar ended by insertion, and the binding reading
    cannot place it, so the shape stands outside the
    family. The previous token is read from the token
    walk the census shares, and a literal ending the
    statement counts as the operand it is, read from
    the character standing before the head in the
    stripped text, where a quote or a backtick can only
    close the literal the statement ended on and a
    slash can only close the regex the statement ended
    on. A closing parenthesis answers by the word
    heading the parenthesis, a control word standing
    clear of a dot leaving a statement to start, any
    other word closing a call the statement ended on,
    and a member name after a dot heading the
    parenthesis as a method the statement called,
    never as the control word it spells.
    """
    refusal = _family_problem(
        "a function declaration standing after a statement "
        "no semicolon ends")
    for match in _FUNCTION_DECL.finditer(code):
        if any(start <= match.start() <= end
                for start, end in spans):
            continue
        j = match.start() - 1
        while j >= 0 and code[j].isspace():
            j -= 1
        if j >= 0 and code[j] in "\"'`/":
            return [refusal]
        prev = None
        prev_index = None
        for index, token in enumerate(tokens):
            if token[3] <= match.start():
                prev = token
                prev_index = index
            else:
                break
        if prev is None:
            continue
        if prev[1] in ("{", "}", ";"):
            continue
        if prev[0] == "word":
            if prev[1] in _FAMILY_HEAD_OK_WORDS:
                continue
            return [refusal]
        if prev[0] == "number":
            return [refusal]
        if prev[1] == "]":
            return [refusal]
        if prev[1] in ("++", "--"):
            return [refusal]
        if prev[1] == ")":
            open_index = _family_matching_open(tokens, prev_index)
            head = tokens[open_index - 1] \
                if open_index else None
            before = tokens[open_index - 2] \
                if open_index is not None and open_index >= 2 \
                else None
            if head is not None and head[0] == "word" and \
                    head[1] in _CONTROL_HEAD_WORDS and \
                    (before is None or
                     before[1] not in (".", "?.")):
                continue
            return [refusal]
    return []


def _family_pattern_member_target(tokens, close_index):
    """Whether a destructuring pattern targets a member.

    The pattern closing at the given bracket assigns
    through a member where a dot step stands on the
    target side of the pattern. Each nested bracket
    frame is a target frame where it stands on the
    target side of its parent, before the parent's
    default sign, and a target standing in parentheses
    is the target still, since the grammar groups a
    reference without changing it. An opening square
    bracket standing where an object pattern expects a
    key is a computed key bracket, whose contents read
    rather than write. A dot behind a default sign, or
    inside a computed key bracket, or inside a frame
    standing on a default side, reads the member rather
    than write it, and a plain name pattern carries no
    dot at all, so those targets write through nothing.
    """
    open_index = _family_matching_open(tokens, close_index)
    if open_index is None:
        return False
    frames = []
    paren = 0
    j = open_index
    while j <= close_index:
        text = tokens[j][1]
        if text in ("{", "["):
            if frames:
                parent = frames[-1]
                target = parent[2] and not parent[1]
                if text == "[" and parent[0] == "{" and \
                        parent[3]:
                    target = False
            else:
                target = True
            frames.append([text, False, target, True])
        elif text in ("}", "]"):
            if frames:
                frames.pop()
        elif text == "(":
            paren += 1
        elif text == ")":
            paren -= 1
        elif paren == 0 and frames and text == ",":
            frames[-1][1] = False
            frames[-1][3] = True
        elif paren == 0 and frames and text == ":":
            frames[-1][3] = False
        elif paren == 0 and frames and text == "=":
            frames[-1][1] = True
        elif frames and text in (".", "?.") and \
                frames[-1][2] and not frames[-1][1]:
            return True
        j += 1
    return False


_FAMILY_NON_OPERAND_WORDS = frozenset({
    "await", "case", "catch", "class", "const",
    "default", "delete", "do", "else", "export",
    "extends", "finally", "for", "function", "if",
    "import", "in", "instanceof", "let", "new",
    "return", "switch", "throw", "try", "typeof",
    "var", "void", "while", "with", "yield",
})


def _family_chain_bracket(tokens, close_index):
    """Whether a closing bracket ends a member chain.

    A square bracket whose opening bracket stands
    behind an operand, a plain name, a number or a
    closing bracket of its own, closes a step of the
    chain that operand heads. A square bracket standing
    behind a keyword, an opening bracket, a comma, a
    default sign or nothing opens a destructuring
    pattern instead, the declaration keyword before an
    array pattern being the spelling that names it.
    """
    open_index = _family_matching_open(tokens, close_index)
    if open_index is None or open_index == 0:
        return False
    before = tokens[open_index - 1]
    if before[0] == "word":
        return before[1] not in _FAMILY_NON_OPERAND_WORDS
    return before[0] == "number" or before[1] in ("]", ")")


def _family_unwrapped_end(tokens, index):
    """The last token of a target, parentheses unwrapped.

    A grouped reference is the reference it groups, so
    a target standing in parentheses ends at the token
    its innermost parenthesis holds at its end, the
    token standing just inside the innermost closing
    parenthesis, where a reading that judges a target
    by its last token can see it.
    """
    j = index
    while j >= 0 and tokens[j][1] == ")":
        if _family_matching_open(tokens, j) is None:
            return index
        j -= 1
    return j


def _family_write_target(tokens, index):
    """Whether the write target ending at an index is a member.

    The target is unwrapped from any parentheses around
    it, then judged the way every write target in the
    census is judged, a pattern by the targets it
    carries and a chain by the steps behind its last
    name.
    """
    end = _family_unwrapped_end(tokens, index)
    prev = tokens[end]
    if prev[1] == "}" or (
            prev[1] == "]" and
            not _family_chain_bracket(tokens, end)):
        return _family_pattern_member_target(tokens, end)
    return _family_member_segments(tokens, end) > 0


def _family_receiver_end(tokens, index):
    """The token index just past a possibly grouped name.

    Parentheses grouping a name alone are unwrapped, one
    pair or several, so the member step after them stands
    where a reading of the name expects it. A parenthesis
    pair whose opening stands behind a name, a number or
    a closing bracket is a call's own pair and unwraps
    nothing, and a pair holding anything beside the name
    and its own parentheses groups an expression, not
    the name.
    """
    j = index + 1
    while j < len(tokens) and tokens[j][1] == ")":
        open_index = _family_matching_open(tokens, j)
        if open_index is None:
            break
        before = tokens[open_index - 1] \
            if open_index else None
        if before is not None and (
                before[0] in ("word", "number") or
                before[1] in ("]", ")")):
            break
        if any(tokens[k][1] not in ("(", ")") and k != index
               for k in range(open_index + 1, j)):
            break
        j += 1
    return j


def _family_call_follows(tokens, index):
    """Whether a call step stands at a token index.

    The call step is the parenthesis itself, or the
    optional step and the parenthesis behind it.
    """
    if index < len(tokens) and tokens[index][1] == "(":
        return True
    return index + 1 < len(tokens) and \
        tokens[index][1] == "?." and \
        tokens[index + 1][1] == "("


def _family_for_target_problem(tokens, index):
    """The refusal a for head draws for a member target.

    A for of or for in head writes its target on every
    turn, so a member standing as that target is written
    with no assignment token anywhere in the module for
    the other readings to see. The head's target is the
    text before the of or in word at the head's own
    depth, and a target carrying a declaration keyword
    binds a fresh name rather than write through one.
    The target is judged the way an assignment target
    is judged, a pattern by the targets it carries and
    a chain by the steps behind its last name, so a
    plain pattern binds and a member target writes by
    the same reading in either place.
    """
    j = index + 1
    if j < len(tokens) and tokens[j][1] == "await":
        j += 1
    if j >= len(tokens) or tokens[j][1] != "(":
        return None
    depth = 0
    target_end = None
    declared = False
    k = j
    while k < len(tokens):
        text = tokens[k][1]
        if text in ("(", "[", "{"):
            depth += 1
        elif text in (")", "]", "}"):
            depth -= 1
            if depth == 0:
                break
        elif depth == 1 and tokens[k][0] == "word" and \
                text in ("in", "of") and \
                tokens[k - 1][1] not in (".", "?."):
            target_end = k - 1
            break
        elif depth == 1 and tokens[k][0] == "word" and \
                text in ("const", "let", "var"):
            declared = True
        k += 1
    if target_end is None or declared:
        return None
    if _family_write_target(tokens, target_end):
        return _family_problem(
            "an assignment through a member of an object")
    return None


def family_problems(code):
    """Problems of family scope with the hooks module source.

    The census reads the comment stripped, escape decoded
    text the other readings read, with the literal spans
    skipped whole, so a construct spelling quoted in a
    string, a template text or a regex certifies nothing
    and refuses nothing. Each construct standing outside
    the family draws the refusal for its kind.
    """
    problems = []

    def add(message):
        if message not in problems:
            problems.append(message)

    spans = literal_spans(code)
    tokens = _reach_tokens(code, 0, len(code), spans)
    ranges = function_ranges(code)
    names = _family_handler_names(code, ranges)
    body_braces = set()
    for entry in ranges:
        brace, _ = _function_body_brace(code, entry)
        if brace is not None:
            body_braces.add(brace)
    class_braces = _family_class_braces(tokens)
    frames = [["top", 0]]
    colon_was_value = False
    i = 0
    while i < len(tokens):
        kind, text, start, end = tokens[i]
        prev = tokens[i - 1] if i else None
        dotted = prev is not None and prev[1] in (".", "?.")
        if text == "(":
            frames.append(["paren", 0])
        elif text == "[":
            frames.append(["bracket", 0])
        elif text == "{":
            if start in body_braces:
                frames.append(["function", 0])
            elif start in class_braces:
                frames.append(["class", 0])
            else:
                after_literal = prev is not None and any(
                    prev[3] <= span[0] and span[1] < start
                    for span in spans)
                frames.append([
                    _family_brace_kind(
                        tokens, i, colon_was_value,
                        after_literal=after_literal),
                    0])
        elif text in (")", "]", "}"):
            if len(frames) > 1:
                frames.pop()
        elif text == "?":
            frames[-1][1] += 1
        elif text == ":":
            if frames[-1][1] > 0:
                frames[-1][1] -= 1
                colon_was_value = True
            elif frames[-1][0] in ("paren", "bracket", "object"):
                colon_was_value = True
            elif frames[-1][0] == "switch":
                colon_was_value = False
            else:
                colon_was_value = False
                add(_family_problem("a labelled statement"))
        elif kind == "word" and not dotted:
            in_method = _family_method_position(
                tokens, i, frames)
            if text in names and prev is not None and \
                    prev[1] == "[" and \
                    i + 1 < len(tokens) and \
                    tokens[i + 1][1] == "]":
                add(_family_problem(
                    "a handler name %s standing alone "
                    "inside brackets" % text))
            if text in ("while", "for"):
                if not in_method and frames[-1][0] != "class":
                    condition = _family_loop_condition(tokens, i)
                    if condition is not None and not any(
                            token[0] == "word" and
                            token[1] not in _FAMILY_CONDITION_WORDS
                            for token in condition):
                        add(_family_problem(
                            "a loop whose condition reads no "
                            "state the module holds"))
                    if text == "for":
                        target = _family_for_target_problem(
                            tokens, i)
                        if target is not None:
                            add(target)
            elif text in ("const", "let", "var"):
                declarators = _family_declarators(
                    code, tokens, i,
                    in_for_head=_family_in_for_head(tokens, i))
                for position, (bound, pattern) in enumerate(
                        declarators):
                    if pattern and position > 0:
                        add(_family_problem(
                            "a destructuring pattern standing "
                            "after the first declarator of its "
                            "declaration"))
                    if text in ("const", "let") and names and \
                            _family_nested(frames):
                        for name in bound:
                            if name in names:
                                add(_family_problem(
                                    "a declaration of the "
                                    "handler name %s under "
                                    "const or let inside a "
                                    "block" % name))
            elif text == "delete":
                if not _family_member_name(tokens, i, frames):
                    add(_family_problem("a delete operator"))
            elif text in ("Object", "Reflect"):
                writes = _FAMILY_OBJECT_WRITES \
                    if text == "Object" else _FAMILY_REFLECT_WRITES
                method = None
                j = _family_receiver_end(tokens, i)
                if j + 1 < len(tokens) and \
                        tokens[j][1] in (".", "?.") and \
                        tokens[j + 1][1] in writes and \
                        _family_call_follows(tokens, j + 2):
                    method = tokens[j + 1][1]
                bracket = None
                if method is None and j < len(tokens) and \
                        tokens[j][1] == "[":
                    bracket = j
                if method is None and bracket is None and \
                        j + 1 < len(tokens) and \
                        tokens[j][1] == "?." and \
                        tokens[j + 1][1] == "[":
                    bracket = j + 1
                if bracket is not None:
                    close = _family_matching_close(
                        tokens, bracket)
                    if close is not None and \
                            _family_call_follows(
                                tokens, close + 1):
                        named = _family_bracket_literal(
                            code, tokens[bracket],
                            tokens[close])
                        if named in writes:
                            method = named
                if method is not None:
                    add(_family_problem(
                        "a call to %s.%s" % (text, method)))
            elif text == "Proxy":
                if not _family_member_name(tokens, i, frames):
                    add(_family_problem("the Proxy constructor"))
            elif text == "eval":
                following = tokens[i + 1] \
                    if i + 1 < len(tokens) else None
                direct = following is not None and \
                    following[1] == "("
                closings = 0
                k = i + 1
                while k < len(tokens) and \
                        tokens[k][1] == ")":
                    closings += 1
                    k += 1
                openings = 0
                m = i - 1
                while m >= 0 and tokens[m][1] == "(":
                    openings += 1
                    m -= 1
                grouped = closings >= 1 and \
                    openings >= closings and \
                    k < len(tokens) and tokens[k][1] == "("
                if (direct or grouped) and \
                        not _family_member_name(
                            tokens, i, frames):
                    add(_family_problem("a call to eval"))
            elif text == "Function":
                following = tokens[i + 1] \
                    if i + 1 < len(tokens) else None
                called = following is not None and \
                    following[1] == "("
                built = prev is not None and prev[1] == "new"
                if (called or built) and \
                        not _family_member_name(
                            tokens, i, frames):
                    add(_family_problem(
                        "the Function constructor"))
        elif text in _FAMILY_ASSIGN_OPS:
            if i and _family_write_target(tokens, i - 1):
                add(_family_problem(
                    "an assignment through a member of "
                    "an object"))
        elif kind == "op" and text in ("++", "--"):
            before = tokens[i - 1] if i else None
            if before is not None and (
                    before[0] in ("word", "number")
                    or before[1] in ("]", ")")):
                if _family_write_target(tokens, i - 1):
                    add(_family_problem(
                        "a step through a member of an object"))
            elif i + 1 < len(tokens) and \
                    tokens[i + 1][1] == "(":
                close = _family_matching_close(tokens, i + 1)
                if close is not None and \
                        _family_write_target(tokens, close):
                    add(_family_problem(
                        "a step through a member of an object"))
            elif i + 2 < len(tokens) and \
                    tokens[i + 1][0] == "word" and \
                    tokens[i + 2][1] in (".", "?.", "["):
                add(_family_problem(
                    "a step through a member of an object"))
        i += 1
    problems.extend(_family_head_problems(code, tokens, spans))
    return problems


def export_problems(code):
    """Problems with the module's named export surface.

    The module exports register and nothing else. An inline
    export on a declaration and a trailing export list are
    the two spellings the reading collects, and in a list
    the exported name is the name after an as, the name a
    consumer binds. A default word standing before a value
    carries no name, so it stands outside this reading the
    way it stands outside the name readings elsewhere in
    this gate. The code stands stripped and decoded, and
    an export word inside a literal is no export.
    """
    problems = []
    exported = []
    spans = literal_spans(code)
    for match in re.finditer(r"\bexport\b", code):
        if any(start <= match.start() <= end
                for start, end in spans):
            continue
        rest = code[match.end():].lstrip()
        if rest.startswith("{"):
            brace = code.index("{", match.end())
            close = matching_close(code, brace)
            if close is None:
                continue
            for item in code[brace + 1:close].split(","):
                item = item.strip()
                if not item:
                    continue
                name = item.split(" as ")[-1].strip()
                name = name.strip("'\"")
                if name:
                    exported.append(name)
        elif rest.startswith("*"):
            exported.append("*")
        else:
            declared = re.match(
                r"(?:async\s+)?(?:function\s*\*?\s*|class\s+|"
                r"const\s+|let\s+|var\s+)([A-Za-z_$][\w$]*)",
                rest,
            )
            if declared:
                exported.append(declared.group(1))
    if "register" not in exported:
        problems.append(
            "the hooks module does not export register, so "
            "the host has no registration entry to load"
        )
    for name in sorted(set(exported)):
        if name != "register":
            problems.append(
                "the hooks module exports %s beside register, "
                "so its surface is wider than the one "
                "registration the contract pins" % name
            )
    return problems


def verified_equality_problems(code):
    """Problems with the equality the verified check stands on.

    The one comparison the whole spawn gate turns on is the
    manifest verified flag against true, and the shipped
    module spells it with the strict equality operator, so
    a value that is merely truthy never passes. The loose
    spelling reads almost the same and widens the gate to
    any truthy value the manifest carries, and the
    structural census tolerates either operator, so the
    loose form once passed every reading in this gate. The
    pin is two sided. No loose equality or loose inequality
    operator stands anywhere in the module outside a
    literal, in either operand order and under any alias,
    because the module needs no loose comparison for any
    of its checks. And the verified comparison itself must
    stand in its shipped strict form, a member read of the
    verified flag compared strictly against true, so an
    alias that carries the flag away from the comparison
    draws the same refusal as the loose operator does.
    """
    problems = []
    spans = literal_spans(code)
    for match in re.finditer(r"==|!=", code):
        if match.group(0) == "==" and code[match.end():match.end() + 1] == "=":
            continue
        if match.group(0) == "!=" and code[match.end():match.end() + 1] == "=":
            continue
        if any(start <= match.start() <= end for start, end in spans):
            continue
        problems.append(
            "the hooks module compares with the loose "
            "operator %s, and every comparison in the module "
            "stands in its strict form so a truthy value can "
            "never stand in for the verified flag"
            % match.group(0)
        )
        break
    if not re.search(r"\.verified\s*===\s*true\b", code):
        problems.append(
            "the hooks module does not compare the manifest "
            "verified flag against true with the strict "
            "equality operator in its shipped form, so the "
            "one comparison the spawn gate turns on does "
            "not stand pinned"
        )
    return problems


def module_problems(path):
    """Problems with the hooks module source."""
    problems = []
    if path.exists() and not path.is_file():
        return [
            "the hooks module at %s cannot be read, "
            "it is not a regular file" % path
        ]
    source = path.read_text(encoding="utf-8")
    stripped = strip_comments(source)
    decoded = decode_identifier_escapes(stripped)
    problems.extend(family_problems(decoded))
    problems.extend(registration_problems(decoded))
    problems.extend(export_problems(decoded))
    if "onFailure" in source:
        problems.append(
            "the hooks module uses the struck onFailure language, a "
            "category error on the Mods surface"
        )
    if "--mod" in source:
        problems.append(
            "the hooks module uses the withdrawn --mod flag"
        )
    if "disable-model-invocation" in source:
        problems.append(
            "the hooks module touches disable-model-invocation, which "
            "stays at its default false"
        )
    problems.extend(verified_equality_problems(decoded))
    code = normalise_member_spellings(decoded)
    ranges = function_ranges(code)
    problems.extend(dollar_value_problems(code, ranges, decoded))
    problems.extend(alien_receiver_problems(code))
    # The call pins receive the stripped source with its
    # member spellings as written, so their receiver scan
    # can judge a computed or optional spelling before
    # their own normalisation erases it for the argument
    # scans. Identifier escapes in a member name stand
    # decoded in that reading, as the host's parser reads
    # them, so an escaped noun or method is judged as the
    # plain member it spells. Every other scan keeps the
    # normalised reading it has always read.
    problems.extend(env_call_problems(decoded))
    problems.extend(fs_read_problems(decoded))
    calls = set()
    spans = literal_spans(code)
    for call in re.finditer(
            r"\$\s*\.\s*([A-Za-z_$][\w$]*)"
            r"(?:\s*\.\s*([A-Za-z_$][\w$]*))?", code):
        if any(start <= call.start() <= end
                for start, end in spans):
            continue
        calls.add(
            "$." + call.group(1)
            + ("." + call.group(2) if call.group(2) else ""))
    for call in sorted(calls):
        if call not in ALLOWED_API_CALLS:
            problems.append(
                "the hooks module calls %s, outside the allowlist, so "
                "a model judgment could replace the deterministic check"
                % call
            )
    return problems


def brief_problems():
    """Problems with the mod brief's stated contract."""
    problems = []
    if BRIEF.exists() and not BRIEF.is_file():
        return [
            "cannot read docs/mod-build7.md, "
            "it is not a regular file"
        ]
    try:
        raw = BRIEF.read_text(encoding="utf-8")
    except OSError as exc:
        return ["cannot read docs/mod-build7.md, %s" % exc]
    text = re.sub(r"\s+", " ", raw)
    for sentence, label in (
        (LIMIT_SENTENCE, "the second layer fail open limit"),
        (BOUNDARY_SENTENCE, "the in session gating boundary"),
        (GATE_CHECK, "the deployment gate check"),
        (FLAG_RECONCILIATION, "the disable-model-invocation reconciliation"),
        (
            "offers the mod as its own marketplace entry, "
            "named recognitio-mod",
            "the marketplace entry",
        ),
        (
            "The module validates clean on Claude Code 2.1.314 "
            "with its agent.spawn hook named in the gating "
            "hooks report with its catch flag set",
            "the live validation claim",
        ),
        (
            "The mod needs Claude Code v2.1.287 or later, the "
            "first build with mods, and stands live tested "
            "on 2.1.314",
            "the version floor",
        ),
        (
            "The gate reads a loop condition's shape, not its "
            "value, so a loop condition that is constant in "
            "fact but not in spelling, standing as a name the "
            "module bound to a literal, as a member of a "
            "literal, or against a bound no spelling can "
            "reach, reads as state under the census while the "
            "loop it heads never ends.",
            "the loop condition residual",
        ),
        (
            "A bare local call that never returns, standing "
            "before the registration, reads as the delegation "
            "the family tolerates while the registration it "
            "precedes never runs.",
            "the bare local call residual",
        ),
        (
            "A call that writes into an object, reached "
            "through a receiver whose identity the census "
            "does not judge, an alias holding the constructor "
            "or the constructor reached through the global "
            "object, reads as a call on a name the census "
            "leaves alone while the write lands the same way.",
            "the write call through an unjudged receiver "
            "residual",
        ),
        (
            "A write through a member standing as one clause "
            "of a comma sequence inside a returned value "
            "reads as the value it stands in, since the write "
            "readings judge statements and a sequence clause "
            "is a value position.",
            "the comma sequence write residual",
        ),
        (
            "A handler standing under an export alias, or "
            "under a differently cased export name beside the "
            "name the registration binds, reads as the export "
            "it stands under, since the readings judge the "
            "names the module's own text binds.",
            "the export alias residual",
        ),
        (
            "A call to eval reached through a member chain "
            "reads as a call on the receiver it stands "
            "behind.",
            "the member chain eval residual",
        ),
        (
            "A regex literal spelled inside a template "
            "literal's hole reads as the template it stands "
            "in, since the slash judgement stands over "
            "literal text and a hole is code.",
            "the template hole regex residual",
        ),
    ):
        if sentence not in text:
            problems.append(
                "docs/mod-build7.md does not state %s" % label
            )
    if "is struck from this brief as a category error" not in text:
        problems.append(
            "docs/mod-build7.md does not strike the onFailure language"
        )
    if "onFailure block mode" in text or "onFailure: " in text:
        problems.append(
            "docs/mod-build7.md presents onFailure as a mod mechanism"
        )
    return problems


def test_story_problems():
    """Problems with the host side test story."""
    tests = sorted((ROOT / "hooks").glob("*.test.ts"))
    if not tests:
        return ["hooks/ holds no *.test.ts file for claude plugin test"]
    return []


def plugin_copy_problems():
    """Problems with the marketplace entry copy of the mod.

    The recognitio-mod plugin folder ships the mod on its own.
    Its hooks folder must hold exactly the files the hooks
    folder at the root holds, each a byte identical copy of
    the original, and its LICENSE must be a byte identical
    copy of the root LICENSE, so the entry can never install
    a module this gate has not certified or stand in a
    folder under different terms.
    """
    problems = []
    hooks_dir = ROOT / "hooks"
    if not hooks_dir.is_dir():
        return ["hooks/ is missing, so the mod has no original"]
    originals = sorted(
        path.name for path in hooks_dir.iterdir() if path.is_file())
    copies = []
    if MOD_PLUGIN_HOOKS.is_dir():
        copies = sorted(
            path.name for path in MOD_PLUGIN_HOOKS.iterdir()
            if path.is_file())
    if copies != originals:
        problems.append(
            "plugins/recognitio-mod/hooks holds %s and hooks "
            "holds %s, so the marketplace copy of the mod does "
            "not mirror the certified module"
            % (copies, originals))
    for name in sorted(set(originals) & set(copies)):
        if (MOD_PLUGIN_HOOKS / name).read_bytes() != \
                (hooks_dir / name).read_bytes():
            problems.append(
                "plugins/recognitio-mod/hooks/%s differs from "
                "hooks/%s, so the marketplace copy of the mod "
                "has drifted from the certified module"
                % (name, name))
    license_copy = MOD_PLUGIN_DIR / "LICENSE"
    if not license_copy.is_file():
        problems.append(
            "plugins/recognitio-mod/LICENSE is missing, so "
            "the mod plugin folder carries no licence of its "
            "own")
    elif license_copy.read_bytes() != (ROOT / "LICENSE").read_bytes():
        problems.append(
            "plugins/recognitio-mod/LICENSE differs from the "
            "root LICENSE, so the mod plugin folder stands "
            "under different terms")
    return problems


def mod_problems(root=None):
    """Every Build 7 mod problem."""
    problems = []
    path, problem = module_path()
    if problem:
        return [problem]
    problems.extend(module_problems(path))
    problems.extend(brief_problems())
    problems.extend(test_story_problems())
    problems.extend(plugin_copy_problems())
    return problems


def main(argv=None):
    problems = mod_problems()
    if problems:
        for problem in problems:
            print("check_mod: %s" % problem, file=sys.stderr)
        return 1
    print("check_mod: the Build 7 mod contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
