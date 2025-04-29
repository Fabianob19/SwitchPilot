# Como descobrir a região do PGM na tela

Este guia ensina como usar o script para selecionar a área do PGM (programa principal) na tela do seu computador. Siga o passo a passo abaixo:

---

## 1. Pré-requisitos
- Ter o Python instalado no computador.
- Ter as dependências instaladas (se não tiver, peça para quem te enviou o pacote rodar: pip install -r requirements.txt)

---

## 2. Como usar o script

1. **Deixe a tela do PGM visível na sua área de trabalho.**
   - Organize as janelas para que o PGM esteja aparecendo na tela.

2. **Abra o Prompt de Comando ou PowerShell** na pasta onde está o arquivo `descobrir_regiao_pgm.py`.

3. **Execute o comando:**
   
       python descobrir_regiao_pgm.py

4. **Siga as instruções que aparecerem na tela:**
   - Leia as instruções iniciais.
   - Quando a imagem da sua tela aparecer, clique com o mouse no canto superior esquerdo da área do PGM, segure e arraste até o canto inferior direito da área do PGM.
   - Solte o mouse para finalizar a seleção.

5. **Veja as coordenadas exibidas no final:**
   - O script vai mostrar os valores de `top`, `left`, `width` e `height`.
   - Anote esses valores! Eles serão usados no script principal de automação.

---

## Dicas
- Se errar a seleção, basta fechar a janela e rodar o script novamente.
- Se não aparecer nada, verifique se o Python e as dependências estão instalados corretamente.

---

Se tiver dúvidas, envie uma mensagem para quem te forneceu o script! 