# Contribuindo para o SwitchPilot

Obrigado por querer contribuir! Este guia ajuda você a propor mudanças produtivamente.

## Como começar
- Dê uma olhada nas issues abertas. Use labels para filtrar (bug, feature, doc, good first issue).
- Para grandes mudanças, abra uma issue de proposta antes de enviar PR.

## Ambiente de desenvolvimento
- Python 3.10+
- `python -m venv .venv310 && .venv310/Scripts/activate`
- `pip install -r requirements.txt`
- `python main.py`

## Padrões de código
- Seguir PEP8 e nomes descritivos (Clean Code).
- Evitar aninhamento profundo; usar early returns.
- Adicionar logs úteis; evitar ruído.
- Não capturar exceções sem tratar.

## Commits e PRs
- Commits claros, no imperativo: `feat(ui): ...`, `fix(core): ...`, `docs: ...`.
- Um PR por tópico. Inclua descrição, screenshots se for UI.
- Adicione/atualize documentação quando necessário.

## Testes manuais
- Validar: seleção de ROI, detecção básica com uma referência, execução de uma ação (OBS/vMix simulado).

## Segurança
- Não inclua credenciais. Reporte vulnerabilidades em `SECURITY.md`.

## Licença
- Ao contribuir, você concorda com a licença MIT do projeto. 