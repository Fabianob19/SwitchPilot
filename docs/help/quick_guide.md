# SwitchPilot - Guia Rápido

## 🎯 INÍCIO RÁPIDO (5 PASSOS)

1.  **Configure OBS/vMix**
    *   **OBS**: Porta 4455, senha do WebSocket.
    *   **vMix**: Porta 8088, ative Web Controller.

2.  **Defina a Área de Captura**
    *   Vá em **Gerenciador de Referências** → **Selecionar Região PGM**.
    *   Desenhe a área da tela que o SwitchPilot deve "assistir".

3.  **Adicione Imagens de Referência**
    *   Clique em **Adicionar Referência**.
    *   Selecione um print/imagem da cena que você quer detectar.

4.  **Configure as Ações**
    *   Duplo clique na referência criada.
    *   Diga o que fazer quando ela for encontrada (ex: Mudar para Cena X no OBS).

5.  **Inicie**
    *   Clique em **Iniciar Monitoramento**.
    *   O sistema fará tudo automaticamente!

---

## ⚙️ COMO FUNCIONA A DETECÇÃO

*   **Captura**: O programa olha para a região definida em tempo real.
*   **Comparação**: Compara o que vê com suas imagens de referência.
*   **Score**: Calcula um score de similaridade (0.0 a 1.0).
*   **Ação**: Se Score >= Limiar, a ação é executada.

---

## 💡 DICAS RÁPIDAS

### Score
*   **> 0.92**: Excelente. Detecção precisa.
*   **< 0.85**: Ruim. Ajuste a iluminação ou mude a imagem de referência.

### Limiar (Threshold)
*   **Alto (0.93+)**: Muito preciso, mas pode falhar se houver pequenas mudanças.
*   **Médio (0.88-0.92)**: **Recomendado**. Equilíbrio ideal.
*   **Baixo (< 0.87)**: Muito sensível, risco de falsos positivos.

### Performance
*   **Intervalo 0.5s**: Recomendado. Bom equilíbrio entre rapidez e uso de CPU.
