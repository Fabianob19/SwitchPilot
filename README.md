# SwitchPilot

Automação de corte de cenas para lives (OBS/vMix), com captura de tela/janela, comparação de imagem rápida (Hist+NCC+LBP) e execução de ações. Interface PyQt5 com tema escuro, título custom e suporte a DPI alto.

> **v1.5.1** - Agora com algoritmo de detecção otimizado! +5% de precisão no NCC, +1% no score final.

## Visão Geral
- **Fontes**: Monitor, Janela (NDI opcional)
- **Detecção**: Ensemble Histogram Correlation + NCC + LBP otimizado, com suavização temporal
  - **Precisão de detecção**: ~95% (score final)
  - **Performance**: ~0.54s por ciclo de detecção
  - **Otimização NCC**: Downscaling inteligente para 128x128 pixels
- **Ações**: OBS (WebSocket 5.x), vMix (API HTTP)
- **UI**: Título custom escuro, menubar integrada, seleção de ROI com prévia nítida
- **Windows**: AppUserModelID, ícone próprio, DPI-aware (Per-Monitor v2)

## Quickstart (Usuário Final)
1. Baixe o ZIP de release e extraia.
2. Abra `SwitchPilot.exe`.
3. Configure OBS/vMix (se usar) nas abas correspondentes.
4. Em Gerenciador de Referências: escolha a fonte (Monitor/Janela) e clique em "Selecionar Região PGM".
5. Adicione imagens de referência e associe ações. Inicie o monitoramento.

Requisitos:
- Windows 10/11
- Para OBS: WebSocket 5.x ativado
- Para vMix: API HTTP ativa
- NDI é opcional

## Desenvolvimento
- Python 3.10+ (recomendado 3.11+)
- Ambiente virtual recomendado

Instalação (dev):
```
python -m venv .venv310
.venv310\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Arquitetura
- Núcleo: `switchpilot/core/` (MainController, MonitorThread)
- Integrações: `switchpilot/integrations/` (OBS, vMix, NDI opcional)
- UI: `switchpilot/ui/` (MainWindow, widgets, temas)

Diagrama (alto nível):
```mermaid
flowchart LR
  A[Captura (Monitor/Janela/NDI)] --> B[Pré-processamento ROI]
  B --> C[Similaridade (Hist + NCC + LBP)]
  C -->|match| D[Decisão temporal (K/M/histerese)]
  D -->|true| E[Executores (OBS/vMix)]
  D -->|false| F[Loop próximo frame]
  subgraph UI
    U1[MainWindow] -- configura --> U2[ReferenceManager]
    U1 -- monitora --> U3[Log]
  end
  U2 -- ROI/source --> A
  E --> U3
```

Detalhes adicionais em `docs/arquitetura.md`.

## Licença
MIT. Veja `LICENSE`.

## Contribuindo
Veja `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md`.

## Segurança
Reporte vulnerabilidades conforme `SECURITY.md`. 