# 🎯 Sistema de Versão Centralizada

## 📋 **RESUMO**
A versão do SwitchPilot agora é centralizada em um único arquivo: `VERSION`

## 📁 **ARQUIVO PRINCIPAL**
```
VERSION  ← ÚNICA FONTE DA VERDADE
```

**Conteúdo atual:** `1.5.2`

## 🔄 **COMO FUNCIONA**

### **1. Arquivo VERSION**
- Contém apenas o número da versão (ex: `1.5.2`)
- Este é o **ÚNICO** lugar onde você edita a versão

### **2. Atualização Automática**
- `switchpilot/__init__.py` lê automaticamente do arquivo `VERSION`
- Scripts PowerShell atualizam todos os outros arquivos

### **3. Scripts de Atualização**

#### **`update_version_in_installer.ps1`**
```powershell
# Atualiza apenas o SwitchPilot_Installer.iss
powershell -ExecutionPolicy Bypass -File update_version_in_installer.ps1
```

#### **`update_version_everywhere.ps1`**
```powershell
# Atualiza TODOS os arquivos de documentação
powershell -ExecutionPolicy Bypass -File update_version_everywhere.ps1
```

## 🚀 **COMO ATUALIZAR VERSÃO**

### **Passo 1: Editar VERSION**
```bash
# Edite apenas este arquivo:
echo "1.5.3" > VERSION
```

### **Passo 2: Executar Scripts**
```powershell
# Atualizar instalador
powershell -ExecutionPolicy Bypass -File update_version_in_installer.ps1

# Atualizar documentação
powershell -ExecutionPolicy Bypass -File update_version_everywhere.ps1
```

### **Passo 3: Testar**
```bash
python main.py
# Deve mostrar v1.5.3 no título
```

## 📂 **ARQUIVOS ATUALIZADOS AUTOMATICAMENTE**

✅ **Código:**
- `switchpilot/__init__.py` (lê automaticamente)
- `switchpilot/ui/main_window.py` (via script)

✅ **Instalador:**
- `SwitchPilot_Installer.iss` (via script)

✅ **Documentação:**
- `README.md` (via script)
- `CHANGELOG.md` (via script)

## 🎯 **VANTAGENS**

1. ✅ **Única fonte da verdade** - Edite apenas `VERSION`
2. ✅ **Impossível esquecer** - Scripts atualizam tudo automaticamente
3. ✅ **Sem erros de sincronização** - Versão sempre consistente
4. ✅ **Processo simples** - 2 comandos para atualizar tudo

## 🚨 **IMPORTANTE**

- **NUNCA** edite versão diretamente nos outros arquivos
- **SEMPRE** use o arquivo `VERSION` como fonte única
- **SEMPRE** execute os scripts após editar `VERSION`

## 📝 **EXEMPLO COMPLETO**

```bash
# 1. Atualizar versão
echo "1.6.0" > VERSION

# 2. Atualizar tudo automaticamente
powershell -ExecutionPolicy Bypass -File update_version_in_installer.ps1
powershell -ExecutionPolicy Bypass -File update_version_everywhere.ps1

# 3. Testar
python main.py
# Título: "SwitchPilot - v1.6.0" ✅
```

---

**🎉 Agora é impossível ter versões inconsistentes!**
