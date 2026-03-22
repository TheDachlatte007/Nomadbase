from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_PATHS = [
    "/",
    "/api/health",
    "/api/map/places?limit=1",
    "/api/trips/",
    "/api/saves/",
    "/api/docs",
]


@dataclass
class CheckResult:
    path: str
    ok: bool
    status: int | None
    note: str


def fetch(base_url: str, path: str) -> CheckResult:
    url = f"{base_url.rstrip('/')}{path}"
    request = Request(url, headers={"User-Agent": "NomadbaseSmokeCheck/1.0"})
    try:
        with urlopen(request, timeout=12) as response:
            status = response.getcode()
            body = response.read(400).decode("utf-8", errors="replace")
            note = body.strip().replace("\n", " ")[:140]
            return CheckResult(path=path, ok=200 <= status < 400, status=status, note=note)
    except HTTPError as exc:
        body = exc.read(300).decode("utf-8", errors="replace")
        return CheckResult(
            path=path,
            ok=False,
            status=exc.code,
            note=body.strip().replace("\n", " ")[:140] or "HTTP error",
        )
    except URLError as exc:
        return CheckResult(path=path, ok=False, status=None, note=str(exc.reason))


def summarize(results: Iterable[CheckResult]) -> int:
    failed = False
    for result in results:
        prefix = "PASS" if result.ok else "FAIL"
        status = result.status if result.status is not None else "-"
        print(f"[{prefix}] {result.path} ({status})")
        if result.note:
            print(f"       {result.note}")
        failed = failed or not result.ok
    return 1 if failed else 0


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    paths = sys.argv[2:] or DEFAULT_PATHS
    print(json.dumps({"base_url": base_url, "paths": paths}, indent=2))
    results = [fetch(base_url, path) for path in paths]
    return summarize(results)


if __name__ == "__main__":
    raise SystemExit(main())
