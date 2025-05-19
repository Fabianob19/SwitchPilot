# SwitchPilot

Painel de automação para corte de câmeras em transmissões ao vivo, com integração ao vMix e OBS. Interface moderna, responsiva e personalizável.

## Funcionalidades
- Seleção de fonte de captura (monitor, janela)
- Seleção visual da região do PGM
- Associação de imagens de referência a ações automáticas (corte, overlay, transição, cenas OBS, etc)
- Log detalhado e exportação de configurações
- Temas claros e escuros
- Diagnóstico de conexão com vMix e OBS

## Requisitos
- Python 3.10+
- Windows 10/11
- Dependências: ver `requirements.txt`

## Instalação
1. Crie e ative um ambiente virtual (recomendado):
   ```
   python -m venv .venv310
   .venv310\Scripts\activate
   ```
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o painel:
   ```
   python -m ui.painel
   ```

## Observações
- O painel não depende mais de NDI/NDIlib.
- Para integração com vMix, mantenha a API HTTP ativada (porta 8088).
- Para integração com OBS, ative o WebSocket (porta 4455).

## Suporte
Dúvidas, sugestões ou bugs: suporte@seudominio.com

---
© 2024 SeuNome. Todos os direitos reservados. 