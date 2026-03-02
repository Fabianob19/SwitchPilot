# Tutorial Completo - SwitchPilot

Bem-vindo ao guia detalhado do **SwitchPilot**. Aprenda como configurar e dominar a automação de cortes usando detecção de imagem por Inteligência Artificial.

---

## 1. Instalação e Preparação inicial

> O SwitchPilot requer privilégios de administrador em algumas máquinas Windows para capturar a tela corretamente, especialmente se a janela-alvo estiver rodando como administrador (ex: jogos ou OBS).

1. Baixe o instalador mais recente na aba de *Releases* do GitHub.
2. Execute o instalador (recomendamos marcar a opção de criar atalho na Área de Trabalho).
3. Ao abrir o aplicativo pela primeira vez, clique com o botão direito no ícone e selecione **"Executar como administrador"**.

---

## 2. Configurações de Conexão

Para que o SwitchPilot possa controlar seu software de transmissão, ele precisa estar conectado. Suportamos **OBS Studio** e **vMix**.

### a) Conectando ao OBS Studio
O OBS Studio possui um servidor WebSocket embutido na versão 28+.
1. Abra o OBS Studio e acesse `Ferramentas` → `Configurações do Servidor WebSocket`.
2. Certifique-se de que a caixa **"Habilitar Servidor WebSocket"** está marcada.
3. Anote a porta (por padrão `4455`) e clique em *Mostrar Senha* para copiar a senha.
4. No SwitchPilot, na aba inferior de *Configuração OBS*, insira o IP (`localhost` se for na mesma máquina), a porta e a senha.
5. Clique no botão **Testar Conexão OBS**.

### b) Conectando ao vMix
O vMix utiliza uma API Web nativa muito rápida.
1. No vMix, acesse `Settings` → `Web Controller`.
2. Marque a opção **"Enable Web Controller"**.
3. O IP padrão será o IP local da sua rede ou `localhost`, e a porta padrão é `8088`.
4. No SwitchPilot, na aba *Configuração vMix*, digite os dados e clique em **Testar Conexão vMix**.

---

## 3. Seleção de Fonte e Região (PGM)

O coração do SwitchPilot é o monitoramento visual. Você precisa definir **onde** a IA deve olhar.

1. Acesse a aba **Gerenciador de Referências**.
2. No topo, em Fonte de Captura, selecione `Monitor` (para capturar monitores inteiros) ou `Janela` (para capturar aplicativos específicos que rodam em segundo plano).
3. Selecione a tela correta ao lado.
4. Clique no botão azul **Selecionar Região PGM**.
5. A tela será congelada. Clique e arraste para desenhar um quadrado perfeito ao redor da área que deseja monitorar. Pressione `<Enter>` para confirmar.

> **💡 Dica Pro:** Desenhe a região o mais restrita possível (ex: apenas o rosto de um palestrante ou placar). Regiões menores consomem absurdamente menos CPU e são muito mais rápidas de processar.

---

## 4. Criando Imagens de Referência

Agora que a área de PGM está definida, precisamos dizer à IA o que ela deve procurar.

1. Clique no botão **Adicionar Referência...** no centro da tela.
2. Um pequeno diálogo de captura aparecerá com o preview da sua tela.
3. Quando a cena desejada estiver aparecendo, clique no botão de câmera 📸.
4. Digite um nome para esta referência (ex: `Camera_Palestrante_A`).
5. Ela aparecerá na **Lista de Referências Atuais**.

---

## 5. Vinculando Ações Automáticas

A mágica acontece quando a IA encontra a imagem de referência e executa um corte de câmera.

1. Selecione a referência recém-criada na lista e clique em **Configurar Ações da Selecionada**.
2. Na nova janela, escolha a sua integração (`OBS` ou `vMix`).
3. Escolha o tipo de Ação (ex: `Trocar Cena`).
4. Preencha os campos exigidos. Por exemplo, digite o nome exato da Cena no OBS.
5. Clique em **Aplicar Mudanças à Ação** e por fim, **OK**.

---

## 6. Iniciando o Motor de Monitoramento

Tudo pronto! 

1. Acesse o painel **Controle** na parte inferior.
2. Clique no botão principal **Iniciar Monitoramento**.
3. A barra lateral direita exibirá um preview real-time (se ativado nas configurações). O status ficará verde.
4. O LOG exibirá cada quadro comparado. Se a IA encontrar a imagem `Camera_Palestrante_A` na região PGM, ela enviará imediatamente o comando de corte para o OBS/vMix!

> A qualquer momento, clique em **Parar Monitoramento** para pausar a análise e testar novos ajustes.
