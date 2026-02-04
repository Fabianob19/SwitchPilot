# Tutorial Completo - SwitchPilot

## 1. INSTALAÇÃO
*   Baixe o instalador ou executável mais recente do GitHub.
*   Execute como administrador (recomendado para garantir permissões de captura).
*   Atalhos serão criados automaticamente na área de trabalho e menu iniciar.

## 2. CONFIGURAÇÃO BÁSICA

### a) Conectar OBS
1.  No OBS, vá em **Ferramentas** → **Configurações WebSocket**.
2.  Anote a porta (padrão `4455`) e a senha.
3.  No SwitchPilot, vá na aba **Configuração OBS**.
4.  Preencha IP (`localhost`), porta e senha.
5.  Clique em **Conectar** e aguarde a confirmação.

### b) Conectar vMix
1.  No vMix, vá em **Configurações** → **Web Controller**.
2.  Ative a opção **Enable Web Controller**.
3.  No SwitchPilot, vá na aba **Configuração vMix**.
4.  Preencha IP (`localhost`) e porta (`8088`).
5.  Clique em **Testar Conexão**.

### c) Selecionar Fonte de Captura
1.  Vá à aba **Gerenciador de Referências**.
2.  Clique em **Selecionar Região PGM**.
3.  Escolha: **Monitor** (tela inteira) ou **Janela** (aplicativo específico).
4.  Desenhe a região que será monitorada na tela.

## 3. ADICIONANDO REFERÊNCIAS

### a) Criar Referência
1.  Clique no botão **Adicionar Referência**.
2.  Escolha uma imagem clara e nítida da cena que deseja detectar.
3.  Dê um nome descritivo (ex: "Câmera Principal", "Tela de Aguarde").

### b) Configurar Ações
1.  Clique duas vezes na referência criada na lista.
2.  Escolha o tipo de ação: **OBS** (Trocar Cena, Toggle Filtro) ou **vMix**.
3.  Configure os parâmetros necessários (nome da cena, input, etc.).
4.  Clique em **Salvar**.

### c) Testar
1.  Use o botão **Teste Manual** na janela de configuração de ação.
2.  Verifique se a ação ocorre no OBS/vMix.
3.  Ajuste se necessário.

## 4. USO AVANÇADO

### Ajustar Limiares
Acesse **Menu Configurações** → **Limiar de Similaridade**:
*   **Limiar Estático**: 0.90-0.95 (recomendado **0.92**). Define quão parecida a imagem deve ser.
*   **Modo Sequência**: 2-3 detecções. Exige que a imagem seja detectada X vezes seguidas para confirmar.
*   **Intervalo**: 0.3s-1.0s (padrão **0.5s**). Tempo entre cada verificação.

### Dicas de Otimização
*   **Performance**: Reduza a área de captura e aumente o intervalo para consumir menos CPU.
*   **Precisão**: Use imagens PNG sem compressão e evite áreas com movimento constante (relógios, vídeos em loop).
