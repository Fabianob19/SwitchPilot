# 🔴 SOLUÇÕES: Erros de Instalação do SwitchPilot

## 📋 **ERROS COMUNS:**

### **Erro 1: "Incapaz de executar o arquivo unins000.exe"**
Este erro aparece quando você tenta instalar uma nova versão do SwitchPilot, mas o Windows ainda tem registros de uma instalação antiga cujo desinstalador foi deletado ou corrompido.

### **Erro 2: "Código 225 - Não possui o software adequado"**
Este erro indica que faltam dependências do sistema Windows (Visual C++ Redistributable).

---

## ✅ **SOLUÇÃO PARA ERRO "unins000.exe" (3 PASSOS):**

### **1️⃣ Delete a pasta antiga manualmente**

Abra o Explorador de Arquivos e delete esta pasta:
```
C:\Users\[SEU_NOME]\AppData\Local\Programs\SwitchPilot
```

**Como acessar rapidamente:**
1. Pressione `Win + R`
2. Cole: `%LocalAppData%\Programs`
3. Pressione Enter
4. Delete a pasta `SwitchPilot` se existir

---

### **2️⃣ (Opcional) Limpe o Menu Iniciar**

Delete os atalhos antigos:
1. Pressione `Win + R`
2. Cole: `%AppData%\Microsoft\Windows\Start Menu\Programs`
3. Pressione Enter
4. Delete a pasta `SwitchPilot` se existir

---

### **3️⃣ Execute o novo instalador COMO ADMINISTRADOR**

1. **Clique direito** no arquivo `SwitchPilot_v1.5.1_Setup.exe`
2. Escolha **"Executar como administrador"**
3. Siga a instalação normalmente

---

## ✅ **SOLUÇÃO PARA ERRO "CÓDIGO 225" (FALTAM DEPENDÊNCIAS):**

### **Causa:**
Falta o Microsoft Visual C++ Redistributable 2015-2022 (x64)

### **Solução Automática:**
1. Execute o novo instalador do SwitchPilot v1.5.1+
2. Ele vai **detectar automaticamente** a falta da dependência
3. Vai perguntar se quer **baixar e instalar**
4. Clique em **"Sim"**
5. Aguarde a instalação (~25 MB)
6. Continue a instalação do SwitchPilot normalmente

### **Solução Manual:**
1. Baixe de: **https://aka.ms/vs/17/release/vc_redist.x64.exe**
2. Execute o instalador baixado
3. Clique em **"Instalar"**
4. Aguarde a instalação terminar
5. Execute o instalador do SwitchPilot novamente

---

## 🎯 **SE AINDA DER ERRO:**

### **Limpeza Completa do Registro:**

1. Pressione `Win + R`
2. Digite: `regedit` e pressione Enter
3. Navegue até:
   ```
   HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall
   ```
4. Procure por uma chave com nome parecido com:
   ```
   {A5B8C3D4-E6F7-4A8B-9C0D-1E2F3A4B5C6D}_is1
   ```
5. **Clique direito** nela e escolha **"Excluir"**
6. Feche o Registro e execute o instalador novamente

---

## 📢 **BOA NOTÍCIA:**

A partir da **versão 1.5.1+**, o instalador detecta e **corrige automaticamente** estes problemas! O instalador inteligente vai:

✅ Detectar instalações antigas corrompidas  
✅ Limpar automaticamente o registro  
✅ Perguntar se quer desinstalar versões antigas  
✅ Verificar se o Visual C++ Redistributable está instalado  
✅ Oferecer download e instalação automática das dependências  
✅ Instalar sem erros  

---

## 🆘 **PRECISA DE MAIS AJUDA?**

- **Discord:** https://discord.gg/2MKdsQpMFt
- **Issues GitHub:** https://github.com/Fabianob19/SwitchPilot/issues
- **Email:** fabianob19@gmail.com

---

**Desenvolvido por Fabianob19**  
**Em parceria com André Gribel (O Safadasso)** 🎮

