# Perguntas Frequentes (FAQ)

### ❓ O programa não detecta minha cena!
**Verifique:**
*   A **região de captura** está correta? (Menu Visualizar → Exibir Área de Captura).
*   A **imagem de referência** é nítida? (Use PNG, evite compressão).
*   O **limiar** está muito alto? (Tente baixar para 0.88-0.90).
*   A fonte (janela/monitor) está visível?

### ❓ A detecção está muito lenta!
**Soluções:**
*   **Reduza a área de captura**: Capture apenas um pedaço pequeno e único da tela (ex: o logo do canal), não a tela toda.
*   **Aumente o intervalo**: Vá em Configurações → Limiar e mude para 0.8s ou 1.0s.
*   Feche programas pesados em segundo plano.

### ❓ OBS não conecta!
**Checklist:**
1.  **WebSocket 5.x** está ativo no OBS? (Ferramentas → Configurações WebSocket).
2.  A **porta** é a mesma? (Padrão 4455).
3.  A **senha** está correta?
4.  O OBS está aberto?

### ❓ vMix não responde!
**Checklist:**
1.  **Web Controller** ativado? (Configurações → Web Controller).
2.  Porta correta (8088)?
3.  **Nome da cena exato**? (Maiúsculas/minúsculas importam!).

### ❓ Funciona com StreamLabs?
*   **StreamLabs OBS (SLOBS)**: **SIM** ✅ (Usa a mesma API WebSocket do OBS).
*   **StreamLabs Desktop**: **NÃO** ❌ (Não tem API compatível).

### ❓ Funciona com Twitch/YouTube?
**SIM!** ✅ O SwitchPilot controla o seu software de transmissão (OBS/vMix). Não importa para onde você está transmitindo (Twitch, YouTube, Facebook, TikTok), ele vai funcionar.

### ❓ Preciso instalar o NDI?
**NÃO** ❌. O NDI é opcional.
*   Para capturar tela ou janelas normais, você **não** precisa do NDI.
*   Instale apenas se você usa fontes de vídeo via rede NDI.
