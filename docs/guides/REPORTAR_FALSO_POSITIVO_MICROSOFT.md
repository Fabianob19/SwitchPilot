# 📝 COMO REPORTAR FALSO POSITIVO À MICROSOFT

## 🎯 **PASSO A PASSO COMPLETO:**

### **1️⃣ Acesse o Portal da Microsoft**
https://www.microsoft.com/en-us/wdsi/filesubmission

### **2️⃣ Preencha o Formulário**

**Tipo de Envio:**
- Selecione: **"Software developer"**

**Informações do Arquivo:**
- **File SHA-256:** (vou gerar abaixo)
- **File Name:** `SwitchPilot.exe`
- **Product Name:** `SwitchPilot`
- **Product Version:** `1.5.1`

**Informações do Desenvolvedor:**
- **Your Name:** Fabiano Brandão
- **Company:** (se tiver) ou "Individual Developer"
- **Email:** fabianob19@gmail.com
- **Phone:** (opcional)

**Descrição do Problema:**
```
This is a false positive detection. SwitchPilot is a legitimate open-source 
application for controlling OBS Studio and vMix during live streams.

- Project URL: https://github.com/Fabianob19/SwitchPilot
- Source Code: Available on GitHub (open-source)
- Built with: Python 3.10 + PyInstaller
- No malicious code or behavior

The application only:
- Monitors screen regions for image matching
- Sends HTTP/WebSocket commands to OBS/vMix
- Manages user-defined reference images

Please whitelist this application.
```

**Arquivo:**
- Faça upload do `SwitchPilot.exe`

### **3️⃣ Aguardar Análise**
- Microsoft analisa em 1-3 semanas
- Você receberá email com resultado

### **4️⃣ Resultado Positivo:**
- Windows Defender para de bloquear
- Outras antivírus podem seguir a decisão

---

## 🔢 **GERAR SHA-256 DO ARQUIVO:**

Execute no PowerShell:
```powershell
Get-FileHash "installer_output\SwitchPilot_v1.5.1_Setup.exe" -Algorithm SHA256
```

Copie o hash e cole no formulário da Microsoft.

---

## ⚠️ **IMPORTANTE:**

- Você precisa reportar **A CADA NOVA VERSÃO**
- Se mudar muito o código, pode ser detectado novamente
- Assinatura digital é a solução mais definitiva

---

## 🔗 **LINKS ÚTEIS:**

- **Reportar à Microsoft:** https://www.microsoft.com/en-us/wdsi/filesubmission
- **Verificar Status:** https://www.microsoft.com/en-us/wdsi/filesubmission/status
- **VirusTotal (verificar outros antivírus):** https://www.virustotal.com

---

## 💡 **DICA:**

Também reporte em outros antivírus populares:
- **Avast:** https://www.avast.com/false-positive-file-form.php
- **AVG:** https://www.avg.com/en-us/false-positive-file-form
- **Kaspersky:** https://opentip.kaspersky.com/
- **Norton:** https://submit.norton.com/

Quanto mais você reportar, menos usuários terão problemas! ✅

