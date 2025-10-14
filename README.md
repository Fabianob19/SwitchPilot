# SwitchPilot

AutomaÃ§Ã£o de corte de cenas para lives (OBS/vMix), com captura de tela/janela, comparaÃ§Ã£o de imagem rÃ¡pida (Hist+NCC+LBP) e execuÃ§Ã£o de aÃ§Ãµes. Interface PyQt5 com tema escuro, tÃ­tulo custom e suporte a DPI alto.

> **v1.5.2** - Agora com algoritmo de detecÃ§Ã£o otimizado! +5% de precisÃ£o no NCC, +1% no score final.

## ðŸš€ **Download**

[![Download](https://img.shields.io/badge/Download-SwitchPilot%20v1.5.2-blue?style=for-the-badge&logo=windows)](https://github.com/Fabianob19/SwitchPilot/releases/latest)

**ðŸŽ¯ Recomendado**: [Instalador Windows](https://github.com/Fabianob19/SwitchPilot/releases/latest) (`SwitchPilot_v1.5.2_Setup.exe` - 65MB)  
**ðŸ“ Alternativa**: [ExecutÃ¡vel Direto](https://github.com/Fabianob19/SwitchPilot/releases/latest) (`SwitchPilot.exe` - 95MB)

## âœ¨ **Novidades v1.5.2**

### ðŸŽ¯ **Instalador Profissional**
- **Instalador Windows**: Interface em PortuguÃªs com instalaÃ§Ã£o automÃ¡tica
- **Ãcones Corrigidos**: Atalhos no Menu Iniciar e Ãrea de Trabalho funcionando
- **DesinstalaÃ§Ã£o FÃ¡cil**: Registrado em "Programas e Recursos"
- **Tamanho Otimizado**: 65MB vs 95MB do executÃ¡vel direto

### âš¡ **Melhorias de DetecÃ§Ã£o**
- **NCC Otimizado**: +5% de precisÃ£o (77% â†’ 82%)
- **Score Final**: +1% (94.3% â†’ 95.3%)
- **Downscaling Inteligente**: Processamento mais robusto com 128x128 pixels
- **Ensemble Rebalanceado**: Histograma (40%), NCC (20%), LBP (40%)

## VisÃ£o Geral
- **Fontes**: Monitor, Janela (NDI opcional)
- **DetecÃ§Ã£o**: Ensemble Histogram Correlation + NCC + LBP otimizado, com suavizaÃ§Ã£o temporal
  - **PrecisÃ£o de detecÃ§Ã£o**: ~95% (score final)
  - **Performance**: ~0.54s por ciclo de detecÃ§Ã£o
  - **OtimizaÃ§Ã£o NCC**: Downscaling inteligente para 128x128 pixels
- **AÃ§Ãµes**: OBS (WebSocket 5.x), vMix (API HTTP)
- **UI**: TÃ­tulo custom escuro, menubar integrada, seleÃ§Ã£o de ROI com prÃ©via nÃ­tida
- **Windows**: AppUserModelID, Ã­cone prÃ³prio, DPI-aware (Per-Monitor v2)

## Quickstart (UsuÃ¡rio Final)

### ðŸŽ¯ **InstalaÃ§Ã£o Recomendada (Instalador)**
1. Baixe `SwitchPilot_v1.5.2_Setup.exe` da [pÃ¡gina de releases](https://github.com/Fabianob19/SwitchPilot/releases)
2. Execute o instalador e siga as instruÃ§Ãµes
3. O SwitchPilot serÃ¡ instalado em `C:\Program Files\SwitchPilot\`
4. Atalhos serÃ£o criados no Menu Iniciar e Ãrea de Trabalho
5. Execute o SwitchPilot pelo Menu Iniciar ou atalho

### ðŸ“ **InstalaÃ§Ã£o Alternativa (ExecutÃ¡vel Direto)**
1. Baixe `SwitchPilot.exe` da [pÃ¡gina de releases](https://github.com/Fabianob19/SwitchPilot/releases)
2. Extraia em uma pasta
3. Execute `SwitchPilot.exe`

### âš™ï¸ **ConfiguraÃ§Ã£o Inicial**
1. Configure OBS/vMix (se usar) nas abas correspondentes
2. Em **Gerenciador de ReferÃªncias**: escolha a fonte (Monitor/Janela) e clique em "Selecionar RegiÃ£o PGM"
3. Adicione imagens de referÃªncia e associe aÃ§Ãµes
4. Inicie o monitoramento

### ðŸ“‹ **Requisitos**
- **Sistema**: Windows 10/11 (64-bit)
- **MemÃ³ria**: 4GB mÃ­nimo, 8GB recomendado
- **EspaÃ§o**: 200MB livres
- **OBS**: WebSocket 5.x ativado
- **vMix**: API HTTP ativa
- **NDI**: Opcional

## Desenvolvimento
- Python 3.10+ (recomendado 3.11+)
- Ambiente virtual recomendado

InstalaÃ§Ã£o (dev):
```
python -m venv .venv310
.venv310\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Arquitetura
- NÃºcleo: `switchpilot/core/` (MainController, MonitorThread)
- IntegraÃ§Ãµes: `switchpilot/integrations/` (OBS, vMix, NDI opcional)
- UI: `switchpilot/ui/` (MainWindow, widgets, temas)

Diagrama (alto nÃ­vel):
```mermaid
flowchart LR
  A[Captura Monitor Janela NDI] --> B[Pre processamento ROI]
  B --> C[Similaridade Hist NCC LBP]
  C -->|match| D[Decisao temporal]
  D -->|true| E[Executores OBS vMix]
  D -->|false| F[Loop proximo frame]
  subgraph UI
    U1[MainWindow]
    U2[ReferenceManager]
    U3[Log]
    U1 --> U2
    U1 --> U3
  end
  U2 --> A
  E --> U3
```

Detalhes adicionais em `docs/arquitetura.md`.

## LicenÃ§a
MIT. Veja `LICENSE`.

## Contribuindo
Veja `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md`.

## SeguranÃ§a
Reporte vulnerabilidades conforme `SECURITY.md`. 
