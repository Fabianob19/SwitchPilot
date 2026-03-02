# Filtro NSFW (Detecção de Conteúdo Inadequado)

O **SwitchPilot v1.7.1+** introduziu um poderoso motor de Inteligência Artificial baseado no modelo YOLOv8 para identificar proativamente e evitar a transmissão acidental de conteúdo Sensível ou Inadequado (NSFW - *Not Safe For Work*).

---

## 🛡️ Como Funciona o Bloqueio NSFW?

Diferente do detector de Referências (que busca imagens que você configurou), a Detecção NSFW roda em uma **fase invisível** separada:
1. **Captura Inicial**: O quadro da Região PGM é capturado a cada intervalo.
2. **Scanner Analítico**: Um modelo `YOLOv8 OnnxRuntime` analisa a imagem para encontrar elementos classificados como: `Nudez Feminina`, `Nudez Masculina` ou características adultas primárias.
3. **Interceptação (Corte Crítico)**: Se a IA encontrar esses elementos acima do Limiar de Confiança, ela **cancela imediatamente** a verificação de imagens de corte padrão e dispara a Segurança Máxima, trocando para sua Cena Segura!

---

## ⚙️ Configuração do Sistema NSFW

A configuração fica em **Configurações → Limiares de Detecção (Ctrl+T)**.

### Limiar Geral de Gatilho
Define quão seguro o SwitchPilot deve estar de que a tela possui algo indevido. O recomendando é **`0.65`** até **`0.75`** para evitar falsos positivos (como achar que o dedo de alguém é outra coisa).

### Cena de Emergência
Para onde o OBS/vMix deve cortar caso algo indesejado apareça? Pense numa Tela de "Aguarde", ou "Cena Técnica". É vital que na aba de **Configuração OBS/vMix**, os dados estejam corretos e você tenha uma Cena Segura configurada, ou o filtro apitará mas o programa não saberá para qual cena técnica cortar.

> **💡 O que é Fallback para CPU?**
> A detecção YOLO usa Aceleração de Placa de Vídeo (DirectML) por padrão para rodar os blocos de Inteligência Artificial. Se sua máquina não tiver GPU offboard (NVIDIA/AMD), ele usará a sua CPU normal para fazer os cálculos.

---

## ⚡ Performance vs Segurança

Ter dois modelos de IA rodando sobrepostos (Casamento de Modelo + YOLOv8) requer muito poder de processamento. 

Para extrair o melhor dos dois:
* **Diminua a Região PGM**: O YOLO processará as imagens 10x mais rápido se o seu retângulo for pequeno!
* **Intervalo de Verificação (Ms)**: Se o seu computador começar a travar (Lag), aumente o intervalo de 500ms para 1000ms. O SwitchPilot demorará mais para cortar, porém o seu PC ficará mais livre.
