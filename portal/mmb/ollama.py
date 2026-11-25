"""Ollama-compatible JSON inference transport with a configured endpoint."""
import json
import urllib.request
from urllib.parse import urlsplit

from .storage import encode

LOCAL_CHAT = "http://127.0.0.1:11434/api/chat"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def service_url(url):
    parsed = urlsplit(url)
    allowed = parsed.scheme == "https" or (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    )
    if not (allowed and parsed.hostname and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment):
        raise ValueError("请配置本机 HTTP 或可信 HTTPS 服务地址。")
    return url


def chat(model, messages, timeout, url=LOCAL_CHAT, token=""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        service_url(url), headers=headers, data=encode({
            "model": model, "stream": False, "format": "json",
            "options": {"temperature": 0, "seed": 7}, "messages": messages,
        }).encode("utf-8"),
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(512 * 1024 + 1)
    if len(raw) > 512 * 1024:
        raise ValueError("Model response exceeded the size limit")
    envelope = json.loads(raw)
    answer = json.loads(envelope["message"]["content"])
    if not isinstance(answer, dict):
        raise ValueError("Model response must be a JSON object")
    return envelope, answer
