import websocket
import json
import uuid
import base64
import hashlib
from PyQt5.QtCore import QSettings # Para ler a senha como no código original por enquanto
import time # Adicionado para os sleeps nos testes

class OBSController:
    def __init__(self, host='localhost', port='4455', password=''):
        self.host = host
        self.port = port
        self.password = password # Senha fornecida na inicialização
        # self.ws = None # Não vamos manter uma conexão persistente por enquanto
        self.log_callback = None

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
        return '' # Retorna string vazia se self.password não foi setada

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
                    # Mesmo que não consigamos gerar a auth string, ainda podemos tentar o IDENTIFY sem ela,
                    # pois authenticationRequired pode ser false. Mas se o OBS espera, vai falhar.
                    # Para ser seguro, se challenge/salt estão lá e não temos senha, é um erro de configuração.
                    # No entanto, o servidor pode aceitar um identify sem auth string se authRequired for false.
                    # Vamos prosseguir e enviar o identify sem a auth string, mas logar o aviso severo.
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

    def _send_request(self, request_type, request_data={}):
        """Conecta, autentica, envia uma requisição e retorna a resposta."""
        ws = None
        try:
            self._log(f"OBS (_send_request): Conectando a ws://{self.host}:{self.port}", "debug")
            ws = websocket.create_connection(f"ws://{self.host}:{self.port}", timeout=3)
            self._log(f"OBS (_send_request): Conexão WebSocket criada.", "debug")
            
            if not self._authenticate(ws):
                self._log("OBS (_send_request): Autenticação FALHOU. Retornando None.", "error") 
                if ws: ws.close()
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
            response_str = "" # Inicializar para o caso de erro antes da atribuição

            while time.time() < deadline:
                try:
                    # O recv() da biblioteca websocket-client é bloqueante.
                    # O timeout da conexão (3s no create_connection) pode ou não se aplicar aqui.
                    # Este loop com deadline é uma camada adicional de segurança contra bloqueio indefinido.
                    
                    # Calcular o tempo restante para uma eventual chamada com timeout (se a lib suportasse por chamada)
                    # remaining_time_for_recv = deadline - time.time()
                    # if remaining_time_for_recv <= 0:
                    #     self._log(f"OBS (_send_request): Timeout (deadline) atingido antes de chamar recv() para reqId {request_id}.", "error")
                    #     # O finally cuidará de fechar o ws, não precisa retornar aqui se o finally estiver fora do loop
                    #     break # Sai do while, resultando em timeout geral

                    response_str = ws.recv() 
                    self._log(f"OBS (_send_request): Resposta BRUTA recebida: {response_str[:250]}...", "debug") # Log um pouco maior
                    
                    parsed_response = json.loads(response_str)
                    op_code = parsed_response.get("op")

                    if op_code == 7: # RequestResponse
                        if parsed_response.get("d", {}).get("requestId") == request_id:
                            self._log(f"OBS (_send_request): Resposta op:7 com requestId ({request_id}) correspondente recebida.", "debug")
                            # Não fechar ws aqui, o finally fará isso ao retornar.
                            return parsed_response 
                        else:
                            self._log(f"OBS (_send_request): Resposta op:7 com requestId diferente. Esperado: {request_id}, Recebido: {parsed_response.get('d', {}).get('requestId')}. Ignorando.", "warning")
                            # Continuar no loop while para esperar a resposta correta ou timeout
                    elif op_code == 5: # Event
                        self._log(f"OBS (_send_request): Evento op:5 (type: {parsed_response.get('d', {}).get('eventType')}) recebido e ignorado enquanto esperava reqId {request_id}.", "debug")
                        # Continuar no loop while
                    elif op_code == 0: # Hello (não deveria acontecer depois da autenticação)
                        self._log(f"OBS (_send_request): Mensagem Hello (op:0) recebida inesperadamente enquanto esperava reqId {request_id}. Ignorando.", "warning")
                    elif op_code == 2: # Identified (não deveria acontecer depois da autenticação)
                        self._log(f"OBS (_send_request): Mensagem Identified (op:2) recebida inesperadamente enquanto esperava reqId {request_id}. Ignorando.", "warning")
                    else:
                        self._log(f"OBS (_send_request): op_code {op_code} inesperado recebido. Ignorando. Resposta: {parsed_response}", "warning")
                
                except websocket.WebSocketTimeoutException as e_timeout: 
                    # Este except só seria atingido se o timeout do create_connection se aplicasse ao recv
                    # e expirasse durante uma chamada ws.recv().
                    self._log(f"OBS (_send_request): WebSocketTimeoutException no recv() para reqId {request_id}: {e_timeout}. Continuando a tentar até o deadline.", "warning")
                    # O loop while com deadline externo é a principal proteção de timeout.
                    if time.time() >= deadline: # Verificar se o deadline geral também foi atingido
                        break
                    continue # Tentar receber novamente dentro do deadline
                except json.JSONDecodeError as e_json:
                    raw_response_for_log = response_str if response_str else "N/A" 
                    self._log(f"Erro ao decodificar JSON da resposta OBS em _send_request (loop) para reqId {request_id}: {e_json}. Resposta bruta: '{raw_response_for_log[:250]}...'.", "error")
                    # Continuar no loop while, pode ser um pacote corrompido e o próximo ser bom.
                except websocket.WebSocketConnectionClosedException as e_closed:
                    self._log(f"OBS (_send_request): Conexão WebSocket fechada inesperadamente (reqId {request_id}): {e_closed}", "error")
                    return None # Sair do loop e da função, o finally fechará o ws se ainda existir.
                except Exception as e_recv: 
                    self._log(f"OBS (_send_request): Exceção no recv() (loop) para reqId {request_id}: {e_recv}. Resposta: {response_str[:250] if response_str else 'N/A'}...", "error")
                    return None # Sair por segurança, o finally fechará o ws.

            # Se sair do loop while por causa do deadline
            self._log(f"OBS (_send_request): TIMEOUT GERAL ({operation_timeout_seconds}s) esperando pela resposta op:7 para requestId {request_id}.", "error")
            return None # O finally fechará o ws.

        except websocket.WebSocketBadStatusException as e_bad_status:
            self._log(f"Erro de status ao conectar/enviar para OBS em ws://{self.host}:{self.port}: {e_bad_status}", "error")
            if ws: ws.close()
            return None
        except ConnectionRefusedError:
            self._log(f"Conexão recusada pelo OBS em ws://{self.host}:{self.port} (dentro de _send_request). OBS aberto e WebSocket ativo? Retornando None.", "error")
            if ws: ws.close()
            return None
        except Exception as e:
            self._log(f"Erro genérico em _send_request para '{request_type}': {e}. Retornando None.", "error")
            if ws: ws.close()
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
        """Define a visibilidade de uma fonte em uma cena específica (se scene_name=None, usa a atual)."""
        scene_display_name = scene_name if scene_name else "CENA ATUAL"
        self._log(f"OBS: Visibilidade de '{source_name}' em '{scene_display_name}' para {enabled}", "info")
        ws = None
        try:
            self._log(f"OBS: Conectando (para SetSourceVisibility) a ws://{self.host}:{self.port}", "debug")
            ws = websocket.create_connection(f"ws://{self.host}:{self.port}", timeout=3)
            
            if not self._authenticate(ws):
                if ws: ws.close()
                return False

            effective_scene_name = scene_name
            if not effective_scene_name:
                req_id_current_scene = str(uuid.uuid4())
                payload_current_scene = {"op": 6, "d": {"requestType": "GetCurrentProgramScene", "requestId": req_id_current_scene}}
                ws.send(json.dumps(payload_current_scene))
                resp_current_scene_str = ws.recv()
                self._log(f"OBS GetCurrentProgramScene RESPOSTA: {resp_current_scene_str}", "debug")
                resp_current_scene = json.loads(resp_current_scene_str)
                effective_scene_name = resp_current_scene.get('d', {}).get('responseData', {}).get('currentProgramSceneName')
                if not effective_scene_name:
                    self._log("OBS: Não foi possível obter cena atual para SetSourceVisibility.", "error")
                    if ws: ws.close()
                    return False
                self._log(f"OBS: Cena atual para SetSourceVisibility: {effective_scene_name}", "debug")

            req_id_list = str(uuid.uuid4())
            payload_list = {"op": 6, "d": {"requestType": "GetSceneItemList", "requestData": {"sceneName": effective_scene_name}, "requestId": req_id_list}}
            ws.send(json.dumps(payload_list))
            resp_list_str = ws.recv()
            self._log(f"OBS GetSceneItemList para '{effective_scene_name}' RESPOSTA: {resp_list_str}", "debug")
            resp_list = json.loads(resp_list_str)
            
            scene_item_id = None
            scene_items = resp_list.get('d', {}).get('responseData', {}).get('sceneItems', [])
            for item in scene_items:
                if item.get('sourceName') == source_name:
                    scene_item_id = item.get('sceneItemId')
                    break
            
            if scene_item_id is None:
                self._log(f"OBS: Fonte '{source_name}' não encontrada na cena '{effective_scene_name}'.", "error")
                if ws: ws.close()
                return False

            req_id_set = str(uuid.uuid4())
            payload_set = {"op": 6, "d": {
                "requestType": "SetSceneItemEnabled", 
                "requestData": {"sceneName": effective_scene_name, "sceneItemId": scene_item_id, "sceneItemEnabled": enabled}, 
                "requestId": req_id_set
            }}
            ws.send(json.dumps(payload_set))
            resp_set_str = ws.recv()
            self._log(f"OBS SetSceneItemEnabled para '{source_name}' RESPOSTA: {resp_set_str}", "debug")
            resp_set = json.loads(resp_set_str)
            
            # Verificar o status da resposta do SetSceneItemEnabled
            # A resposta para SetSceneItemEnabled não tem um 'requestStatus' como outras, 
            # é apenas um op 7 (RequestResponse) sem 'responseData' se bem sucedido.
            # Um erro retornaria um 'requestStatus' com 'code' != 100.
            # Para simplificar, vamos assumir sucesso se não houver erro explícito.
            # OBS WS Protocol: "If a request was successful, requestStatus will NOT be present."
            # Então, se requestStatus não está lá, é sucesso. Se está, verificamos o código.
            status_data = resp_set.get('d', {}).get('requestStatus', {})
            if not status_data: # Sem requestStatus significa sucesso
                 self._log(f"OBS: Visibilidade de '{source_name}' em '{effective_scene_name}' definida para {enabled} com sucesso.", "info")
                 success = True
            elif status_data.get('code') == 100: # Código 100 também é sucesso
                 self._log(f"OBS: Visibilidade de '{source_name}' em '{effective_scene_name}' definida para {enabled} com sucesso (código 100).", "info")
                 success = True
            else:
                 self._log(f"OBS: Falha ao definir visibilidade de '{source_name}'. Código: {status_data.get('code')}, Comentário: {status_data.get('comment')}", "error")
                 success = False
            
            if ws: ws.close()
            return success

        except websocket.WebSocketTimeoutException:
            self._log(f"Timeout durante SetSourceVisibility para OBS em ws://{self.host}:{self.port}", "error")
            if ws: ws.close()
            return False
        except ConnectionRefusedError:
            self._log(f"Conexão recusada pelo OBS (SetSourceVisibility) em ws://{self.host}:{self.port}. OBS aberto e WebSocket ativo?", "error")
            if ws: ws.close()
            return False
        except Exception as e:
            self._log(f"Erro durante SetSourceVisibility para OBS: {e}", "error")
            if ws: ws.close()
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
            else: # Sucesso, mas não obteve o estado
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