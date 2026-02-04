# Arquitetura do SwitchPilot

Este documento descreve a arquitetura do SwitchPilot, seus componentes principais, o fluxo de dados e pontos de extensão.

## Visão de Alto Nível

```mermaid
flowchart LR
  cap[Captura (Monitor/Janela/NDI)] --> roi[Pré-processamento ROI]
  roi --> sim[Similaridade: Hist + NCC + LBP]
  sim --> dec[Decisão temporal (K confirmações / M limpeza / Histerese)]
  dec -->|match| exec[Executores]
  dec -->|nomatch| loop[Próximo frame]
  subgraph Integradores
    obs[OBSController]
    vmix[VMixController]
    ndi[NDIController (opcional)]
  end
  exec --> obs
  exec --> vmix
  cap --> ndi
  subgraph UI
    mw[MainWindow]
    ref[ReferenceManagerWidget]
    mon[MonitoringControlWidget]
  end
  mw --> ref
  mw --> mon
  ref --> cap
```

## Componentes

- `MainController`: orquestra a UI, referências e integradores (OBS/vMix). Mantém estado global e responde a eventos da UI.
- `MonitorThread`: laço de monitoramento que captura frames, recorta ROI e calcula similaridade.
- `OBSController`/`VMixController`: executores de ações (habilitar fonte, trocar cena, transições, overlays etc.).
- `ReferenceManagerWidget`: gerencia fontes (monitor/janela/NDI), seleção de ROI, e referências (imagens + ações).
- `MonitoringControlWidget`: inicia/para o monitoramento e exibe logs.

## Detecção de Similaridade

### Métricas (v1.5.1 - Otimizado)

- **Histograma** (correlação, 1 canal, 256 bins)
  - Peso: 40% (otimizado de 20%)
  - Precisão típica: ~99-100%
  
- **NCC** (TM_CCOEFF_NORMED) para robustez a ganho/offset
  - Peso: 20% (otimizado de 50%)
  - Precisão típica: ~82% (melhorado de 77%)
  - **Otimização v1.5.1**: Downscaling inteligente para 128x128 pixels com INTER_AREA
  - Benefícios: +5% precisão, processamento mais rápido, maior robustez a ruídos
  
- **LBP** (textura) para padrões granulares
  - Peso: 40% (otimizado de 30%)
  - Precisão típica: ~97%

### Ensemble e Performance

- **Fórmula**: `S = 0.4*Hist + 0.2*NCC + 0.4*LBP`
- **Score Final Típico**: ~95% (melhorado de 94.3%)
- **Tempo de Processamento**: ~0.54s por ciclo
- **Suavização temporal**: `K` quadros para confirmar, `M` para limpar, histerese de thresholds

## Coordenadas e DPI

- O app é DPI-aware (Per-Monitor v2). Coordenadas de ROI são calculadas em pixels reais e remapeadas quando a pré-visualização é redimensionada.

## Fluxo de Monitoramento

```mermaid
sequenceDiagram
  participant UI
  participant MC as MainController
  participant MT as MonitorThread
  participant CAP as Captura
  participant CMP as Comparador
  participant EX as Executores

  UI->>MC: Iniciar monitoramento (fonte, ROI, refs)
  MC->>MT: start(fonte, ROI, refs)
  loop a cada intervalo
    MT->>CAP: capturar_frame()
    CAP-->>MT: frame
    MT->>MT: recortar ROI; downscale se necessário
    MT->>CMP: calcular S(Hist,NCC,LBP)
    CMP-->>MT: S
    MT->>MT: aplicar K/M/histerese
    alt match confirmado
      MT->>EX: executar ação (OBS/vMix)
      EX-->>MT: ok
    else
      MT->>MT: continuar
    end
  end
```

## Extensibilidade

- Novas fontes: implementar provedor com `capturar_frame()` e registrar em `ReferenceManagerWidget`.
- Novas ações: adicionar no `MainController._execute_action` e expor na UI.
- Novas métricas: implementar função de score e combinar no ensemble.

## Erros e Logs

- Logs detalhados no painel de Log com limite de linhas e debounce.
- Erros de conexão OBS/vMix são tratados com reconexão sob demanda.

## Build e Distribuição

- PyInstaller via `SwitchPilot.spec`.
- Artefatos: `dist/SwitchPilot.exe` e pacote limpo em `release_clean/`. 