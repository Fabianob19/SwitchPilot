import requests
import xml.etree.ElementTree as ET

class VMixController:
    def __init__(self, host="localhost", port="8088"):
        self.host = host
        self.port = port
        self.log_callback = None

    def set_log_callback(self, callback):
        self.log_callback = callback

    def _log(self, message, level="info"):
        if self.log_callback:
            self.log_callback(f"[VMixController] {message}", level)
        else:
            print(f"[VMixController - {level.upper()}]: {message}")

    def _send_request(self, function_name, params=None):
        """
        Envia uma requisição para a API HTTP do vMix.
        Args:
            function_name (str): O nome da função da API vMix (ex: "StartStopRecording").
            params (dict, optional): Dicionário de parâmetros adicionais para a função 
                                     (ex: {"Input": "1", "Value": "My Text"}).
        Returns:
            requests.Response object or None if an error occurred.
        """
        if not self.host or not self.port:
            self._log("Host ou Porta do vMix não configurados.", "error")
            return None

        base_url = f"http://{self.host}:{self.port}/api/"
        
        request_params = {"Function": function_name}
        if params:
            request_params.update(params)
        
        try:
            self._log(f"Enviando para vMix: Function={function_name}, Params={params if params else '{}'}", "debug")
            response = requests.get(base_url, params=request_params, timeout=5) # Timeout de 5 segundos
            response.raise_for_status()  # Levanta HTTPError para respostas ruins (4xx ou 5xx)
            
            # vMix geralmente retorna 200 OK mesmo para comandos que não fazem nada se a sintaxe estiver correta.
            # O conteúdo da resposta (XML) precisaria ser verificado para erros lógicos específicos do vMix.
            self._log(f"vMix Resposta (Status {response.status_code}): {response.text[:200]}...", "debug") # Logar início da resposta
            return response
        except requests.exceptions.Timeout:
            self._log(f"Timeout ao conectar/enviar para vMix API em {base_url} com params {request_params}", "error")
            return None
        except requests.exceptions.ConnectionError as e:
            self._log(f"Erro de conexão com vMix API em {base_url}: {e}", "error")
            return None
        except requests.exceptions.HTTPError as e:
            self._log(f"Erro HTTP do vMix API: {e}. Resposta: {e.response.text if e.response else 'N/A'}", "error")
            return None
        except requests.exceptions.RequestException as e:
            self._log(f"Erro genérico de requisição para vMix API: {e}", "error")
            return None
        return None

    def check_connection(self):
        """Verifica a conexão com o vMix tentando obter a versão (raiz da API)."""
        self._log("vMix: Testando conexão...", "info")
        # Acessar a raiz da API /api/ retorna um XML com a versão e outras infos.
        if not self.host or not self.port:
            self._log("Host ou Porta do vMix não configurados para teste.", "error")
            return False, "Host/Porta não configurados."
        
        base_url = f"http://{self.host}:{self.port}/api/"
        try:
            response = requests.get(base_url, timeout=3)
            response.raise_for_status()
            # Se chegou aqui, a conexão foi bem sucedida e o vMix respondeu.
            # Poderíamos parsear o XML para pegar a versão, mas para um teste de conexão, 200 OK é suficiente.
            # Exemplo de como pegar a versão do XML (requer biblioteca como xml.etree.ElementTree):
            # import xml.etree.ElementTree as ET
            # tree = ET.fromstring(response.content)
            # version = tree.find('version').text
            # self._log(f"vMix: Conexão bem-sucedida. Versão vMix: {version}", "success")
            # return True, f"Conectado! vMix Versão: {version}"
            
            self._log(f"vMix: Conexão bem-sucedida (Status {response.status_code}).", "success")
            return True, f"Conectado! vMix respondeu de {self.host}:{self.port}."

        except requests.exceptions.Timeout:
            self._log(f"Timeout ao testar conexão com vMix API em {base_url}", "error")
            return False, f"Timeout ({base_url})"
        except requests.exceptions.ConnectionError as e:
            self._log(f"Erro de conexão ao testar vMix API em {base_url}: {e}", "error")
            return False, f"Erro de Conexão ({base_url})"
        except requests.exceptions.HTTPError as e:
            self._log(f"Erro HTTP ao testar vMix API: {e}. Resposta: {e.response.text if e.response else 'N/A'}", "error")
            return False, f"Erro HTTP: {e.response.status_code if e.response else 'N/A'} ({base_url})"
        except requests.exceptions.RequestException as e:
            self._log(f"Erro genérico de requisição ao testar vMix API: {e}", "error")
            return False, f"Erro de Requisição ({base_url})"
        return False, "Falha desconhecida no teste de conexão vMix."

    def get_inputs_list(self):
        """Busca e retorna uma lista dos títulos dos inputs no vMix."""
        self._log("vMix: Buscando lista de inputs...", "debug")
        if not self.host or not self.port:
            self._log("Host ou Porta do vMix não configurados para buscar inputs.", "error")
            return []

        base_url = f"http://{self.host}:{self.port}/api/"
        inputs_list = []
        try:
            response = requests.get(base_url, timeout=5) # Timeout um pouco maior para XML potencialmente grande
            response.raise_for_status()
            
            # Parsear o XML
            xml_root = ET.fromstring(response.content)
            inputs_element = xml_root.find("inputs")
            if inputs_element is not None:
                for input_node in inputs_element.findall("input"):
                    title = input_node.get("title")
                    if title:
                        inputs_list.append(title)
            
            if not inputs_list:
                self._log("Nenhum input encontrado no XML do vMix ou XML malformado.", "debug")
            else:
                self._log(f"vMix: {len(inputs_list)} inputs encontrados: {inputs_list[:5]}...", "debug") # Logar alguns
            return inputs_list

        except requests.exceptions.Timeout:
            self._log(f"Timeout ao buscar lista de inputs do vMix API em {base_url}", "error")
        except requests.exceptions.ConnectionError as e:
            self._log(f"Erro de conexão ao buscar inputs do vMix API em {base_url}: {e}", "error")
        except requests.exceptions.HTTPError as e:
            self._log(f"Erro HTTP ao buscar inputs do vMix API: {e}. Resposta: {e.response.text if e.response else 'N/A'}", "error")
        except ET.ParseError as e:
            self._log(f"Erro ao parsear XML da lista de inputs do vMix: {e}", "error")
        except requests.exceptions.RequestException as e:
            self._log(f"Erro genérico de requisição ao buscar inputs do vMix API: {e}", "error")
        return [] # Retorna lista vazia em caso de erro

    # --- Métodos de Ação Específicos ---
    def set_text(self, input_name_or_key, selected_name_or_index="SelectedName", value=""):
        """
        Define o texto de um elemento Title/GT.
        Args:
            input_name_or_key (str): Nome ou chave do Input (ex: "MeuTitulo.xaml" ou UUID).
            selected_name_or_index (str): Nome do campo de texto no Title (ex: "NomeConvidado.Text") 
                                         ou índice do campo de texto (ex: "0" para o primeiro).
                                         Padrão "SelectedName" para o campo selecionado no editor de títulos do vMix.
            value (str): O texto a ser definido.
        """
        params = {
            "Input": input_name_or_key,
            "SelectedName": selected_name_or_index, # Ou pode ser um índice como "0", "1"
            "Value": value
        }
        response = self._send_request("SetText", params)
        # A resposta para SetText bem-sucedido é geralmente apenas um 200 OK com XML simples.
        # Precisaríamos de uma lógica mais robusta para confirmar o sucesso se necessário.
        if response and response.status_code == 200:
            self._log(f"SetText para Input='{input_name_or_key}', Campo='{selected_name_or_index}' com Valor='{value}' enviado.", "info")
            return True
        else:
            self._log(f"Falha ao enviar SetText para Input='{input_name_or_key}'. Resposta: {response.text if response else 'Nenhuma'}", "error")
            return False

    def start_recording(self):
        response = self._send_request("StartRecording")
        if response and response.status_code == 200:
            self._log("Comando StartRecording enviado.", "info")
            return True
        return False

    def stop_recording(self):
        response = self._send_request("StopRecording")
        if response and response.status_code == 200:
            self._log("Comando StopRecording enviado.", "info")
            return True
        return False

    def fade(self, input_key_or_name=None, duration_ms=500):
        params = {"Duration": duration_ms}
        if input_key_or_name:
            params["Input"] = input_key_or_name
        response = self._send_request("Fade", params)
        if response and response.status_code == 200:
            self._log(f"Comando Fade (Duração: {duration_ms}ms, Input: {input_key_or_name if input_key_or_name else 'Preview/Program'}) enviado.", "info")
            return True
        return False
        
    def cut(self, input_key_or_name=None):
        params = {}
        if input_key_or_name:
            params["Input"] = input_key_or_name
        response = self._send_request("Cut", params)
        if response and response.status_code == 200:
            self._log(f"Comando Cut (Input: {input_key_or_name if input_key_or_name else 'Preview/Program'}) enviado.", "info")
            return True
        return False

    def overlay_input_in(self, overlay_channel=1, input_key_or_name=None):
        # Lógica simplificada para overlay_input_in
        # Se input_key_or_name é fornecido, define esse input para o canal de overlay e o ativa.
        # Se não, apenas ativa o que já está configurado para o canal de overlay.
        if input_key_or_name:
            # API: Function=OverlayInput, Input=<nome_do_input>, Value=<numero_do_overlay>
            final_params = {"Input": input_key_or_name, "Value": overlay_channel}
            response = self._send_request("OverlayInput", final_params)
        else:
            # API: Function=OverlayInputIn, Input=<numero_do_overlay>
            final_params = {"Input": overlay_channel}
            response = self._send_request("OverlayInputIn", final_params)
            
        if response and response.status_code == 200:
            self._log(f"Comando para Overlay {overlay_channel} (Input: {input_key_or_name if input_key_or_name else 'Atual'}) enviado.", "info")
            return True
        return False

    def overlay_input_out(self, overlay_channel=1):
        response = self._send_request(f"OverlayInput{overlay_channel}Out")
        if response and response.status_code == 200:
            self._log(f"Comando OverlayInput{overlay_channel}Out enviado.", "info")
            return True
        return False

    # Adicionar outros métodos conforme necessário: 
    # start_streaming, stop_streaming, set_volume, etc. 