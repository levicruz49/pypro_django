"""Grava o status `codex-review` no HEAD do PR, a partir do CI.

O hook `bloquear-merge-sem-babysit.sh` só barra o `gh pr merge` da sessão. PR
aberto sem babysit-pr ficava sem pedido de revisão e nada no GitHub mostrava
(lume #11 e #12, 2026-10-24). Este script deixa o HEAD vermelho até o Codex
revisar aquele commit.

A decisão é a mesma do hook: importa `codex_revisou_head.py`, que o
`instalar-portao-codex.sh` copia ao lado deste arquivo. Stdlib só: o runner
do VPS é o usuário `ghrunner`, sem `gh` nem pip.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

from codex_revisou_head import decidir

CONTEXTO = "codex-review"
# Mesma consulta do hook de merge, sem o corpo do PR.
CONSULTA = (
    "query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo)"
    "{pullRequest(number:$pr){headRefOid reviews(last:100){nodes{author{__typename login}"
    " commit{oid}}} comments(last:100){nodes{author{__typename login} body}}}}}"
)
MSG_ERRO = "Não consegui ler a revisão do Codex. Portão fechado."


class PortaoFechado(Exception):
    """Consulta falhou: o status fica vermelho e o job falha."""


def numero_do_pr(evento: dict) -> int | None:
    if "pull_request" in evento:
        return evento["pull_request"]["number"]
    issue = evento.get("issue") or {}
    return issue["number"] if "pull_request" in issue else None


def status_do_commit(decisao: str, head: str) -> tuple[str, str]:
    if decisao == "ok":
        return "success", f"Codex revisou {head[:7]}."
    if decisao.startswith("pendente:"):
        curto = decisao.removeprefix("pendente:")
        return (
            "failure",
            f"Sem revisão do Codex no {curto}. Rode babysit-pr (pedir-codex-review.sh).",
        )
    return "failure", MSG_ERRO


def _gravar(requisitar, repo: str, sha: str, estado: str, descricao: str) -> None:
    corpo = {"state": estado, "context": CONTEXTO, "description": descricao}
    requisitar("POST", f"/repos/{repo}/statuses/{sha}", corpo)


def publicar(evento: dict, repo: str, requisitar) -> None:
    """`requisitar(metodo, caminho, corpo) -> dict` fala com a API do GitHub."""
    numero = numero_do_pr(evento)
    if numero is None:
        return
    dono, nome = repo.split("/", 1)
    variaveis = {"owner": dono, "repo": nome, "pr": numero}
    sha_do_evento = ((evento.get("pull_request") or {}).get("head") or {}).get("sha")
    try:
        resposta = requisitar("POST", "/graphql", {"query": CONSULTA, "variables": variaveis})
        pr = resposta["data"]["repository"]["pullRequest"]
        # Logo após o push, o GraphQL pode ainda devolver o head anterior, já
        # revisado: gravaria success nele e o commit novo ficaria sem status.
        if sha_do_evento:
            pr["headRefOid"] = sha_do_evento
        head = pr["headRefOid"]
    except (OSError, ValueError, KeyError, TypeError) as erro:
        if sha_do_evento:
            _gravar(requisitar, repo, sha_do_evento, "failure", MSG_ERRO)
        raise PortaoFechado(MSG_ERRO) from erro
    _gravar(requisitar, repo, head, *status_do_commit(decidir(resposta), head))


def _requisitar_github(metodo: str, caminho: str, corpo: dict) -> dict:
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    # Só https: `file://` ou esquema próprio faria o urllib ler arquivo local
    # (ruff S310, apontado no iot_app em 2026-10-28).
    if not api.startswith("https://"):
        raise ValueError(f"GITHUB_API_URL precisa ser https: {api}")
    pedido = urllib.request.Request(  # noqa: S310 - esquema conferido acima
        api + caminho,
        data=json.dumps(corpo).encode(),
        method=metodo,
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:  # noqa: S310
        return json.load(resposta)


def main() -> None:
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as arquivo:
        evento = json.load(arquivo)
    try:
        publicar(evento, os.environ["GITHUB_REPOSITORY"], _requisitar_github)
    except PortaoFechado as erro:
        print(f"::error::{erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()
