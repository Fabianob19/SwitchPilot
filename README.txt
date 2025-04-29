# Automação de Corte Automático no vMix

Este pacote permite que você monitore o PGM do vMix e, ao detectar a tela "fora do ar", faça o corte automático para uma entrada/câmera de sua escolha.

---

## Arquivos necessários
- **monitor_vmix.py**: Script principal da automação.
- **requirements.txt**: Lista de dependências Python necessárias para rodar o script.
- **fora_do_ar.png**: Imagem de referência da tela "fora do ar" (deve ser um print da tela preta com ruído, igual ao exemplo fornecido).

---

## Passo a passo para rodar o script

### 1. Pré-requisitos
- Ter o **vMix** instalado e aberto no computador.
- Ter o **Python** instalado (de preferência Python 3.8 ou superior). Se não tiver, baixe em: https://www.python.org/downloads/

### 2. Ativar a API Web do vMix
1. Abra o vMix normalmente.
2. No vMix, clique em **Settings** (ícone de engrenagem ou menu superior).
3. No menu lateral, clique em **Web Controller**.
4. Marque a opção **"Enable Web Controller (port 8088)"**.
5. Clique em **OK** para salvar.

> **Importante:** O vMix precisa estar aberto e com a API ativada sempre que for rodar o script.

### 3. Colocar os arquivos na mesma pasta
- Crie uma pasta (por exemplo, `Automacao_vMix`).
- Coloque dentro dela os arquivos: `monitor_vmix.py`, `requirements.txt` e `fora_do_ar.png`.

### 4. Instalar as dependências
1. Abra o **Prompt de Comando** ou **PowerShell**.
2. Navegue até a pasta onde estão os arquivos. Exemplo:

       cd C:\caminho\para\Automacao_vMix

3. Instale as dependências com o comando:

       pip install -r requirements.txt

> Se aparecer mensagem de "Requirement already satisfied", significa que já está instalado.

### 5. Rodar o script
No mesmo terminal, execute:

    python monitor_vmix.py

### 6. Siga as instruções na tela
- O script vai mostrar as entradas disponíveis no vMix (câmeras, vídeos, etc).
- Digite o número da entrada que deseja usar quando detectar "fora do ar" e pressione Enter.
- O script vai pedir para informar a posição e tamanho do PGM na tela:
    - **Top**: distância do topo da tela até o início do PGM (em pixels)
    - **Left**: distância da esquerda da tela até o início do PGM (em pixels)
    - **Width**: largura do PGM (em pixels)
    - **Height**: altura do PGM (em pixels)
- Se não souber, apenas pressione Enter para usar os valores padrão.
- O script começará a monitorar automaticamente.

---

## Dicas e dúvidas comuns

- **Como saber a posição e tamanho do PGM?**
  - Se o corte não funcionar corretamente, ajuste os valores de Top, Left, Width e Height para capturar exatamente a área do PGM na tela.
  - Você pode usar a ferramenta "Captura de Tela" do Windows para medir a área.

- **A imagem de referência precisa ser igual à tela fora do ar?**
  - Sim! Tire um print da tela exatamente como aparece quando está fora do ar e salve como `fora_do_ar.png`.

- **O script não encontra entradas no vMix!**
  - Verifique se o vMix está aberto e a API Web está ativada (passo 2).
  - Certifique-se de que o firewall não está bloqueando a porta 8088.

- **Como parar o script?**
  - Pressione `Ctrl+C` no terminal para encerrar.

- **Posso usar em outro computador?**
  - Sim! Basta copiar a pasta com todos os arquivos e seguir o passo a passo.

---

## Suporte
Se aparecer alguma mensagem de erro, copie e envie para quem te forneceu o script para suporte.

Se precisar de ajuda para ajustar a região do PGM, ou para criar a imagem de referência, peça auxílio ao responsável pelo script.

---

**Desenvolvido para automação de corte no vMix.** 