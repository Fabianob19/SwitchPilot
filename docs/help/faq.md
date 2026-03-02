# Perguntas Frequentes (FAQ)

Aqui estão as dúvidas mais comuns sobre o uso do **SwitchPilot**.

---

### O SwitchPilot precisa de internet para funcionar?
**Não!** O processamento de inteligência artificial (reconhecimento de imagem e NSFW) ocorre `100% localmente` na sua própria máquina (CPU/GPU). Isso garante privacidade absoluta e nenhum atraso de rede (lag).

### Por que ele não reconhece a tela do meu OBS?
Quando você captura a Região PGM usando o modo **Monitor**, certifique-se de que a janela do OBS (Preview) não ficará minimizada nem escondida atrás de outros programas pesados. Além disso, se o OBS estiver sendo executado como "Administrador", o SwitchPilot também precisará ser executado como "Administrador" para conseguir "ver" a tela dele.

### Qual o uso recomendado de CPU?
Por padrão, o SwitchPilot consome muito pouco da CPU quando o monitoramento não está ativo.
Ao clicar em **"Iniciar Monitoramento"**, ele passa a capturar e analisar várias imagens por segundo. 
> Recomendamos um **Intervalo de Captura de 0.5s** nas opções de **Limiares** caso seu computador seja mais antigo.

### Quantas imagens de referência posso adicionar?
Você pode registrar **dezenas de imagens**. Porém, a cada ciclo (ex: meio segundo), a IA irá verificar **todas as suas imagens contra a sua tela**. Quanto mais imagens de referência, mais CPU/GPU ele precisará. Recomendamos manter de `3 a 10` imagens cruciais.

### As funções automáticas não disparam no vMix
Verifique se a opção `Web Controller` está ativa nas Configurações do vMix e não esqueça de configurar *a porta correta* (padrão é 8088). Tente apertar **Testar Conexão** no painel esquerdo; o log mostrará "Sucesso" se conseguir se conectar.
