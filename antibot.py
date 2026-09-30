"""anti-bot fetch: TLS/JA3/JA4 + HTTP/2 fingerprint browser asli.

Pakai:
    from antibot import fetch, Session

    r = fetch("https://target.com")
    print(r.status_code, r.text[:200])

    with Session("chrome131") as s:
        s.get("https://site.com/login")      # ambil cookie
        r = s.post("https://site.com/api", json={"a": 1})

Kenapa ini bekerja: server mem-fingerprint koneksi TLS (JA3/JA4), urutan header,
dan fingerprint HTTP/2. curl_cffi memakai BoringSSL + profil browser asli
sehingga ketiganya identik dengan browser sungguhan — bukan cuma ganti User-Agent.

Batas: ini menangani deteksi tingkat jaringan. Challenge yang butuh eksekusi
JavaScript (Turnstile, _abck sensor, captcha gambar) TIDAK bisa dilewati —
untuk itu butuh browser sungguhan (playwright + stealth).
"""
from __future__ import annotations

import time
from typing import Any, Iterable

from curl_cffi import requests as cffi
from curl_cffi.requests import Response, Session as _CffiSession

__all__ = ["fetch", "Session", "PROFILES", "DEFAULT_PROFILE", "browser_of"]

# Profil terkini per keluarga. Ganti angka kalau target menolak versi lama.
PROFILES = {
    "chrome": "chrome131",
    "chrome_new": "chrome146",
    "chrome_android": "chrome131_android",
    "firefox": "firefox133",
    "safari": "safari180",
    "safari_ios": "safari180_ios",
    "edge": "edge101",
    "tor": "tor145",
}
DEFAULT_PROFILE = "chrome"

# Urutan header per keluarga browser (meniru order asli browser).
# Header di luar daftar ditaruh di akhir; ini mencegah kebocoran urutan.
_ORDER = {
    "chrome": [
        "host", "connection", "content-length", "pragma", "cache-control",
        "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform", "upgrade-insecure-requests",
        "user-agent", "accept", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-user",
        "sec-fetch-dest", "accept-encoding", "accept-language", "cookie", "priority",
    ],
    "firefox": [
        "host", "user-agent", "accept", "accept-language", "accept-encoding",
        "connection", "upgrade-insecure-requests", "sec-fetch-dest", "sec-fetch-mode",
        "sec-fetch-site", "sec-fetch-user", "priority", "cookie",
    ],
    "safari": [
        "host", "accept", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest",
        "user-agent", "accept-language", "accept-encoding", "connection", "cookie",
    ],
}

# Header standar yang sering hilang kalau request dibuat manual.
# Kalau request punya lebih sedikit header daripada browser asli, itu sinyal bot.
_DEFAULTS = {
    "chrome": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "accept-encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "priority": "u=0, i",
    },
    "firefox": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "accept-encoding": "gzip, deflate, br",
        "upgrade-insecure-requests": "1",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "priority": "u=0, i",
    },
    "safari": {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "accept-encoding": "gzip, deflate, br",
    },
}


def browser_of(profile: str) -> str:
    """Keluarga browser dari nama profil (chrome131 -> chrome)."""
    p = profile.lower()
    for fam in ("firefox", "safari", "edge", "tor"):
        if p.startswith(fam):
            return "firefox" if fam in ("firefox", "tor") else fam
    return "chrome"


def _prepare_headers(headers: dict, profile: str) -> dict:
    """Tambal header yang kurang, lalu urutkan seperti browser asli."""
    fam = browser_of(profile)
    out = {k: v for k, v in (headers or {}).items()}
    lower = {k.lower() for k in out}
    for k, v in _DEFAULTS.get(fam, _DEFAULTS["chrome"]).items():
        if k not in lower:
            out[k] = v
    order = _ORDER.get(fam, _ORDER["chrome"])
    idx = {h: i for i, h in enumerate(order)}
    return dict(sorted(out.items(), key=lambda kv: idx.get(kv[0].lower(), 999)))


class Session:
    """Sesi persisten: cookie bertahan antar request, seperti browser asli.

    Pakai ini (bukan fetch()) untuk situs yang butuh alur: kunjungi halaman ->
    dapat cookie (termasuk cf_clearance / _abck) -> baru panggil API.

    Bisa dipakai sebagai context manager:
        with Session("chrome131") as s:
            s.get("https://site.com")
    """

    def __init__(self, profile: str = DEFAULT_PROFILE, *, retries: int = 2,
                 retry_wait: float = 1.5, **session_kwargs: Any):
        self.profile = profile
        self.retries = retries
        self.retry_wait = retry_wait
        self._s = _CffiSession(impersonate=profile, **session_kwargs)

    def request(self, method: str, url: str, *, headers: dict | None = None,
                **kw: Any) -> Response:
        kw["headers"] = _prepare_headers(headers or {}, self.profile)
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._s.request(method, url, **kw)
            except Exception as e:  # koneksi putus / timeout / reset
                last = e
                if attempt < self.retries:
                    time.sleep(self.retry_wait * (attempt + 1))
        raise last  # type: ignore[misc]

    def get(self, url: str, **kw: Any) -> Response:
        return self.request("GET", url, **kw)

    def post(self, url: str, **kw: Any) -> Response:
        return self.request("POST", url, **kw)

    def cookies_dict(self) -> dict:
        """Cookie saat ini — berguna untuk dipindah ke tool lain."""
        return self._s.cookies.get_dict()

    def close(self) -> None:
        self._s.close()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def fetch(url: str, *, profile: str = DEFAULT_PROFILE, method: str = "GET",
          headers: dict | None = None, retries: int = 2,
          retry_wait: float = 1.5, **kw: Any) -> Response:
    """Request sekali jalan dengan fingerprint browser. Return Response."""
    with Session(profile, retries=retries, retry_wait=retry_wait) as s:
        return s.request(method, url, headers=headers, **kw)


if __name__ == "__main__":
    # Self-check: pastikan profil valid & header tertata. Tanpa jaringan.
    assert browser_of("chrome131") == "chrome"
    assert browser_of("firefox133") == "firefox"
    assert browser_of("safari180_ios") == "safari"
    h = _prepare_headers({"X-Custom": "1"}, "chrome131")
    keys = [k.lower() for k in h]
    assert "sec-ch-ua" in keys, "header chrome standar harus ditambal"
    assert "x-custom" in keys, "header milik pemanggil harus dipertahankan"
    assert "accept-language" in keys
    # header browser asli harus lebih dulu daripada header custom (anti-kebocoran urutan)
    assert keys.index("accept") < keys.index("x-custom"), "urutan header salah"
    # firefox tidak boleh dapat header sec-ch-ua (khas chrome)
    hf = _prepare_headers({}, "firefox133")
    assert "sec-ch-ua" not in [k.lower() for k in hf]
    assert set(PROFILES) >= {"chrome", "firefox", "safari", "edge"}
    print("selftest OK — profil:", ", ".join(PROFILES.values()))
