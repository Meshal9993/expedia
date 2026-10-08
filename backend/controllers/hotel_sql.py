"""Restricted SQL grammar and authorization policy; SQLite I/O stays in DatabaseController."""

import re

from backend.models.hotel_chat import SqlProposal


HOTEL_COLUMNS = {
    "saved_hotels": {"hotel_id", "name", "address", "latitude", "longitude"},
    "saved_hotel_locations": {"hotel_id", "requested_zip", "resolved_postcode", "city",
                              "state", "latitude", "longitude"},
    "demo_hotel_nights": {"hotel_id", "stay_date", "nightly_rate_cents", "rooms_available"},
}
SAFE_FUNCTIONS = {"like", "lower", "upper", "coalesce"}
ROW_LIMIT = 50
OUTPUT_LIMIT = 32768
QUERY_SECONDS = 1.0
FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "create", "replace", "attach",
    "detach", "pragma", "vacuum", "begin", "commit", "rollback", "savepoint",
    "release", "end", "with", "union", "intersect", "except", "group", "having",
    "offset", "returning", "window", "over", "filter", "values", "explain", "cross", "natural", "right", "full",
}
TOKEN = re.compile(r"\s+|[A-Za-z_][A-Za-z0-9_]*|[0-9]+|<=|>=|<>|!=|[.,()?;=<>]")
PROJECTION = re.compile(r"(?:[a-z_][a-z0-9_]*\s*\.\s*)?([a-z_][a-z0-9_]*)(?:\s+as\s+([a-z_][a-z0-9_]*))?$")


class RejectedHotelSql(Exception):
    """The model query is outside the approved read-only grammar."""


class HotelRetrievalError(Exception):
    """A validated read could not complete; no raw SQLite text is exposed."""

    def __init__(self, executed_sql=None):
        self.executed_sql = executed_sql


def validate_joins(tokens: list[str]) -> None:
    """Only real hotel_id relationships may join the three physical tables.

    JOIN conditions are an ID equality followed by optional bound conditions on
    the joined table. This prevents CROSS/OR joins from misattributing nightly data.
    """
    start = tokens.index("from") + 1
    end = next((i for i in range(start, len(tokens)) if tokens[i] in {"where", "order", "limit"}), len(tokens))
    clause = tokens[start:end]
    aliases = {}
    used_tables = set()
    stop = {"join", "inner", "left", "outer", "on"}

    def table_at(position):
        if position >= len(clause) or clause[position] not in HOTEL_COLUMNS:
            raise RejectedHotelSql
        table = clause[position]
        position += 1
        alias = table
        if position < len(clause) and clause[position] == "as":
            position += 1
            if position >= len(clause):
                raise RejectedHotelSql
            alias = clause[position]
            position += 1
        elif position < len(clause) and clause[position] not in stop:
            alias = clause[position]
            position += 1
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", alias) or alias in aliases or table in used_tables:
            raise RejectedHotelSql
        aliases[alias] = table
        used_tables.add(table)
        return alias, position

    _, position = table_at(0)
    while position < len(clause):
        if clause[position] in {"left", "inner"}:
            position += 1
            if position < len(clause) and clause[position] == "outer":
                position += 1
        if position >= len(clause) or clause[position] != "join":
            raise RejectedHotelSql
        joined, position = table_at(position + 1)
        if position >= len(clause) or clause[position] != "on":
            raise RejectedHotelSql
        position += 1
        condition = clause[position:position + 7]
        if (len(condition) != 7 or condition[1:3] != [".", "hotel_id"]
                or condition[3] != "=" or condition[5:] != [".", "hotel_id"]):
            raise RejectedHotelSql
        first, second = condition[0], condition[4]
        if (first == second or joined not in (first, second) or first not in aliases or second not in aliases
                or "saved_hotels" not in (aliases[first], aliases[second])):
            raise RejectedHotelSql
        position += 7
        while position < len(clause) and clause[position] == "and":
            condition = clause[position:position + 6]
            if (len(condition) != 6 or condition[1] != joined or condition[2] != "."
                    or condition[3] not in HOTEL_COLUMNS[aliases[joined]]
                    or condition[4] not in {"=", "!=", "<>", "<", ">", "<=", ">="} or condition[5] != "?"):
                raise RejectedHotelSql
            position += 6


