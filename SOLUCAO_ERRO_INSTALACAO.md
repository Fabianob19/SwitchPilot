# 🔴 SOLUÇÃO: Erro "Incapaz de executar o arquivo unins000.exe"

## 📋 **O QUE É ESSE ERRO?**

Este erro aparece quando você tenta instalar uma nova versão do SwitchPilot, mas o Windows ainda tem registros de uma instalação antiga cujo desinstalador foi deletado ou corrompido.

---

## ✅ **SOLUÇÃO RÁPIDA (3 PASSOS):**

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

A partir da **versão 1.5.1**, o instalador detecta e **corrige automaticamente** este problema! Se você baixou a versão mais recente, o instalador vai:

✅ Detectar instalações antigas corrompidas  
✅ Limpar automaticamente o registro  
✅ Perguntar se quer desinstalar versões antigas  
✅ Instalar sem erros  

---

## 🆘 **PRECISA DE MAIS AJUDA?**

- **Discord:** https://discord.gg/2MKdsQpMFt
- **Issues GitHub:** https://github.com/Fabianob19/SwitchPilot/issues
- **Email:** fabianob19@gmail.com

---

**Desenvolvido por Fabianob19**  
**Em parceria com André Gribel (O Safadasso)** 🎮

