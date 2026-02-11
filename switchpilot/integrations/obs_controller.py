import websocket
import json
import uuid
import base64
import hashlib
from PyQt5.QtCore import QSettings  # Para ler a senha como no código original por enquanto
import time  # Adicionado para os sleeps nos testes


class OBSController:
    def __init__(self, host='localhost', port='4455', password=''):
        self.host = host
        self.port = port
        self.password = password  # Senha fornecida na inicialização
        self.log_callback = None
        self.ws = None  # conexão persistente (criada sob demanda)
        self._scene_item_id_cache = {}  # (scene_name, source_name) -> sceneItemId

    def set_log_callback(self, callback):
        self.log_callback = callback

    def _log(self, message, level="info"):
        print(f"[OBSController DEBUG PRINT]: Level: {level}, Message: {message}")
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[OBSController {level.upper()}]: {message}")

    def _get_password(self):
        """Retorna a senha de self.password. Loga aviso se vazia."""
        if self.password:
            return self.password

        self._log("Nenhuma senha OBS fornecida diretamente ao OBSController.", "warning")
        return ''  # Retorna string vazia se self.password não foi setada

    def _authenticate(self, ws_instance):
        """Autentica no OBS WebSocket 5.x. Retorna True se bem-sucedido, False caso contrário."""
        password_to_use = self._get_password()
        try:
            resp_hello = ws_instance.recv()
            self._log(f"OBS HELLO: {resp_hello}", "debug")
            data_hello = json.loads(resp_hello)
            identify_payload = {"op": 1, "d": {"rpcVersion": 1}}

            # Modificação da lógica de autenticação:
            # Verificar se 'authentication' (com challenge e salt) está presente no HELLO,
            # independentemente de 'authenticationRequired'.
            auth_data_from_hello = data_hello.get('d', {}).get('authentication')

            if auth_data_from_hello and 'challenge' in auth_data_from_hello and 'salt' in auth_data_from_hello:
                self._log("OBS HELLO contém challenge e salt. Tentando autenticar.", "debug")
                if not password_to_use:
                    self._log("OBS challenge/salt recebido, mas nenhuma senha foi configurada/encontrada para gerar resposta.", "error")
                    self._log("Prosseguindo com IDENTIFY sem string de autenticação, apesar de challenge/salt presentes. Pode falhar.", "warning")
                else:
                    challenge = auth_data_from_hello['challenge']
                    salt = auth_data_from_hello['salt']

                    secret_bytes = (password_to_use + salt).encode('utf-8')
                    secret_hash = hashlib.sha256(secret_bytes).digest()
                    secret_b64 = base64.b64encode(secret_hash).decode('utf-8')

                    auth_response_bytes = (secret_b64 + challenge).encode('utf-8')
                    auth_response_hash = hashlib.sha256(auth_response_bytes).digest()
                    auth_response_b64 = base64.b64encode(auth_response_hash).decode('utf-8')

                    identify_payload["d"]["authentication"] = auth_response_b64
                    self._log("String de autenticação gerada e adicionada ao IDENTIFY.", "debug")
            else:
                self._log("OBS HELLO não contém challenge/salt, ou authenticationRequired é false/ausente. Procedendo sem enviar authentication string.", "debug")

            ws_instance.send(json.dumps(identify_payload))
            self._log(f"OBS IDENTIFY enviado: {json.dumps(identify_payload)}", "debug")

            resp_identified = ws_instance.recv()
            self._log(f"OBS IDENTIFIED recebido: {resp_identified}", "debug")
            data_identified = json.loads(resp_identified)

            if data_identified.get('op') == 2 and data_identified.get('d', {}).get('negotiatedRpcVersion') == 1:
                self._log("Autenticação OBS bem-sucedida.", "info")
                return True
            else:
                self._log(f"Falha na autenticação OBS. Resposta: {resp_identified}", "error")
                return False

        except websocket.WebSocketConnectionClosedException as e:
            self._log(f"Conexão OBS fechada durante a autenticação: {e}. Verifique a senha e config do OBS.", "error")
            return False
        except json.JSONDecodeError as e:
            self._log(f"Erro ao decodificar JSON do OBS durante autenticação: {e}. Resposta: {resp_hello if 'resp_hello' in locals() else 'N/A'}", "error")
            return False
        except Exception as e:
            self._log(f"Erro inesperado durante a autenticação OBS: {e}", "error")
            return False

    # --- Conexão persistente e utilitários ---
    def _ensure_persistent_ws(self):
        """Garante que self.ws esteja conectado e autenticado. Retorna True/False."""
        try:
            if self.ws is not None:
                # websocket-client expõe .connected em WebSocket
                if getattr(self.ws, 'connected', False):
                    return True
                # caso contrário, fecha e recria
                try:
                    self.ws.close()
                except Exception:
                    pass
                self.ws = None
            self._log(f"OBS (persistent): conectando a ws://{self.host}:{self.port}", "debug")
            self.ws = websocket.create_connection(f"ws://{self.host}:{self.port}", timeout=3)
            if not self._authenticate(self.ws):
                try:
                    self.ws.close()
                except Exception:
                    pass
                self.ws = None
                return False
            self._log("OBS (persistent): conectado e autenticado.", "debug")
            return True
        except Exception as e:
            self._log(f"OBS (persistent): falha ao conectar/autenticar: {e}", "error")
            try:
                if self.ws:
                    self.ws.close()
            except Exception:
                pass
            self.ws = None
            return False

    def _ws_send_request(self, request_type, request_data=None, timeout_seconds=5.0):
        """Envia uma requisição usando a conexão persistente e espera pela resposta op:7 correspondente."""
        if request_data is None:
            request_data = {}
        if not self._ensure_persistent_ws():
            return None
        try:
            request_id = str(uuid.uuid4())
            payload = {
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId": request_id,
                    "requestData": request_data
                }
            }
            self._log(f"OBS (persistent): enviando {request_type} -> {json.dumps(payload)}", "debug")
            self.ws.send(json.dumps(payload))

            deadline = time.time() + timeout_seconds
            response_str = ""
            while time.time() < deadline:
                try:
                    response_str = self.ws.recv()
                    parsed_response = json.loads(response_str)
                    op_code = parsed_response.get("op")
                    if op_code == 7 and parsed_response.get("d", {}).get("requestId") == request_id:
                        self._log(f"OBS (persistent): resposta op:7 recebida para {request_type}", "debug")
                        return parsed_response
                    elif op_code == 5:
                        # Evento: ignorar
                        continue
                    else:
                        # Outros pacotes (hello/identified não deveriam chegar aqui)
                        continue
                except Exception as e:
                    self._log(f"OBS (persistent): erro no recv() para {request_type}: {e}", "error")
                    try:
                        self.ws.close()
                    except Exception:
                        pass
                    self.ws = None
                    return None
            self._log(f"OBS (persistent): TIMEOUT aguardando resposta para {request_type}", "error")
            return None
        except Exception as e:
            self._log(f"OBS (persistent): erro ao enviar {request_type}: {e}", "error")
            return None

    def _get_current_program_scene(self):
        resp = self._ws_send_request("GetCurrentProgramScene")
        if resp and resp.get('d', {}).get('requestStatus', {}).get('code') == 100:
            return resp.get('d', {}).get('responseData', {}).get('currentProgramSceneName')
        # Algumas respostas de sucesso podem vir sem requestStatus
        if resp and not resp.get('d', {}).get('requestStatus'):
            return resp.get('d', {}).get('responseData', {}).get('currentProgramSceneName')
        return None

    def _get_scene_item_id_cached(self, scene_name, source_name):
        key = (scene_name, source_name)
        if key in self._scene_item_id_cache:
            return self._scene_item_id_cache[key]
        # Buscar via API e preencher cache
        resp = self._ws_send_request("GetSceneItemList", {"sceneName": scene_name})
        if not resp:
            return None
        items = resp.get('d', {}).get('responseData', {}).get('sceneItems', [])
        for item in items:
            sname = item.get('sourceName')
            sid = item.get('sceneItemId')
            if sname:
                self._scene_item_id_cache[(scene_name, sname)] = sid
        return self._scene_item_id_cache.get(key)

    def _invalidate_scene_cache(self, scene_name):
        # Remove todas as entradas daquela cena
        keys_to_del = [k for k in self._scene_item_id_cache.keys() if k[0] == scene_name]
        for k in keys_to_del:
            del self._scene_item_id_cache[k]

    def _send_request(self, request_type, request_data={}):
        """Conecta, autentica, envia uma requisição e retorna a resposta."""
        ws = None
        try:
            self._log(f"OBS (_send_request): Conectando a ws://{self.host}:{self.port}", "debug")
            ws = websocket.create_connection(f"ws://{self.host}:{self.port}", timeout=3)
            self._log(f"OBS (_send_request): Conexão WebSocket criada.", "debug")

            if not self._authenticate(ws):
                self._log("OBS (_send_request): Autenticação FALHOU. Retornando None.", "error")
                if ws:
                    ws.close()
                return None
            self._log(f"OBS (_send_request): Autenticação bem-sucedida.", "debug")

            request_id = str(uuid.uuid4())
            payload = {
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId": request_id,
                    "requestData": request_data
                }
            }
            self._log(f"OBS (_send_request): Enviando payload: {json.dumps(payload)}", "debug")
            ws.send(json.dumps(payload))
            self._log(f"OBS REQUISIÇÃO ({request_type}) enviada (payload acima). Esperando resposta...", "debug")

            # Loop para aguardar a resposta correta, ignorando eventos
            operation_timeout_seconds = 5.0  # Timeout para esperar a resposta específica
            deadline = time.time() + operation_timeout_seconds
            response_str = ""  # Inicializar para o caso de erro antes da atribuição

            while time.time() < deadline:
                try:
                    response_str = ws.recv()
                    self._log(f"OBS (_send_request): Resposta BRUTA recebida: {response_str[:250]}...", "debug")  # Log um pouco maior

                    parsed_response = json.loads(response_str)
                    op_code = parsed_response.get("op")

                    if op_code == 7:  # RequestResponse
                        if parsed_response.get("d", {}).get("requestId") == request_id:
                            self._log(f"OBS (_send_request): Resposta op:7 com requestId ({request_id}) correspondente recebida.", "debug")
                            # Não fechar ws aqui, o finally fará isso ao retornar.
                            return parsed_response
                        else:
                            self._log(f"OBS (_send_request): Resposta op:7 com requestId diferente. Esperado: {request_id}, Recebido: {parsed_response.get('d', {}).get('requestId')}. Ignorando.", "warning")
                            # Continuar no loop while para esperar a resposta correta ou timeout
                    elif op_code == 5:  # Event
                        self._log(f"OBS (_send_request): Evento op:5 (type: {parsed_response.get('d', {}).get('eventType')}) recebido e ignorado enquanto esperava reqId {request_id}.", "debug")
                        # Continuar no loop while
                    elif op_code == 0:  # Hello (não deveria acontecer depois da autenticação)
                        self._log(f"OBS (_send_request): Mensagem Hello (op:0) recebida inesperadamente enquanto esperava reqId {request_id}. Ignorando.", "warning")
                    elif op_code == 2:  # Identified (não deveria acontecer depois da autenticação)
                        self._log(f"OBS (_send_request): Mensagem Identified (op:2) recebida inesperadamente enquanto esperava reqId {request_id}. Ignorando.", "warning")
                    else:
                        self._log(f"OBS (_send_request): op_code {op_code} inesperado recebido. Ignorando. Resposta: {parsed_response}", "warning")

                except websocket.WebSocketTimeoutException as e_timeout:
                    self._log(f"OBS (_send_request): WebSocketTimeoutException no recv() para reqId {request_id}: {e_timeout}. Continuando a tentar até o deadline.", "warning")
                    if time.time() >= deadline:
                        break
                    continue
                except json.JSONDecodeError as e_json:
                    raw_response_for_log = response_str if response_str else "N/A"
                    self._log(f"Erro ao decodificar JSON da resposta OBS em _send_request (loop) para reqId {request_id}: {e_json}. Resposta bruta: '{raw_response_for_log[:250]}...'.", "error")
                except websocket.WebSocketConnectionClosedException as e_closed:
                    self._log(f"OBS (_send_request): Conexão WebSocket fechada inesperadamente (reqId {request_id}): {e_closed}", "error")
                    return None
                except Exception as e_recv:
                    self._log(f"OBS (_send_request): Exceção no recv() (loop) para reqId {request_id}: {e_recv}. Resposta: {response_str[:250] if response_str else 'N/A'}...", "error")
                    return None

            self._log(f"OBS (_send_request): TIMEOUT GERAL ({operation_timeout_seconds}s) esperando pela resposta op:7 para requestId {request_id}.", "error")
            return None

        except websocket.WebSocketBadStatusException as e_bad_status:
            self._log(f"Erro de status ao conectar/enviar para OBS em ws://{self.host}:{self.port}: {e_bad_status}", "error")
            if ws:
                ws.close()
            return None
        except ConnectionRefusedError:
            self._log(f"Conexão recusada pelo OBS em ws://{self.host}:{self.port} (dentro de _send_request). OBS aberto e WebSocket ativo? Retornando None.", "error")
            if ws:
                ws.close()
            return None
        except Exception as e:
            self._log(f"Erro genérico em _send_request para '{request_type}': {e}. Retornando None.", "error")
            if ws:
                ws.close()
            return None

    # --- Métodos de Ação Específicos ---
    def set_current_scene(self, scene_name):
        self._log(f"OBS: Solicitando mudança para cena: {scene_name}", "info")
        response = self._send_request("SetCurrentProgramScene", {"sceneName": scene_name})
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            self._log(f"OBS: Cena alterada para '{scene_name}' com sucesso.", "info")
            return True
        self._log(f"OBS: Falha ao alterar cena para '{scene_name}'. Resposta: {response}", "error")
        return False

    def start_record(self):
        self._log("OBS: Solicitando iniciar gravação...", "info")
        response = self._send_request("StartRecord")
        if response and response.get('op') == 7:
            status_data = response.get('d', {}).get('requestStatus', {})
            if status_data.get('code') == 100:
                self._log("OBS: Gravação iniciada com sucesso.", "info")
                return True
            else:
                self._log(f"OBS: Falha ao iniciar gravação. Código: {status_data.get('code')}. Resposta: {response}", "error")
                return False
        self._log(f"OBS: Falha ao iniciar gravação (resposta inesperada). Resposta: {response}", "error")
        return False

    def stop_record(self):
        self._log("OBS: Solicitando parar gravação...", "info")
        response = self._send_request("StopRecord")
        if response and response.get('op') == 7:
            status_data = response.get('d', {}).get('requestStatus', {})
            if status_data.get('code') == 100:
                self._log("OBS: Gravação parada com sucesso.", "info")
                return True
            else:
                self._log(f"OBS: Falha ao parar gravação. Código: {status_data.get('code')}. Resposta: {response}", "error")
                return False
        self._log(f"OBS: Falha ao parar gravação (resposta inesperada). Resposta: {response}", "error")
        return False

    def start_stream(self):
        self._log("OBS: Solicitando iniciar transmissão...", "info")
        response = self._send_request("StartStream")
        if response and response.get('op') == 7:
            status_data = response.get('d', {}).get('requestStatus', {})
            if status_data.get('code') == 100:
                self._log("OBS: Transmissão iniciada com sucesso.", "info")
                return True
            else:
                self._log(f"OBS: Falha ao iniciar transmissão. Código: {status_data.get('code')}. Resposta: {response}", "error")
                return False
        self._log(f"OBS: Falha ao iniciar transmissão (resposta inesperada). Resposta: {response}", "error")
        return False

    def stop_stream(self):
        self._log("OBS: Solicitando parar transmissão...", "info")
        response = self._send_request("StopStream")
        if response and response.get('op') == 7:
            status_data = response.get('d', {}).get('requestStatus', {})
            if status_data.get('code') == 100:
                self._log("OBS: Transmissão parada com sucesso.", "info")
                return True
            else:
                self._log(f"OBS: Falha ao parar transmissão. Código: {status_data.get('code')}. Resposta: {response}", "error")
                return False
        self._log(f"OBS: Falha ao parar transmissão (resposta inesperada). Resposta: {response}", "error")
        return False

    # set_source_render é mais complexo por precisar do sceneItemId.
    # Vamos adaptar set_scene_item_enabled_obs do código original.
    def set_source_visibility(self, scene_name, source_name, enabled):
        """Define a visibilidade de uma fonte em uma cena específica usando conexão persistente.
        Se scene_name=None, usa a cena de programa atual.
        """
        scene_display_name = scene_name if scene_name else "CENA ATUAL"
        self._log(f"OBS: Visibilidade de '{source_name}' em '{scene_display_name}' para {enabled}", "info")

        # Garantir conexão persistente
        if not self._ensure_persistent_ws():
            return False

        # Resolver cena efetiva
        effective_scene_name = scene_name
        if not effective_scene_name:
            effective_scene_name = self._get_current_program_scene()
            if not effective_scene_name:
                self._log("OBS: Não foi possível obter cena atual para SetSourceVisibility.", "error")
                return False
            self._log(f"OBS: Cena atual para SetSourceVisibility: {effective_scene_name}", "debug")

        # Tentar com cache, se falhar, invalidar e tentar novamente
        attempts = 2
        for attempt in range(attempts):
            scene_item_id = self._get_scene_item_id_cached(effective_scene_name, source_name)
            if scene_item_id is None:
                self._log(f"OBS: Fonte '{source_name}' não encontrada na cena '{effective_scene_name}'.", "error")
                return False

            req = self._ws_send_request(
                "SetSceneItemEnabled",
                {"sceneName": effective_scene_name, "sceneItemId": scene_item_id, "sceneItemEnabled": enabled}
            )

            # Sucesso pode vir sem requestStatus (protocolo 5.x); se vier, código 100 é OK
            if req is not None:
                status = req.get('d', {}).get('requestStatus')
                if (status is None) or (status.get('code') == 100):
                    self._log(f"OBS: Visibilidade de '{source_name}' em '{effective_scene_name}' definida para {enabled} com sucesso.", "info")
                    return True
                else:
                    self._log(f"OBS: Falha ao definir visibilidade (code={status.get('code')}, comment={status.get('comment')}). Tentando recarregar cache...", "warning")
            else:
                self._log("OBS: Resposta None ao definir visibilidade. Tentando recarregar cache...", "warning")

            # Se chegou aqui, invalida cache e tenta novamente
            self._invalidate_scene_cache(effective_scene_name)

        self._log(f"OBS: Não foi possível definir visibilidade de '{source_name}' em '{effective_scene_name}'.", "error")
        return False

    def toggle_mute(self, input_name):
        """Alterna o estado de mudo de uma fonte de áudio (input)."""
        self._log(f"OBS: Solicitando alternar mudo para input: {input_name}", "info")
        response = self._send_request("ToggleInputMute", {"inputName": input_name})
        # A resposta para ToggleInputMute retorna 'responseData': {'inputMuted': bool}
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            muted_state = response.get('d', {}).get('responseData', {}).get('inputMuted', None)
            if muted_state is not None:
                self._log(f"OBS: Mudo para '{input_name}' alternado. Novo estado: {'Mutado' if muted_state else 'Não Mutado'}.", "info")
            else:  # Sucesso, mas não obteve o estado
                self._log(f"OBS: Mudo para '{input_name}' alternado com sucesso (estado não retornado na resposta esperada).", "info")
            return True
        self._log(f"OBS: Falha ao alternar mudo para '{input_name}'. Resposta: {response}", "error")
        return False

    def get_record_status(self):
        """Verifica o status da gravação no OBS."""
        self._log("OBS: Verificando status da gravação...", "debug")
        response = self._send_request("GetRecordStatus")
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            status_data = response.get('d', {}).get('responseData', {})
            is_recording = status_data.get('outputActive', False)
            timecode = status_data.get('outputTimecode', 'N/A')
            duration_ms = status_data.get('outputDuration', 0)
            self._log(f"OBS: Status da gravação: {'Ativa' if is_recording else 'Inativa'}, Timecode: {timecode}, Duração: {duration_ms}ms", "debug")
            return is_recording, timecode, duration_ms
        else:
            self._log(f"OBS: Falha ao obter status da gravação. Resposta: {response}", "error")
            return False, "N/A", 0

    def get_scene_list(self):
        """Busca a lista de todas as cenas no OBS."""
        self._log("OBS: Buscando lista de cenas...", "debug")
        response = self._send_request("GetSceneList")
        scenes = []
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            scene_data = response.get('d', {}).get('responseData', {})
            # scenes é uma lista de objetos, cada um com sceneName e sceneIndex
            for scene_obj in scene_data.get('scenes', []):
                if scene_obj.get('sceneName'):
                    scenes.append(scene_obj['sceneName'])
            self._log(f"OBS: Lista de cenas obtida: {scenes}", "debug")
        else:
            self._log(f"OBS: Falha ao obter lista de cenas. Resposta: {response}", "error")
        return scenes

    def get_input_list(self, input_kind=None):
        """Busca a lista de todos os inputs (fontes) no OBS, opcionalmente filtrado por tipo (inputKind)."""
        self._log(f"OBS: Buscando lista de inputs (tipo: {input_kind if input_kind else 'todos'})...", "debug")
        request_data = {}
        if input_kind:
            request_data['inputKind'] = input_kind

        response = self._send_request("GetInputList", request_data)
        inputs = []
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            input_data_list = response.get('d', {}).get('responseData', {}).get('inputs', [])
            # input_data_list é uma lista de objetos, cada um com inputName, inputKind, etc.
            for input_obj in input_data_list:
                if input_obj.get('inputName'):
                    inputs.append(input_obj['inputName'])
            self._log(f"OBS: Lista de inputs obtida: {inputs}", "debug")
        else:
            self._log(f"OBS: Falha ao obter lista de inputs. Resposta: {response}", "error")
        return inputs

    def get_scene_item_list(self, scene_name):
        """Busca a lista de itens (fontes) em uma cena específica."""
        if not scene_name:
            self._log("OBS: Nome da cena não fornecido para get_scene_item_list.", "error")
            return []

        self._log(f"OBS: Buscando lista de itens para a cena '{scene_name}'...", "debug")
        response = self._send_request("GetSceneItemList", {"sceneName": scene_name})
        items = []
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            scene_item_data = response.get('d', {}).get('responseData', {})
            # sceneItems é uma lista de objetos, cada um com sourceName, sceneItemId, etc.
            for item_obj in scene_item_data.get('sceneItems', []):
                if item_obj.get('sourceName'):
                    items.append(item_obj['sourceName'])
            self._log(f"OBS: Lista de itens para '{scene_name}' obtida: {items}", "debug")
        else:
            self._log(f"OBS: Falha ao obter lista de itens para '{scene_name}'. Resposta: {response}", "error")
        return items

    def check_connection(self):
        """Verifica a conexão com o OBS tentando obter a versão."""
        self._log("OBS: Testando conexão...", "info")
        response = self._send_request("GetVersion")
        if response and response.get('d', {}).get('requestStatus', {}).get('code') == 100:
            version_data = response.get('d', {}).get('responseData', {})
            obs_version = version_data.get('obsVersion', 'N/A')
            ws_version = version_data.get('obsWebSocketVersion', 'N/A')
            self._log(f"OBS: Conexão bem-sucedida. Versão OBS: {obs_version}, Versão WebSocket: {ws_version}", "success")
            return True, f"Conectado! OBS: {obs_version}, WS: {ws_version}"
        else:
            error_message = f"OBS: Falha ao testar conexão. Resposta: {response}"
            self._log(error_message, "error")
            return False, error_message
