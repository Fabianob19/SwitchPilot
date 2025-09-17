from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QLineEdit, QPushButton, QDialogButtonBox, QFormLayout, QFrame, QSpacerItem, QSizePolicy, QWidget, QListWidget, QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt

class ActionConfigDialog(QDialog):
    def __init__(self, reference_data, main_controller, parent=None):
        super().__init__(parent)
        # Remover botão de ajuda ('?') do título
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.reference_data = reference_data
        self.main_controller = main_controller
        
        self.action_config_list = list(reference_data.get('actions', [])) 
        self.current_editing_action_index = -1 
        self.active_param_layout = None 

        self.setWindowTitle(f"Configurar Ações para: {reference_data.get('name', 'Referência')}")
        self.setMinimumWidth(700) 
        self.setMinimumHeight(500)

        self._setup_ui()
        self._load_actions_into_list_widget() 
        if self.action_config_list: 
            self.actions_list_widget.setCurrentRow(0)
        else: 
            self._prepare_for_new_action_creation()


    def _setup_ui(self):
        final_dialog_layout = QVBoxLayout()
        columns_layout = QHBoxLayout()

        left_column_layout = QVBoxLayout()
        list_management_frame = QFrame()
        list_management_layout = QVBoxLayout(list_management_frame)
        list_label = QLabel("Ações Configuradas:")
        list_management_layout.addWidget(list_label)
        self.actions_list_widget = QListWidget()
        self.actions_list_widget.setMinimumWidth(250)
        list_management_layout.addWidget(self.actions_list_widget)
        action_buttons_layout = QHBoxLayout()
        self.add_action_button = QPushButton("Adicionar Nova")
        self.remove_action_button = QPushButton("Remover Selecionada")
        self.remove_action_button.setEnabled(False)
        action_buttons_layout.addWidget(self.add_action_button)
        action_buttons_layout.addWidget(self.remove_action_button)
        list_management_layout.addLayout(action_buttons_layout)
        left_column_layout.addWidget(list_management_frame)
        columns_layout.addLayout(left_column_layout, 1)

        right_column_layout = QVBoxLayout()
        self.config_form_frame = QFrame()
        self.config_form_frame.setObjectName("actionConfigFormFrame")
        form_layout = QFormLayout(self.config_form_frame)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(15, 15, 15, 15)
        self.integration_label = QLabel("Integração:")
        self.integration_combo = QComboBox()
        self.integration_combo.addItems(["Selecione...", "OBS Studio", "vMix"])
        form_layout.addRow(self.integration_label, self.integration_combo)
        self.action_type_label = QLabel("Tipo de Ação:")
        self.action_type_combo = QComboBox()
        self.action_type_combo.setEnabled(False)
        form_layout.addRow(self.action_type_label, self.action_type_combo)
        right_column_layout.addWidget(self.config_form_frame)
        self.params_frame = QFrame()
        self.params_frame.setObjectName("actionParamsFrame")
        self.params_layout = QVBoxLayout()
        self.params_frame.setLayout(self.params_layout)
        self.params_frame.setVisible(False)
        right_column_layout.addWidget(self.params_frame)
        right_column_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.save_current_action_button = QPushButton("Aplicar Mudanças à Ação")
        self.save_current_action_button.setEnabled(False)
        right_column_layout.addWidget(self.save_current_action_button)
        columns_layout.addLayout(right_column_layout, 2)

        final_dialog_layout.addLayout(columns_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        final_dialog_layout.addWidget(self.button_box)
        self.setLayout(final_dialog_layout)

        self.button_box.accepted.connect(self._on_dialog_accept) 
        self.button_box.rejected.connect(self.reject)
        self.integration_combo.currentIndexChanged.connect(self._on_integration_changed)
        self.action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        self.actions_list_widget.currentItemChanged.connect(self._on_actions_list_selection_changed)
        self.add_action_button.clicked.connect(self._handle_add_new_action_button_clicked)
        self.remove_action_button.clicked.connect(self._handle_remove_action_button_clicked)
        self.save_current_action_button.clicked.connect(self._handle_save_current_action_button_clicked)

    def _prepare_for_new_action_creation(self):
        self.actions_list_widget.clearSelection()
        self.current_editing_action_index = -1
        self.integration_combo.setCurrentIndex(0)
        self.action_type_combo.clear()
        self.action_type_combo.setEnabled(False)
        self._clear_params_widgets()
        self.params_frame.setVisible(False)
        self.save_current_action_button.setEnabled(False)

    def _load_actions_into_list_widget(self):
        self.actions_list_widget.clear()
        for idx, action_data in enumerate(self.action_config_list):
            integration = action_data.get('integration', 'N/A')
            action_type = action_data.get('action_type', 'N/A')
            summary_parts = [f"{integration}: {action_type}"]
            params = action_data.get('params', {})
            if params:
                param_summary = []
                if 'scene_name' in params: param_summary.append(f"'{params['scene_name']}'")
                
                # vMix specific summary
                if integration == "vMix":
                    if 'input_key' in params and params['input_key'] is not None:
                        # Try to find the friendly name for the input_key
                        input_name_display = f"Input Key: {params['input_key']}" # Fallback
                        if self.main_controller and self.main_controller.vmix_controller:
                            try:
                                inputs = self.main_controller.vmix_controller.get_inputs_list()
                                found_input = next((inp for inp in inputs if inp['key'] == params['input_key']), None)
                                if found_input:
                                    input_name_display = f"Input: {found_input['number']}: {found_input['title']}"
                            except Exception:
                                pass # Stick to fallback
                        param_summary.append(input_name_display)
                    elif 'input' in params : # Fallback for older or generic "input" param if input_key is not used/present
                        param_summary.append(f"Input: '{params['input']}'")

                    if 'mix_index' in params:
                        mix_map = {0: "Preview", 1: "Program", 2: "Mix 2", 3: "Mix 3", 4: "Mix 4"}
                        mix_display = mix_map.get(params['mix_index'], f"Mix {params['mix_index']}")
                        param_summary.append(f"Para: {mix_display}")

                # OBS Specific (or other integrations if added)
                elif 'input_name' in params: param_summary.append(f"Input: '{params['input_name']}'")


                if 'item_name' in params: param_summary.append(f"Fonte: '{params['item_name']}'")
                if 'function_name' in params: param_summary.append(f"Func: '{params['function_name']}'")
                # Add other vMix specific params to summary if needed
                if 'selected_name' in params : param_summary.append(f"Campo: '{params['selected_name']}'")
                if 'text_value' in params : param_summary.append(f"Valor: '{params['text_value'][:20]}...'")


                if param_summary:
                    summary_parts.append(f"({' | '.join(param_summary)})") # Changed separator for clarity
            item_text = " ".join(summary_parts)
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, idx) 
            self.actions_list_widget.addItem(list_item)

    def _on_actions_list_selection_changed(self, current_item, previous_item):
        if current_item:
            stored_index = current_item.data(Qt.UserRole)
            if isinstance(stored_index, int) and 0 <= stored_index < len(self.action_config_list):
                self._load_action_for_editing(stored_index)
                self.remove_action_button.setEnabled(True)
            else: 
                self._prepare_for_new_action_creation()
                self.remove_action_button.setEnabled(False)
        else: 
            self._prepare_for_new_action_creation()
            self.remove_action_button.setEnabled(False)

    def _load_action_for_editing(self, index_in_config_list):
        if not (0 <= index_in_config_list < len(self.action_config_list)):
            self._prepare_for_new_action_creation()
            return

        self.current_editing_action_index = index_in_config_list
        action_data = self.action_config_list[index_in_config_list]
        integration = action_data.get('integration')
        action_type = action_data.get('action_type')
        params = action_data.get('params', {})

        integration_idx = self.integration_combo.findText(integration)
        if integration_idx != -1:
            self.integration_combo.setCurrentIndex(integration_idx) 
        else:
            self.integration_combo.setCurrentIndex(0) 

        action_type_idx = self.action_type_combo.findText(action_type)
        if action_type_idx != -1:
            self.action_type_combo.setCurrentIndex(action_type_idx) 
        else:
            self.action_type_combo.setCurrentIndex(0) if self.action_type_combo.count() > 0 else None
            self._clear_params_widgets()
            self.params_frame.setVisible(False)
        
        self._fill_param_fields(params) 
        self.save_current_action_button.setEnabled(True) 

    def _handle_add_new_action_button_clicked(self):
        self._prepare_for_new_action_creation()
        self.integration_combo.setFocus()

    def _handle_remove_action_button_clicked(self):
        current_item = self.actions_list_widget.currentItem()
        if not current_item:
            return

        selected_original_index = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(self, 'Remover Ação', 
                                     "Tem certeza que quer remover a ação selecionada?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if 0 <= selected_original_index < len(self.action_config_list):
                del self.action_config_list[selected_original_index]
                self._load_actions_into_list_widget() 
                if self.action_config_list:
                    new_index_to_select = min(selected_original_index, len(self.action_config_list) - 1)
                    if new_index_to_select >= 0:
                         self.actions_list_widget.setCurrentRow(new_index_to_select)
                    else: 
                        self._prepare_for_new_action_creation()
                else: 
                    self._prepare_for_new_action_creation()

    def _handle_save_current_action_button_clicked(self):
        current_integration = self.integration_combo.currentText()
        current_action_type = self.action_type_combo.currentText()

        if current_integration == "Selecione..." or current_action_type == "Selecione...":
            QMessageBox.warning(self, "Configuração Incompleta", 
                                "Por favor, selecione uma integração e um tipo de ação válidos.")
            return

        params = self.get_current_action_params() 
        action_details = {
            'integration': current_integration,
            'action_type': current_action_type,
            'params': params
        }

        if self.current_editing_action_index == -1: 
            self.action_config_list.append(action_details)
            self.current_editing_action_index = len(self.action_config_list) - 1 
        elif 0 <= self.current_editing_action_index < len(self.action_config_list): 
            self.action_config_list[self.current_editing_action_index] = action_details
        else:
            QMessageBox.critical(self, "Erro", "Estado de edição inválido. Não foi possível salvar a ação.")
            return

        self._load_actions_into_list_widget() 
        if self.current_editing_action_index >= 0 :
            self.actions_list_widget.setCurrentRow(self.current_editing_action_index)
        
        self.save_current_action_button.setEnabled(True) 


    def _on_integration_changed(self, index):
        self.action_type_combo.clear()
        self.action_type_combo.setEnabled(False)
        self._clear_params_widgets() 
        self.params_frame.setVisible(False)

        integration = self.integration_combo.itemText(index)
        if integration == "OBS Studio":
            self.action_type_combo.addItems([
                "Selecione...", "Trocar Cena", "Iniciar Gravação", "Parar Gravação", 
                "Iniciar Streaming", "Parar Streaming", "Alternar Mudo (Fonte de Áudio)",
                "Definir Visibilidade da Fonte"
            ])
            self.action_type_combo.setEnabled(True)
        elif integration == "vMix":
            self.action_type_combo.addItems([
                "Selecione...", 
                "Function (Genérico)", 
                "SetText", 
                "StartRecording", 
                "StopRecording", 
                "Fade", 
                "Cut",
                "OverlayInputIn", 
                "OverlayInputOut"
            ])
            self.action_type_combo.setEnabled(True)

    def _on_action_type_changed(self, index):
        self._clear_params_widgets()
        self.params_frame.setVisible(False)
        self.save_current_action_button.setEnabled(False)

        # DEBUG: Verificar valores recebidos
        current_integration = self.integration_combo.currentText()
        action_name = self.action_type_combo.itemText(index)
        current_action_index = self.action_type_combo.currentIndex()
        print(f"DEBUG: _on_action_type_changed - Index: {index}, Integration: '{current_integration}', ActionName: '{action_name}', ActionIndex: {current_action_index}")

        if not action_name or action_name == "Nenhuma" or action_name == "Selecione..." or current_action_index == 0: 
            print(f"DEBUG: _on_action_type_changed - Retornando prematuramente. ActionName: '{action_name}', Index: {current_action_index}")
            return

        print(f"DEBUG: _on_action_type_changed - Prosseguindo para criar layout para '{action_name}'")
        self.active_param_layout = QFormLayout()
        self.active_param_layout.setSpacing(8)
        self.current_param_widgets = {} 

        if self.integration_combo.currentText() == "OBS Studio":
            if action_name == "Trocar Cena":
                scenes_combo = QComboBox()
                scenes_combo.setObjectName("param_scene_name")
                self._populate_obs_scenes_combo(scenes_combo)
                self._add_param_control("Nome da Cena:", scenes_combo)

            elif action_name == "Definir Visibilidade da Fonte": 
                scenes_combo = QComboBox() 
                scenes_combo.setObjectName("param_scene_name_for_item") 
                self._populate_obs_scenes_combo(scenes_combo)
                self._add_param_control("Cena da Fonte:", scenes_combo)

                source_items_combo = QComboBox()
                source_items_combo.setObjectName("param_item_name")
                self._add_param_control("Nome da Fonte na Cena:", source_items_combo)

                visibility_combo = QComboBox()
                visibility_combo.setObjectName("param_visible")
                visibility_combo.addItems(["Visível", "Oculto"])
                self._add_param_control("Estado da Visibilidade:", visibility_combo)

                scenes_combo.currentTextChanged.connect(
                    lambda scene_name: self._populate_obs_scene_items_combo(scene_name, source_items_combo)
                )
                if scenes_combo.count() > 0 and scenes_combo.currentText() not in ["Nenhuma cena encontrada", "Erro ao carregar cenas", "Controlador OBS não disponível"]:
                    self._populate_obs_scene_items_combo(scenes_combo.currentText(), source_items_combo)
                else:
                    source_items_combo.clear() 
                    source_items_combo.setEnabled(False)

            elif action_name == "Alternar Mudo (Fonte de Áudio)":
                audio_input_combo = QComboBox()
                audio_input_combo.setObjectName("param_input_name") 
                self._populate_obs_inputs_combo(audio_input_combo) 
                self._add_param_control("Fonte de Áudio:", audio_input_combo)
            
            elif action_name == "Iniciar/Parar Gravação":
                pass
            elif action_name == "Iniciar/Parar Streaming":
                pass

        elif self.integration_combo.currentText() == "vMix":
            if action_name == "Function (Genérico)":
                input_label = QLabel("Input vMix (Opcional):")
                input_combo = QComboBox()
                input_combo.setObjectName("param_vmix_input")
                self._populate_vmix_inputs_combo(input_combo, add_none_option=True)
                self.active_param_layout.addRow(input_label, input_combo)

                self._add_param_control("Nome da Função (API)", "function_name", "Ex: StartRecording, SetText")
                self._add_param_control("Valor (Opcional)", "vmix_value", "Ex: True, 00:05:00, Texto aqui")
                self._add_param_control("Duração (ms, Opcional)", "vmix_duration", "Ex: 1000")
                
                mix_target_label = QLabel("Alvo do Mix (Opcional):")
                mix_target_combo = QComboBox()
                mix_target_combo.setObjectName("param_vmix_mix_target")
                mix_options = ["Nenhum", "Program", "Mix 2", "Mix 3", "Mix 4"]
                mix_target_combo.addItems(mix_options)
                self.active_param_layout.addRow(mix_target_label, mix_target_combo)

            elif action_name == "SetText":
                input_label_st = QLabel("Input (Título/GT):")
                input_combo_st = QComboBox()
                input_combo_st.setObjectName("param_vmix_input_settext")
                self._populate_vmix_inputs_combo(input_combo_st, add_none_option=False)
                self.active_param_layout.addRow(input_label_st, input_combo_st)

                self._add_param_control("Nome do Campo/Índice", "selected_name", "Ex: Headline.Text ou 0")
                self._add_param_control("Valor do Texto", "text_value", "O texto a ser definido")

            elif action_name == "StartRecording" or action_name == "StopRecording": 
                pass 

            elif action_name == "Fade": 
                input_combo = QComboBox()
                input_combo.setObjectName("param_vmix_input_for_fade")
                self._populate_vmix_inputs_combo(input_combo, add_none_option=True)
                self._add_param_control("Input Alvo (Opcional):", input_combo)

                duration_edit = QLineEdit()
                duration_edit.setObjectName("param_vmix_duration_for_fade")
                self._add_param_control("Duração (ms):", duration_edit, "Ex: 1000")

                mix_combo = QComboBox()
                mix_combo.setObjectName("param_mix_index")
                mix_combo.addItem("Program (Mix 1)", 1)
                mix_combo.addItem("Preview (Mix 0)", 0)
                mix_combo.addItem("Mix 2", 2)
                mix_combo.addItem("Mix 3", 3)
                mix_combo.addItem("Mix 4", 4)
                self._add_param_control("Enviar para Mix:", mix_combo)


            elif action_name == "Cut": 
                print(f"DEBUG: vMix Cut action selected. Creating controls.") # DEBUG
                input_combo = QComboBox()
                input_combo.setObjectName("param_vmix_input_for_cut")
                self._populate_vmix_inputs_combo(input_combo, add_none_option=True)
                self._add_param_control("Input Alvo (Opcional):", input_combo)

                print(f"DEBUG: vMix Cut - Adding mix_combo...") # DEBUG
                mix_combo = QComboBox()
                mix_combo.setObjectName("param_mix_index")
                mix_combo.addItem("Program (Mix 1)", 1)
                mix_combo.addItem("Preview (Mix 0)", 0)
                mix_combo.addItem("Mix 2", 2)
                mix_combo.addItem("Mix 3", 3)
                mix_combo.addItem("Mix 4", 4)
                self._add_param_control("Enviar para Mix:", mix_combo)
                print(f"DEBUG: vMix Cut - mix_combo added to layout attempt.") # DEBUG

            elif action_name == "OverlayInputIn": 
                overlay_channel_edit = QLineEdit()
                overlay_channel_edit.setObjectName("param_overlay_channel")
                self._add_param_control("Número do Canal Overlay:", overlay_channel_edit, "Ex: 1, 2, ...")

                input_combo = QComboBox()
                input_combo.setObjectName("param_vmix_input_for_overlay")
                self._populate_vmix_inputs_combo(input_combo, add_none_option=False)
                self._add_param_control("Input para Overlay:", input_combo)
            
            elif action_name == "OverlayInputOut": 
                overlay_channel_edit = QLineEdit() 
                overlay_channel_edit.setObjectName("param_overlay_channel") 
                self._add_param_control("Número do Canal Overlay:", overlay_channel_edit, "Ex: 1, 2, ...")

        if self.active_param_layout.rowCount() > 0:
            self.params_layout.addLayout(self.active_param_layout)
            self.params_frame.setVisible(True)
            self.save_current_action_button.setEnabled(True)
        else:
            # Esta parte é para ações sem parâmetros, ou se nenhum widget foi adicionado
            if action_name and action_name != "Nenhuma" and self.action_type_combo.currentIndex() > 0:
                # Permite salvar mesmo sem params_frame visível (ex: StartRecording)
                self.save_current_action_button.setEnabled(True) 
            else:
                self.save_current_action_button.setEnabled(False)
            self.params_frame.setVisible(False) # Oculta se não há linhas no layout ativo

    def _add_param_control(self, label_text, widget_or_param_key, placeholder_text_or_default_value=""):
        print(f"DEBUG: _add_param_control called for Label: '{label_text}'") # DEBUG
        label_widget = QLabel(label_text)
        control_widget = None
        if isinstance(widget_or_param_key, QWidget): 
            control_widget = widget_or_param_key
        else: 
            param_key_for_object_name = str(widget_or_param_key) 
            line_edit = QLineEdit()
            if placeholder_text_or_default_value:
                 line_edit.setPlaceholderText(str(placeholder_text_or_default_value))
            line_edit.setObjectName(f"param_{param_key_for_object_name}") 
            control_widget = line_edit
        
        if self.active_param_layout is not None and isinstance(self.active_param_layout, QFormLayout):
            self.active_param_layout.addRow(label_widget, control_widget)
            if control_widget.objectName():
                self.current_param_widgets[control_widget.objectName()] = control_widget
        else:
            pass 

    def _clear_params_widgets(self):
        if self.active_param_layout is not None:
            self.params_layout.removeItem(self.active_param_layout)
            for i in reversed(range(self.active_param_layout.rowCount())):
                field_item = self.active_param_layout.itemAt(i, QFormLayout.FieldRole)
                if field_item:
                    widget = field_item.widget()
                    if widget:
                        widget.deleteLater()
                label_item = self.active_param_layout.itemAt(i, QFormLayout.LabelRole)
                if label_item:
                    widget = label_item.widget()
                    if widget:
                        widget.deleteLater()
            self.active_param_layout.deleteLater()
            self.active_param_layout = None
        self.current_param_widgets = {} 
        self.params_frame.setVisible(False) 

    def _populate_obs_scenes_combo(self, combo_box):
        combo_box.clear()
        if self.main_controller and self.main_controller.obs_controller:
            try:
                scenes = self.main_controller.obs_controller.get_scene_list()
                if scenes:
                    combo_box.addItems(scenes)
                else:
                    combo_box.addItem("Nenhuma cena encontrada")
                    combo_box.setEnabled(False)
            except Exception as e:
                combo_box.addItem("Erro ao carregar cenas")
                combo_box.setEnabled(False)
        else:
            combo_box.addItem("Controlador OBS não disponível")
            combo_box.setEnabled(False)

    def _populate_obs_inputs_combo(self, combo_box, input_kind=None):
        combo_box.clear()
        if self.main_controller and self.main_controller.obs_controller:
            try:
                inputs = self.main_controller.obs_controller.get_input_list(input_kind=input_kind)
                if inputs:
                    combo_box.addItems(inputs)
                else:
                    combo_box.addItem(f"Nenhum input {'do tipo ' + input_kind if input_kind else ''} encontrado")
                    combo_box.setEnabled(False)
            except Exception as e:
                combo_box.addItem("Erro ao carregar inputs")
                combo_box.setEnabled(False)
        else:
            combo_box.addItem("Controlador OBS não disponível")
            combo_box.setEnabled(False)

    def _populate_obs_scene_items_combo(self, scene_name, combo_box):
        combo_box.clear()
        combo_box.setEnabled(True) 

        if not scene_name or scene_name == "Nenhuma cena encontrada" or scene_name == "Erro ao carregar cenas" or scene_name == "Controlador OBS não disponível":
            combo_box.addItem("Selecione uma cena válida primeiro")
            combo_box.setEnabled(False)
            return

        if self.main_controller and self.main_controller.obs_controller:
            try:
                items = self.main_controller.obs_controller.get_scene_item_list(scene_name)
                if items:
                    combo_box.addItems(items)
                else:
                    combo_box.addItem(f"Nenhum item em '{scene_name}'")
            except Exception as e:
                combo_box.addItem("Erro ao carregar itens")
                combo_box.setEnabled(False)
        else:
            combo_box.addItem("Controlador OBS não disponível")
            combo_box.setEnabled(False)
            
    def _fill_param_fields(self, params):
        if self.active_param_layout is None or not isinstance(self.active_param_layout, QFormLayout):
            if not params: 
                self.params_frame.setVisible(False)
            else: 
                self.params_frame.setVisible(False) 
            return

        if not params: 
            self.params_frame.setVisible(self.active_param_layout.rowCount() > 0) 
            self.save_current_action_button.setEnabled(self.current_editing_action_index != -1 or \
                                                       (self.integration_combo.currentIndex() > 0 and \
                                                        self.action_type_combo.currentIndex() > 0))
            return

        for i in range(self.active_param_layout.rowCount()):
            field_item = self.active_param_layout.itemAt(i, QFormLayout.FieldRole)
            if field_item:
                control_widget = field_item.widget()
                if control_widget:
                    param_key_full = control_widget.objectName() 
                    if param_key_full and param_key_full.startswith("param_"):
                        param_key_short = param_key_full[len("param_"):] 
                        
                        value_to_set = params.get(param_key_short)

                        if value_to_set is None: # Se o parâmetro não existir nos dados salvos, não tenta definir
                            if param_key_short == "mix_index" and isinstance(control_widget, QComboBox): # Default mix_index to 1 (Program)
                                combo_idx = control_widget.findData(1)
                                if combo_idx != -1:
                                    control_widget.setCurrentIndex(combo_idx)
                            continue

                        if isinstance(control_widget, QLineEdit):
                            control_widget.setText(str(value_to_set))
                        elif isinstance(control_widget, QComboBox):
                            # Primeiro, tentar encontrar pelo UserData (que deve ser a "key" para inputs vMix)
                            data_idx = -1
                            if param_key_short in ["vmix_input", "vmix_input_settext"]: # Campos que armazenam vMix input key
                                for i in range(control_widget.count()):
                                    if control_widget.itemData(i) == value_to_set: # value_to_set aqui é a input_key
                                        data_idx = i
                                        break
                            
                            if data_idx != -1:
                                control_widget.setCurrentIndex(data_idx)
                            else:
                                # Fallback para texto, ou para campos que não usam UserData da mesma forma
                                text_to_select = str(value_to_set) # valor padrão para texto
                                if param_key_short == "mix_index": # Para mix_index, value_to_set é o índice numérico
                                    mix_map_from_index = {0: "Program", 1: "Mix 2", 2: "Mix 3", 3: "Mix 4"}
                                    text_to_select = mix_map_from_index.get(value_to_set, "Nenhum")
                                
                                combo_idx = control_widget.findText(text_to_select)
                                if combo_idx != -1:
                                    control_widget.setCurrentIndex(combo_idx)
                                elif param_key_short in ["vmix_input", "vmix_input_settext"] and value_to_set is None:
                                    # Se a chave do input armazenada for None, selecionar a opção "Nenhum"
                                    for i_text_none in range(control_widget.count()):
                                        if control_widget.itemData(i_text_none) is None:
                                            control_widget.setCurrentIndex(i_text_none)
                                            break
                        elif param_key_short == "visible": # OBS specific
                            text_to_select = "Visível" if str(value_to_set).lower() == "true" else "Oculto"
                            combo_idx = control_widget.findText(text_to_select)
                            if combo_idx != -1:
                                control_widget.setCurrentIndex(combo_idx)
                        elif param_key_short == "input_key": # vMix input key
                            combo_idx = control_widget.findData(value_to_set) # Find by UserData (key)
                            if combo_idx == -1 and value_to_set is None: # if key is None, select the "None" option
                                 combo_idx = control_widget.findData(None) # Assumes "None" option has userData=None
                            if combo_idx != -1:
                                control_widget.setCurrentIndex(combo_idx)
                            else:
                                # Fallback for OBS scene/item names if not found, or other text-based combos
                                if control_widget.isEditable():
                                    control_widget.setEditText(str(value_to_set))
                                elif param_key_short == "input_key" and value_to_set is None: 
                                    # If input_key is None and "None" option not found by findData(None)
                                    # try to find by text like "Nenhum" or "Padrão"
                                    for i_text in range(control_widget.count()):
                                        if control_widget.itemText(i_text).lower().startswith(("nenhum", "padrão", "preview/program")):
                                            control_widget.setCurrentIndex(i_text)
                                            break
                                elif param_key_short == "mix_index": # Default if not found
                                     default_mix_idx = control_widget.findData(1) # Try to select Program (Mix 1)
                                     if default_mix_idx != -1: control_widget.setCurrentIndex(default_mix_idx)

        self.params_frame.setVisible(self.active_param_layout.rowCount() > 0)
        self.save_current_action_button.setEnabled(True) 

    def _on_dialog_accept(self): 
        self.accept()

    def get_action_config(self): 
        return self.action_config_list

    def get_current_action_params(self):
        params = {}
        integration = self.integration_combo.currentText()
        action_type = self.action_type_combo.currentText()

        if integration == "OBS Studio":
            if action_type == "Trocar Cena":
                scene_combo = self.findChild(QComboBox, "param_scene_name")
                if scene_combo:
                    params["scene_name"] = scene_combo.currentText()
            
            elif action_type in ["Iniciar Gravação", "Parar Gravação", "Iniciar Streaming", "Parar Streaming"]:
                pass 
            
            elif action_type == "Alternar Mudo (Fonte de Áudio)":
                input_combo = self.findChild(QComboBox, "param_input_name")
                if input_combo:
                    params["input_name"] = input_combo.currentText()

            elif action_type == "Definir Visibilidade da Fonte":
                scene_combo = self.findChild(QComboBox, "param_scene_name_for_item") 
                item_combo = self.findChild(QComboBox, "param_item_name") 
                visibility_combo = self.findChild(QComboBox, "param_visible") 

                if scene_combo:
                    params["scene_name_for_item"] = scene_combo.currentText()
                if item_combo:
                    params["item_name"] = item_combo.currentText()
                if visibility_combo: 
                    params["visible"] = "true" if visibility_combo.currentText() == "Visível" else "false"
        
        elif integration == "vMix":
            if action_type == "Function (Genérico)":
                fn_name_edit = self.findChild(QLineEdit, "param_function_name")
                if fn_name_edit: params["function_name"] = fn_name_edit.text().strip()
                
                input_combo = self.findChild(QComboBox, "param_vmix_input") 
                if input_combo and input_combo.currentIndex() >= 0:
                    input_key = input_combo.currentData() # Pega o UserData (key do input)
                    if input_key: # Somente se não for "Nenhum" (que tem UserData=None)
                        params["vmix_input"] = input_key 
                
                value_edit = self.findChild(QLineEdit, "param_vmix_value") 
                if value_edit: 
                    val = value_edit.text().strip()
                    if val: params["vmix_value"] = val
                
                duration_edit = self.findChild(QLineEdit, "param_vmix_duration") 
                if duration_edit: 
                    val = duration_edit.text().strip()
                    if val: params["vmix_duration"] = val

                mix_target_combo = self.findChild(QComboBox, "param_vmix_mix_target")
                if mix_target_combo:
                    mix_text = mix_target_combo.currentText()
                    # Mapeamento: "Program": 0, "Mix 2": 1, "Mix 3": 2, "Mix 4": 3. "Nenhum" não adiciona o param.
                    mix_map_to_index = {"Program": 0, "Mix 2": 1, "Mix 3": 2, "Mix 4": 3}
                    if mix_text in mix_map_to_index:
                        params["mix_index"] = mix_map_to_index[mix_text]
            
            elif action_type == "SetText":
                input_combo_st = self.findChild(QComboBox, "param_vmix_input_settext")
                if input_combo_st and input_combo_st.currentIndex() >= 0:
                    input_key = input_combo_st.currentData()
                    if input_key: # Deve sempre haver um input selecionado aqui (add_none_option=False)
                        params["vmix_input"] = input_key
                    else:
                        # Tratar caso onde, apesar de add_none_option=False, algo deu errado.
                        # Idealmente, logar ou mostrar um erro ao usuário se input_key for None aqui.
                        pass 

                selected_name_edit = self.findChild(QLineEdit, "param_selected_name")
                if selected_name_edit: params["selected_name"] = selected_name_edit.text().strip()
                
                text_value_edit = self.findChild(QLineEdit, "param_text_value")
                if text_value_edit: params["text_value"] = text_value_edit.text().strip()

            elif action_type in ["StartRecording", "StopRecording"]:
                pass 

            elif action_type == "Fade":
                input_combo = self.findChild(QComboBox, "param_vmix_input_for_fade") 
                if input_combo: 
                    input_key = input_combo.currentData()
                    if input_key is not None:
                        params["vmix_input_for_fade"] = input_key
                
                duration_edit = self.findChild(QLineEdit, "param_vmix_duration_for_fade") 
                if duration_edit: 
                    val = duration_edit.text().strip()
                    if val: params["vmix_duration_for_fade"] = val

                mix_combo = self.findChild(QComboBox, "param_mix_index")
                if mix_combo:
                    mix_data = mix_combo.currentData()
                    if mix_data is not None:
                        params["mix_index"] = mix_data

            elif action_type == "Cut":
                input_combo = self.findChild(QComboBox, "param_vmix_input_for_cut") 
                if input_combo: 
                    input_key = input_combo.currentData()
                    if input_key is not None:
                        params["vmix_input_for_cut"] = input_key

                mix_combo = self.findChild(QComboBox, "param_mix_index")
                if mix_combo:
                    mix_data = mix_combo.currentData()
                    if mix_data is not None:
                        params["mix_index"] = mix_data

            elif action_type == "OverlayInputIn": 
                channel_edit = self.findChild(QLineEdit, "param_overlay_channel") 
                if channel_edit: 
                    val = channel_edit.text().strip()
                    if val: params["overlay_channel"] = val
                
                input_combo = self.findChild(QComboBox, "param_vmix_input_for_overlay") 
                if input_combo: 
                    input_key = input_combo.currentData()
                    if input_key is not None:
                        params["vmix_input_for_overlay"] = input_key
            
            elif action_type == "OverlayInputOut":
                channel_edit = self.findChild(QLineEdit, "param_overlay_channel") 
                if channel_edit: 
                    val = channel_edit.text().strip()
                    if val: params["overlay_channel"] = val
        return params

    def _populate_vmix_inputs_combo(self, combo_box, add_none_option=True):
        """Popula o QComboBox fornecido com os inputs do vMix."""
        if not (self.main_controller and self.main_controller.vmix_controller):
            combo_box.clear()
            combo_box.addItem("vMix não conectado ou indisponível")
            combo_box.setEnabled(False)
            return

        try:
            inputs = self.main_controller.vmix_controller.get_inputs_list()
            combo_box.clear()
            combo_box.setEnabled(True)

            if add_none_option:
                combo_box.addItem("Nenhum (ou Preview/Program)", None) # UserData None ou especial

            if not inputs:
                # Adicionar mensagem mesmo se estiver conectado mas não houver inputs
                # ou se a lista retornada for vazia (o que get_inputs_list faz em caso de erro também)
                no_inputs_msg = "Nenhum input encontrado no vMix"
                if not self.main_controller.vmix_controller.check_connection()[0]: # Verifica novamente a conexão
                    no_inputs_msg = "vMix não conectado"
                combo_box.addItem(no_inputs_msg, None) 
                combo_box.setEnabled(len(inputs) > 0) # Habilita só se houver inputs reais
                return

            for vmix_input in inputs:
                # Usar title para display e key para userData.
                # Algumas funções vMix podem preferir 'number' ou 'title' como input.
                # Por agora, 'key' (GUID) é o mais específico.
                # Ou poderíamos armazenar o dict completo: vmix_input
                combo_box.addItem(f"{vmix_input['number']}: {vmix_input['title']} (Tipo: {vmix_input.get('type', 'N/A')})", vmix_input['key'])
            
            # Se após popular, apenas a opção "Nenhum" e/ou mensagens de erro estiverem presentes,
            # e não houver inputs reais, talvez desabilitar.
            # A lógica acima já tenta lidar com isso ao setar combo_box.setEnabled(len(inputs) > 0)
            # mas é preciso cuidado se add_none_option = True.
            # Se add_none_option e inputs estiver vazio, count será 1.
            # Se add_none_option e inputs não estiver vazio, count > 1.
            if combo_box.count() == 0 : # Se absolutamente nada foi adicionado
                 combo_box.addItem("Falha ao carregar inputs", None)
                 combo_box.setEnabled(False)
            elif combo_box.count() == 1 and add_none_option and combo_box.itemData(0) is None: # Apenas "Nenhum"
                # Poderia ser útil manter habilitado para permitir selecionar "Nenhum"
                pass


        except Exception as e:
            combo_box.clear()
            combo_box.addItem(f"Erro ao carregar inputs: {e}", None)
            combo_box.setEnabled(False)
            # Logar o erro também seria bom
            if self.main_controller and hasattr(self.main_controller, '_log'):
                 self.main_controller._log(f"ActionConfigDialog: Erro ao popular inputs vMix: {e}", "error")
            else:
                print(f"ActionConfigDialog: Erro ao popular inputs vMix: {e}")
            