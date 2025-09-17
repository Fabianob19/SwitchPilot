# Changelog

## v1.5.0-beta1 (2025-09-17)
- Primeira versão beta oficial.
- Título personalizado escuro com botões (min/max/fechar) e menubar separada.
- Ícone e logo novos (alta nitidez em 16–24 px), AppUserModelID no Windows.
- Melhorias no seletor de fonte/ROI: listas com Atualizar, preview com escala 1:1 quando possível e downscale nítido.
- App DPI-aware (Per-Monitor v2); coordenadas corretas em 125%/150% de escala.
- Sistema de similaridade aprimorado (Hist+NCC+LBP) com suavização temporal.
- vMix/OBS: mapeamentos de ações alinhados e conexão OBS sob demanda.
- Logs otimizados na UI (debounce e limite de linhas).
- NDI opcional na UI; dependência comentada em requirements.

## v1.1.0 (limpeza final)
- Removido todo o suporte, dependências e arquivos relacionados ao NDI/NDIlib
- Limpeza de arquivos de teste, binários e pastas antigas
- requirements.txt gerado apenas com dependências realmente utilizadas
- Pronto para distribuição e manutenção

Todas as mudanças notáveis deste projeto serão documentadas aqui.

## [1.1.0] - 2024-06-XX
### Adicionado
- Novo tema visual "Blue Steel" disponível na seleção de temas do painel.

### Alterado
- Nenhuma alteração adicional nesta versão.

### Corrigido
- Nenhuma correção nesta versão.

## [1.0.0] - 2025-05-01
### Adicionado
- Primeira versão estável do SwitchPilot.
- Interface moderna em PyQt5, responsiva e com três temas (Dark Profundo, Light, Cinza Suave).
- Seleção visual de região do PGM (monitor ou janela).
- Integração com vMix (API), OBS (WebSocket) e NDI (opcional).
- Adição de imagens de referência e associação de múltiplas ações (cut, overlay, transição, shortcut, OBS, etc).
- Monitoramento automático da região, com modo simulação.
- Log detalhado, exportação/importação de configurações e exportação de log.
- Diagnóstico de conexão com vMix.
- Badge de quantidade de ações por referência.
- Lista de referências com miniatura, nome truncado e badge, tooltip detalhado.
- Botões padronizados, acessíveis e responsivos.
- Estrutura modular e código documentado.

### Corrigido
- Sobreposição de texto e badge na lista de referências.
- Problemas de layout e alinhamento dos botões.
- Remoção de estilos antigos e padronização visual.
- Limpeza de arquivos e scripts obsoletos.

### Observações
- O sistema funciona sem NDIlib instalado, mas as funções NDI ficam desabilitadas.
- Pronto para testes, demonstração e expansão futura. 