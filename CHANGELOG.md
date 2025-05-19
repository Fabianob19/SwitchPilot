# Changelog

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