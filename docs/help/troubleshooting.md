# Solução de Problemas (Troubleshooting)

### 🔴 Programa não abre
1.  **Requisitos**: Windows 10/11 64-bit, 4GB RAM.
2.  **Antivírus**: Pode estar bloqueando. Adicione exceção para a pasta do SwitchPilot no Windows Defender.
3.  **Admin**: Tente clicar com botão direito e "Executar como administrador".
4.  **Reinstalar**: Baixe a versão mais recente e reinstale.

### 🔴 Erro ao capturar tela preta
1.  **Execute como Administrador**: Necessário para capturar alguns jogos ou apps protegidos.
2.  **Otimizações de Tela Cheia**:
    *   Clique direito no `SwitchPilot.exe` → Propriedades.
    *   Aba Compatibilidade → **Desmarcar** "Otimizações de tela cheia".
3.  **Captura de Janela**: Tente mudar o modo de captura de "Monitor" para "Janela".

### 🔴 CPU/Memória muito alta
1.  **Intervalo**: Aumente para 1.0s ou 1.5s (Configurações → Limiar).
2.  **Área de Captura**: Reduza o tamanho da região monitorada. Capture 200x200 pixels em vez de Full HD.
3.  **Limpeza**: Remova referências antigas que não está usando (máximo 5-10 ativas recomendado).

### 🔴 Falsos Positivos (Detecta errado)
1.  **Aumente o Limiar**: Suba para 0.95 ou mais.
2.  **Modo Sequência**: Ative para 2 ou 3 confirmações. Isso obriga o programa a ver a cena 3 vezes seguidas antes de agir.
3.  **Região Específica**: Não capture "céu azul" ou "parede branca". Capture logos, textos ou elementos únicos da cena.
