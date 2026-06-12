"""
Knowledge similarity primitives.

Implements three similarity functions used by the indexer / search engine:

- `cosine_similarity` — vector-based, works on dicts of token->weight.
- `jaccard_similarity` — set-based on tokens.
- `pattern_similarity` — heuristic for shared structural patterns.
- `hybrid_similarity` — weighted blend of the three.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Union


def _tokenize(text: str) -> List[str]:
    """Lowercase, split on whitespace and punctuation, drop empties."""
    if not text:
        return []
    out: List[str] = []
    cur: List[str] = []
    for ch in text.lower():
        if ch.isalnum() or ch == "_":
            cur.append(ch)
        else:
            if cur:
                out.append("".join(cur))
                cur = []
    if cur:
        out.append("".join(cur))
    return out


def _tfidf_vector(
    tokens: Sequence[str],
    idf: Dict[str, float] | None = None,
) -> Dict[str, float]:
    """Build a simple TF-IDF vector (or TF when idf is None)."""
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = float(len(tokens))
    vec: Dict[str, float] = {}
    for tok, c in counts.items():
        tf = c / total
        if idf is not None and tok in idf:
            vec[tok] = tf * idf[tok]
        else:
            vec[tok] = tf
    return vec


def _as_iter(value: Union[str, Iterable[str]]) -> List[str]:
    """Normalize inputs to a list of strings."""
    if isinstance(value, str):
        return _tokenize(value)
    try:
        return [str(v) for v in value]
    except TypeError:
        return [str(value)]


def _tokenize_text(t: str) -> str:
    """Normalize a single text token."""
    return str(t).strip().lower()


def _expand(tokens: Iterable[str]) -> set:
    """Expand tokens so that 'monster_rat' becomes {'monster', 'rat'}."""
    out: set = set()
    for tok in tokens:
        if not tok:
            continue
        t = tok.strip().lower()
        if not t:
            continue
        out.add(t)
        if "_" in t:
            for part in t.split("_"):
                if part:
                    out.add(part)
    return out


def _loose_eq(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return False
    return str(a).strip().lower() == str(b).strip().lower()


def _as_number(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    if isinstance(v, (list, tuple)) and v:
        return _as_number(v[0])
    return None


def cosine_similarity(
    a: Union[Dict[str, float], str],
    b: Union[Dict[str, float], str],
    idf: Dict[str, float] | None = None,
) -> float:
    """
    Cosine similarity in [0, 1] between two vector dicts or text strings.

    If a string is passed, it is tokenized on whitespace/punctuation and
    converted to a TF (or TF-IDF if `idf` is given) vector.
    """
    if isinstance(a, str):
        a = _tfidf_vector(_tokenize(a), idf=idf)
    if isinstance(b, str):
        b = _tfidf_vector(_tokenize(b), idf=idf)
    if not a or not b:
        return 0.0
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    sim = dot / (na * nb)
    return max(0.0, min(1.0, sim))


def jaccard_similarity(
    a: Union[Iterable[str], str],
    b: Union[Iterable[str], str],
) -> float:
    """Jaccard similarity in [0, 1] between token iterables / strings."""
    sa = _expand(_as_iter(a))
    sb = _expand(_as_iter(b))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    if not union:
        return 0.0
    return len(inter) / len(union)


def pattern_similarity(
    a_attrs: Dict[str, Any] | None,
    b_attrs: Dict[str, Any] | None,
) -> float:
    """
    Heuristic structural similarity in [0, 1].

    Compares categorical attributes that hint at design patterns:
      - shape (circular, rectangular, irregular)
      - route (linear, circular, branching)
      - layout (open, dense, maze)
      - arena_type (throne, pit, coliseum)
      - theme / style / difficulty
    And continuous attributes (size, spawns, etc.) where closer is better.
    """
    a_attrs = a_attrs or {}
    b_attrs = b_attrs or {}
    cat_keys = (
        "shape",
        "route",
        "layout",
        "arena_type",
        "theme",
        "difficulty",
        "style",
    )
    matches = 0
    total = 0
    for k in cat_keys:
        a = a_attrs.get(k)
        b = b_attrs.get(k)
        if a is None and b is None:
            continue
        total += 1
        if _loose_eq(a, b):
            matches += 1
    cont_matches = 0.0
    cont_total = 0
    for k in (
        "size",
        "spawns",
        "escape_routes",
        "spawn_density",
        "monsters",
        "tile_count",
    ):
        a = _as_number(a_attrs.get(k))
        b = _as_number(b_attrs.get(k))
        if a is None or b is None:
            continue
        cont_total += 1
        m = max(a, b)
        if m <= 0:
            cont_matches += 1.0
        else:
            d = abs(a - b) / m
            cont_matches += max(0.0, 1.0 - d)
    score = 0.0
    if total:
        score += 0.7 * (matches / total)
    if cont_total:
        score += 0.3 * (cont_matches / cont_total)
    return max(0.0, min(1.0, score))


def hybrid_similarity(
    a_text: str,
    b_text: str,
    a_attrs: Dict[str, Any] | None = None,
    b_attrs: Dict[str, Any] | None = None,
    *,
    idf: Dict[str, float] | None = None,
    weight_cosine: float = 0.4,
    weight_jaccard: float = 0.3,
    weight_pattern: float = 0.3,
) -> float:
    """
    Weighted blend of cosine, jaccard and pattern similarity.

    Returns a value in [0, 1].
    """
    c = cosine_similarity(a_text, b_text, idf=idf)
    j = jaccard_similarity(a_text, b_text)
    p = pattern_similarity(a_attrs, b_attrs)
    total = weight_cosine + weight_jaccard + weight_pattern
    if total <= 0:
        return 0.0
    score = (c * weight_cosine + j * weight_jaccard + p * weight_pattern) / total
    return max(0.0, min(1.0, score))


def build_idf(corpus: Iterable[str]) -> Dict[str, float]:
    """
    Build an IDF dictionary from a corpus of documents.

    IDF(t) = log((N + 1) / (df(t) + 1)) + 1
    """
    docs = [c for c in corpus if c]
    n = len(docs)
    if n == 0:
        return {}
    df: Counter = Counter()
    for d in docs:
        for tok in set(_tokenize(d)):
            df[tok] += 1
    idf: Dict[str, float] = {}
    for tok, dfreq in df.items():
        idf[tok] = math.log((n + 1.0) / (dfreq + 1.0)) + 1.0
    return idf