def validate_hotel_sql(proposal: SqlProposal) -> str:
    """Allow a single raw-column SELECT; require placeholders for filter values.

    No literal strings, comments, computed projections, subqueries, or aggregates.
    Totals/coverage are computed from dated evidence by the application instead.
    SQLite's authorizer additionally validates actual resolved tables/columns.
    """
    sql = proposal.sql.strip()
    tokens = []
    offset = 0
    while offset < len(sql):
        match = TOKEN.match(sql, offset)
        if not match:
            raise RejectedHotelSql
        token = match.group().strip().lower()
        if token:
            tokens.append(token)
        offset = match.end()
    if tokens and tokens[-1] == ";":
        tokens.pop()
        sql = sql[:-1].rstrip()
    if (not tokens or tokens[0] != "select" or tokens.count("select") != 1
            or ";" in tokens or any(token in FORBIDDEN for token in tokens)
            or tokens.count("?") != len(proposal.parameters)):
        raise RejectedHotelSql
    # Numeric constants are permitted only for a terminal LIMIT. All conditions bind values.
    for i, token in enumerate(tokens):
        if token.isdigit() and not (i == len(tokens) - 1 and tokens[i - 1] == "limit"
                                   and 1 <= int(token) <= ROW_LIMIT):
            raise RejectedHotelSql
    if "limit" in tokens and (tokens.count("limit") != 1 or tokens[-2] != "limit"
                              or not tokens[-1].isdigit()):
        raise RejectedHotelSql
    prefix, separator, _ = re.split(r"\b(from)\b", sql, maxsplit=1, flags=re.I) if re.search(r"\bfrom\b", sql, re.I) else ("", "", "")
    if not separator:
        raise RejectedHotelSql
    validate_joins(tokens)
    projection = re.sub(r"^select\s+(?:distinct\s+)?", "", prefix.strip(), flags=re.I)
    fields = []
    allowed_columns = set().union(*HOTEL_COLUMNS.values())
    for field in projection.split(","):
        match = PROJECTION.fullmatch(field.strip().lower())
        if not match or match[1] not in allowed_columns or (match[2] and match[2] != match[1]):
            raise RejectedHotelSql
        fields.append(match[1])
    if len(fields) != len(set(fields)):
        raise RejectedHotelSql
    if "hotel_id" not in fields:
        raise RejectedHotelSql
    if proposal.stay and not {"hotel_id", "stay_date", "nightly_rate_cents", "rooms_available"}.issubset(fields):
        raise RejectedHotelSql
    # ZIP comparisons retain their types, including leading zeros. Inspect the
    # immediate operand, not an adjacent AND condition belonging to another value.
    for index, position in enumerate(i for i, token in enumerate(tokens) if token == "?"):
        parameter = proposal.parameters[index]
        left = tokens[max(0, position - 3):position]
        right = tokens[position + 1:position + 5]
        zip_columns = {"requested_zip", "resolved_postcode"}
        comparison = {"=", "!=", "<>", "<", ">", "<=", ">="}
        zip_operand = (len(left) >= 2 and left[-2] in zip_columns and left[-1] in comparison
                       or len(right) >= 2 and right[0] in comparison and right[1] in zip_columns
                       or len(right) >= 4 and right[0] in comparison and right[2] == "." and right[3] in zip_columns)
        if zip_operand:
            if not isinstance(parameter, str) or not re.fullmatch(r"[0-9]{5}", parameter):
                raise RejectedHotelSql
    return sql
