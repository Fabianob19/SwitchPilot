# SwitchPilot

Painel de automação para corte de câmeras em transmissões ao vivo, com integração ao vMix e OBS. Interface moderna, responsiva e personalizável.

## Funcionalidades
- Seleção de fonte de captura (monitor, janela; NDI opcional)
- Seleção visual da região do PGM
- Associação de imagens de referência a ações automáticas (corte, overlay, transição, cenas OBS, etc)
- Log detalhado e exportação de configurações
- Temas claros e escuros; título custom escuro no Windows
- Diagnóstico de conexão com vMix e OBS

## Requisitos
- Python 3.10+
- Windows 10/11
- Dependências: ver `requirements.txt`

## Instalação (dev)
1. Crie e ative um ambiente virtual:
   ```
   python -m venv .venv310
   .venv310\Scripts\activate
   ```
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o app:
   ```
   python main.py
   ```

## Release Beta
- Versão atual: `v1.5.0-beta1`
- Para gerar um executável (opcional):
  ```
  pip install pyinstaller
  pyinstaller SwitchPilot.spec
  ```
  O executável será criado em `dist/`.

## Observações
- NDI é opcional (dependência comentada em `requirements.txt`).
- Para vMix, mantenha a API HTTP ativada (porta 8088).
- Para OBS, ative o WebSocket (porta 4455).

## Suporte
Dúvidas, sugestões ou bugs: suporte@seudominio.com

---
© 2024–2025 SwitchPilot. Todos os direitos reservados. 