"""Decide se o Codex revisou o commit do HEAD de um PR.

Lê do stdin a resposta GraphQL de `bloquear-merge-sem-babysit.sh` e imprime
`ok`, `pendente:<sha7>` ou `erro`. Fail-closed: resposta ilegível vira `erro`,
nunca `ok`, porque este é um portão de merge.

Vale como revisão do HEAD: um review do bot cujo commit é o HEAD, ou um
comentário-recibo do bot cujo "Reviewed commit" é prefixo do HEAD. O Codex
responde por recibo quando não acha problema (formato visto no PR #14 do
Agents-config em 2026-10-22). Sha solto no texto não vale: o bot também
ecoa sha em mensagem de erro ou de limite.
"""

import json
import re
import sys

BOTS_CODEX = {"chatgpt-codex-connector", "chatgpt-codex-connector[bot]"}
MARCA_RECIBO = "<!-- codex-review-receipt:v1 -->"
COMMIT_DO_RECIBO = re.compile(r"\*\*Reviewed commit:\*\* `([0-9a-f]{7,40})`")


def _recibo_do_head(corpo: str, head: str) -> bool:
    if MARCA_RECIBO not in corpo:
        return False
    achado = COMMIT_DO_RECIBO.search(corpo)
    return bool(achado) and head.startswith(achado.group(1))


def _do_codex(no: dict) -> bool:
    # Login sozinho não basta: uma conta comum com o mesmo nome abriria o portão.
    autor = no.get("author") or {}
    return autor.get("__typename") == "Bot" and autor.get("login") in BOTS_CODEX


def decidir(resposta: dict) -> str:
    """Devolve `ok`, `pendente:<sha7>` ou `erro`."""
    try:
        pr = resposta["data"]["repository"]["pullRequest"]
        head = pr["headRefOid"]
        reviews = pr["reviews"]["nodes"]
        comentarios = pr["comments"]["nodes"]
    except (KeyError, TypeError):
        return "erro"
    curto = head[:7]
    for review in reviews:
        if _do_codex(review) and (review.get("commit") or {}).get("oid") == head:
            return "ok"
    for comentario in comentarios:
        if _do_codex(comentario) and _recibo_do_head(comentario.get("body") or "", head):
            return "ok"
    return f"pendente:{curto}"


def main() -> None:
    try:
        resposta = json.load(sys.stdin)
    except ValueError:
        print("erro")
        return
    print(decidir(resposta))


if __name__ == "__main__":
    main()
