#!/usr/bin/env python3
"""
ConfigManager para SwitchPilot
Gerencia persistência de todas as configurações da aplicação.
"""

import json
import os
import zipfile
from typing import Dict, Any


def get_config_dir():
    """Retorna o diretório de configuração do usuário."""
    if os.name == 'nt':
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        config_dir = os.path.join(appdata, 'SwitchPilot')
    else:
        config_dir = os.path.expanduser('~/.config/SwitchPilot')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_config_path():
    """Retorna o caminho do arquivo de configuração principal."""
    return os.path.join(get_config_dir(), 'switchpilot_config.json')


# Também suporta o config legado na raiz do projeto (backward compat)
LEGACY_CONFIG_PATH = "switchpilot_config.json"


class ConfigManager:
    """Gerencia a persistência de todas as configurações do SwitchPilot.

    Centraliza save/load de:
    - Configurações da janela (posição, tamanho)
    - Configurações OBS (host, port, password)
    - Configurações vMix (host, port)
    - Configurações PGM (fonte de captura, região)
    - Referências (lista com caminhos, ações, thresholds)
    - Configurações de monitoramento (intervalo, threshold padrão)
    """

    # Valores padrão para todas as configurações
    DEFAULTS = {
        'window_settings': {
            'x': 100, 'y': 100, 'width': 800, 'height': 600
        },
        'obs_settings': {
            'host': 'localhost', 'port': '4455', 'password': ''
        },
        'vmix_settings': {
            'host': 'localhost', 'port': '8088'
        },
        'pgm_settings': {
            'source_type': 'Monitor',
            'monitor_index': 0,
            'window_title': '',
            'ndi_source': '',
            'region': None
        },
        'references': [],
        'monitoring_settings': {
            'interval': 0.5,
            'default_threshold': 0.90
        }
    }

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_path = get_config_path()
        self._dirty = False  # Flag para saber se há mudanças não salvas

    def load(self) -> Dict[str, Any]:
        """Carrega configurações do disco.

        Tenta primeiro o caminho padrão em AppData.
        Se não existir, tenta o legado na raiz do projeto.
        Se nenhum existir, usa defaults.
        """
        config = {}
        loaded_from = None

        # 1. Tentar carregar de AppData
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                loaded_from = self._config_path
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ConfigManager] Erro ao ler {self._config_path}: {e}")

        # 2. Fallback: tentar config legado
        if not config and os.path.exists(LEGACY_CONFIG_PATH):
            try:
                with open(LEGACY_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                loaded_from = LEGACY_CONFIG_PATH
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ConfigManager] Erro ao ler {LEGACY_CONFIG_PATH}: {e}")

        # 3. Preencher com defaults onde não houver valor
        for key, default_val in self.DEFAULTS.items():
            if key not in config:
                config[key] = default_val
            elif isinstance(default_val, dict):
                # Merge sub-chaves com defaults
                for sub_key, sub_default in default_val.items():
                    if sub_key not in config[key]:
                        config[key][sub_key] = sub_default

        self._config = config
        self._dirty = False

        if loaded_from:
            print(f"[ConfigManager] Configurações carregadas de: {loaded_from}")
        else:
            print("[ConfigManager] Nenhuma configuração encontrada, usando padrões.")

        return dict(self._config)  # Retorna cópia

    def save(self) -> bool:
        """Salva todas as configurações no disco.

        Salva em AppData E mantém cópia no legado para compatibilidade.
        """
        try:
            # Salvar no caminho principal (AppData)
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            # Também salvar no legado (raiz do projeto) para compatibilidade
            try:
                with open(LEGACY_CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            except IOError:
                pass  # Não é crítico se falhar no legado

            self._dirty = False
            print(f"[ConfigManager] Configurações salvas em: {self._config_path}")
            return True

        except Exception as e:
            print(f"[ConfigManager] Erro ao salvar: {e}")
            return False

    # --- Getters/Setters por seção ---

    def get(self, section: str, key: str = None, default=None):
        """Obtém um valor de configuração.

        Args:
            section: Nome da seção (ex: 'obs_settings')
            key: Chave dentro da seção (opcional, retorna seção inteira se None)
            default: Valor padrão se não encontrado
        """
        section_data = self._config.get(section, self.DEFAULTS.get(section, {}))
        if key is None:
            return section_data
        if isinstance(section_data, dict):
            return section_data.get(key, default)
        return default

    def set(self, section: str, data: Any):
        """Define uma seção inteira de configuração."""
        self._config[section] = data
        self._dirty = True

    def update(self, section: str, key: str, value: Any):
        """Atualiza uma chave específica dentro de uma seção."""
        if section not in self._config:
            self._config[section] = {}
        if isinstance(self._config[section], dict):
            self._config[section][key] = value
            self._dirty = True

    # --- Seções específicas ---

    def get_window_settings(self) -> dict:
        return self.get('window_settings') or self.DEFAULTS['window_settings']

    def set_window_settings(self, x: int, y: int, width: int, height: int):
        self.set('window_settings', {'x': x, 'y': y, 'width': width, 'height': height})

    def get_obs_settings(self) -> dict:
        return self.get('obs_settings') or self.DEFAULTS['obs_settings']

    def set_obs_settings(self, host: str, port: str, password: str = ''):
        self.set('obs_settings', {'host': host, 'port': port, 'password': password})

    def get_vmix_settings(self) -> dict:
        return self.get('vmix_settings') or self.DEFAULTS['vmix_settings']

    def set_vmix_settings(self, host: str, port: str):
        self.set('vmix_settings', {'host': host, 'port': port})

    def get_pgm_settings(self) -> dict:
        return self.get('pgm_settings') or self.DEFAULTS['pgm_settings']

    def set_pgm_settings(self, source_type: str, monitor_index: int = 0,
                         window_title: str = '', ndi_source: str = '',
                         region: list = None):
        self.set('pgm_settings', {
            'source_type': source_type,
            'monitor_index': monitor_index,
            'window_title': window_title,
            'ndi_source': ndi_source,
            'region': region
        })

    def get_references(self) -> list:
        """Retorna lista de referências (sem image_data, apenas metadados)."""
        return self.get('references') or []

    def set_references(self, references: list):
        """Salva lista de referências (metadados serializáveis apenas)."""
        # Filtrar campos não serializáveis (image_data contém numpy arrays)
        serializable = []
        for ref in references:
            clean_ref = {
                'name': ref.get('name', ''),
                'type': ref.get('type', 'static'),
                'path': ref.get('path', ''),
                'actions': ref.get('actions', []),
                'pgm_details': ref.get('pgm_details', {})
            }
            # Salvar frame_paths se for sequência
            if ref.get('type') == 'sequence':
                clean_ref['frame_paths'] = ref.get('frame_paths', [])
            serializable.append(clean_ref)
        self.set('references', serializable)

    def get_monitoring_settings(self) -> dict:
        return self.get('monitoring_settings') or self.DEFAULTS['monitoring_settings']

    def set_monitoring_settings(self, interval: float = 0.5, default_threshold: float = 0.90):
        self.set('monitoring_settings', {
            'interval': interval,
            'default_threshold': default_threshold
        })

    # --- Export/Import ---

    def export_to_zip(self, zip_path: str, references_dir: str) -> bool:
        """Exporta configurações + imagens de referência para um arquivo .zip

        Args:
            zip_path: Caminho onde salvar o .zip
            references_dir: Diretório com as imagens de referência
        """
        try:
            # Salvar config atualizada antes de exportar
            self.save()

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Adicionar config JSON
                zf.write(self._config_path, 'switchpilot_config.json')

                # Adicionar imagens de referência
                if os.path.exists(references_dir):
                    for root, dirs, files in os.walk(references_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Caminho relativo dentro do zip
                            arc_name = os.path.join(
                                'references',
                                os.path.relpath(file_path, references_dir)
                            )
                            zf.write(file_path, arc_name)

            print(f"[ConfigManager] Exportado para: {zip_path}")
            return True

        except Exception as e:
            print(f"[ConfigManager] Erro ao exportar: {e}")
            return False

    def import_from_zip(self, zip_path: str, references_dir: str) -> bool:
        """Importa configurações + imagens de um arquivo .zip

        Args:
            zip_path: Caminho do .zip a importar
            references_dir: Diretório onde extrair as imagens
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Extrair config JSON
                if 'switchpilot_config.json' in zf.namelist():
                    config_data = zf.read('switchpilot_config.json')
                    imported_config = json.loads(config_data.decode('utf-8'))
                    self._config = imported_config
                    self.save()

                # Extrair imagens de referência
                for name in zf.namelist():
                    if name.startswith('references/'):
                        # Remover prefixo 'references/'
                        relative_path = name[len('references/'):]
                        if relative_path:  # Ignorar diretório vazio
                            target_path = os.path.join(references_dir, relative_path)
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            with open(target_path, 'wb') as f:
                                f.write(zf.read(name))

            print(f"[ConfigManager] Importado de: {zip_path}")
            return True

        except Exception as e:
            print(f"[ConfigManager] Erro ao importar: {e}")
            return False

    def import_from_json(self, json_path: str) -> bool:
        """Importa configurações de um arquivo JSON simples (compatibilidade legada)."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            # Merge com config atual (não sobrescreve tudo)
            for key, value in imported_config.items():
                self._config[key] = value

            self.save()
            print(f"[ConfigManager] Importado JSON de: {json_path}")
            return True

        except Exception as e:
            print(f"[ConfigManager] Erro ao importar JSON: {e}")
            return False

    @property
    def has_unsaved_changes(self) -> bool:
        return self._dirty
