"""
NFR Elicitation Assistant - Unified Chat Interface
===================================================
Main chatbot interface with integrated menu functions

FIXED VERSION - All logic matches menu_windows.py exactly
"""

import sys
import threading
import json
import re
from typing import Optional, Dict, List, Tuple
from collections import defaultdict
import inspect

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QFrame, QTextEdit, QLineEdit,
    QScrollArea, QSizePolicy, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, Slot, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QColor, QTextCursor, QTextCharFormat

# Import from same directory (flat structure)
import metamodel
from nfr_queries import getEntity, getEntityName, getChildren, getDecompositionsFor, getClaimsFor
from classifier_v6 import classify_fr_nfr, classify_nfr_type, classify_fr_type
from menu_llm import MenuLLM
import ollama
from utils import format_entity_name, fuzzy_match_entity


# ============================================================================
# CHAT MESSAGE WIDGET
# ============================================================================

class ChatMessage(QFrame):
    """A single message in the chat (user or assistant)"""
    
    # Signal emitted when a pipeline button is clicked
    button_clicked = Signal(str, str)  # (button_action, button_label)
    
    def __init__(self, sender: str, message: str, buttons: List[Dict] = None, parent=None):
        """
        Args:
            sender: "user" or "assistant"
            message: The text content
            buttons: List of button dicts: [{"label": "...", "action": "...", "data": {...}}]
        """
        super().__init__(parent)
        self.sender = sender
        self.message_text = message
        self.buttons = buttons or []
        self.button_widgets = []  # Keep reference to button widgets
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup message appearance"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        
        # Message styling based on sender
        if self.sender == "user":
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #E3F2FD;
                    border: 1px solid #90CAF9;
                    border-radius: 10px;
                    margin: 5px 50px 5px 10px;
                }
            """)
            sender_label = QLabel("👤 You:")
            sender_label.setStyleSheet("font-weight: bold; color: #1976D2; font-size: 11pt;")
        else:  # assistant
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #F5F5F5;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                    margin: 5px 10px 5px 50px;
                }
            """)
            sender_label = QLabel("🤖 Assistant:")
            sender_label.setStyleSheet("font-weight: bold; color: #424242; font-size: 11pt;")
        
        layout.addWidget(sender_label)
        
        # Message content
        message_label = QLabel(self.message_text)
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.PlainText)
        message_label.setStyleSheet("""
            font-size: 12pt;
            color: #333;
            line-height: 1.5;
            padding: 5px;
        """)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # Add buttons if any
        if self.buttons:
            # Use grid layout for wrapping buttons
            button_layout = QGridLayout()
            button_layout.setSpacing(10)
            button_layout.setColumnStretch(3, 1)  # Make last column stretch
            
            # Add buttons with wrapping (3 per row)
            for i, btn_data in enumerate(self.buttons):
                row = i // 3
                col = i % 3
                btn = QPushButton(btn_data["label"])
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        font-size: 11pt;
                        font-weight: bold;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 15px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #1565C0;
                    }
                """)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumHeight(35)
                
                # Store button data and connect click
                btn.setProperty("action", btn_data["action"])
                btn.setProperty("button_data", btn_data.get("data", {}))
                #btn.clicked.connect(lambda: self._on_button_click(btn))
                btn.clicked.connect(lambda checked, b=btn: self._on_button_click(b))
                self.button_widgets.append(btn)
                button_layout.addWidget(btn, row, col)
            layout.addLayout(button_layout)
    
    def _on_button_click(self, button):
        """Handle button click - emit signal and hide button"""
        action = button.property("action")
        label = button.text()
        
        # Hide the button
        button.setVisible(False)
        
        # Emit signal for parent to handle
        self.button_clicked.emit(action, label)
    
    def hide_all_buttons(self):
        """Hide all buttons in this message"""
        for btn in self.button_widgets:
            btn.setVisible(False)


# ============================================================================
# INPUT DIALOG FOR MENU ITEMS
# ============================================================================

class InputDialog(QDialog):
    """Simple dialog to get user input for menu items"""
    
    def __init__(self, prompt: str, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Required")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Prompt label
        label = QLabel(prompt)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 12pt; color: #333; margin-bottom: 10px;")
        layout.addWidget(label)
        
        # Input field
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setMinimumHeight(100)
        self.input_field.setMaximumHeight(150)
        self.input_field.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        layout.addWidget(self.input_field)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 11pt;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Submit")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 11pt;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def get_input(self) -> str:
        """Get the input text"""
        return self.input_field.toPlainText().strip()


# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

class ChatInterface(QMainWindow):
    """Main unified chat interface with integrated menu functions"""
    
    # Signals for thread-safe UI updates
    update_ui_signal = Signal(object, str, list)  # (old_msg, text, buttons)
    update_thinking_signal = Signal(object, str)   # (old_msg, text) - no buttons
    add_message_signal = Signal(str, str, list)    # (sender, text, buttons) - add new message
    loading_status_signal = Signal(str)            # loading status text for title bar

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFR Elicitation Assistant - Chat Interface")
        self.setMinimumSize(1400, 900)

        # Initialize components
        self.menu_llm = None  # Initialize later
        self.chat_history = []  # List of ChatMessage widgets
        self.components_loaded = False
        self._model_ready = threading.Event()  # Signals when Ollama model is loaded

        # Connect signals to slots
        self.update_ui_signal.connect(self._update_with_buttons)
        self.update_thinking_signal.connect(self._update_thinking_message)
        self.add_message_signal.connect(self._add_message)
        self.loading_status_signal.connect(self._update_loading_status)

        # Setup UI
        self._setup_ui()

        # Load components in background (non-blocking)
        self._start_background_loading()
    
    def _setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title bar
        self._create_title_bar(main_layout)
        
        # Chat display area (scrollable)
        self._create_chat_area(main_layout)
        
        # Input box
        self._create_input_area(main_layout)
        
        # Menu buttons at bottom
        self._create_menu_buttons(main_layout)
    
    def _create_title_bar(self, parent_layout):
        """Create title bar"""
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("background-color: #1976D2; border-radius: 8px;")
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        title_label = QLabel("🤖 NFR Framework Assistant")
        title_label.setStyleSheet("""
            color: white;
            font-size: 16pt;
            font-weight: bold;
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()

        # Loading status label
        self.loading_label = QLabel("Loading AI model...")
        self.loading_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 10pt;
            font-style: italic;
            padding-right: 10px;
        """)
        title_layout.addWidget(self.loading_label)

        # Info button
        info_btn = QPushButton("ℹ️ Info")
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        info_btn.clicked.connect(self._show_info)
        title_layout.addWidget(info_btn)
        
        parent_layout.addWidget(title_bar)
    
    def _create_chat_area(self, parent_layout):
        """Create scrollable chat display area"""
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                background-color: white;
            }
        """)
        
        # Chat container
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(5)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        
        # Welcome message
        welcome_msg = ChatMessage(
            "assistant",
            "Welcome to the NFR Framework Assistant! 👋\n\n"
            "I can help you with:\n"
            "• Understanding NFR softgoals and their sub-softgoals (decompositions)\n"
            "• Providing sources through claims\n"
            "• Finding ways to achieve NFRs (operationalizations)\n"
            "• Exploring side effects of requirements\n"
            "• Show examples of essential concepts such as types of NFRs, NFR statements, operationalizing softgoals, etc.\n"
            "• Classifying requirements statements\n"
            "• And much more!\n\n"
            "Click a menu button below to get started, or type your question!"
        )
        self.chat_layout.addWidget(welcome_msg)
        self.chat_history.append(welcome_msg)
        
        scroll_area.setWidget(self.chat_container)
        parent_layout.addWidget(scroll_area, stretch=1)
        
        # Keep reference to scroll area for auto-scrolling
        self.scroll_area = scroll_area
    
    def _create_input_area(self, parent_layout):
        """Create input box and send button"""
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        # Input field
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        # Connect Enter key to send (Ctrl+Enter for newline)
        self.input_field.textChanged.connect(self._on_input_changed)
        input_layout.addWidget(self.input_field, stretch=1)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumWidth(100)
        self.send_btn.setMinimumHeight(60)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.clicked.connect(self._send_general_message)
        self.send_btn.setEnabled(False)
        input_layout.addWidget(self.send_btn)
        
        parent_layout.addWidget(input_container)
    
    def _create_menu_buttons(self, parent_layout):
        """Create 8 menu buttons at bottom in grid layout"""
        menu_container = QWidget()
        menu_container.setStyleSheet("""
            background-color: #FAFAFA;
            border: 2px solid #E0E0E0;
            border-radius: 8px;
        """)
        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(10, 10, 10, 10)
        
        # Label
        label = QLabel("🎯 Quick Actions:")
        label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #555;")
        menu_layout.addWidget(label)
        
        # Grid of buttons (2 rows x 4 columns)
        grid = QGridLayout()
        grid.setSpacing(8)
        
        menu_items = [
            {"icon": "📖", "label": "What's This?", "callback": self._menu_whats_this},
            {"icon": "🌳", "label": "Decompose", "callback": self._menu_decompose},
            {"icon": "🔧", "label": "Operationalize", "callback": self._menu_operationalize},
            {"icon": "⚡", "label": "Side Effects", "callback": self._menu_side_effects},
            {"icon": "📜", "label": "Claims", "callback": self._menu_claims},
            {"icon": "🎓", "label": "Domain Knowledge", "callback": self._menu_domain_knowledge},
            {"icon": "✅", "label": "Classify", "callback": self._menu_classify},
            {"icon": "📚", "label": "Browse", "callback": self._menu_browse},
        ]
        
        for i, item in enumerate(menu_items):
            row = i // 4
            col = i % 4
            
            btn = QPushButton(f"{item['icon']} {item['label']}")
            btn.setMinimumHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #333;
                    font-size: 11pt;
                    font-weight: bold;
                    border: 2px solid #E0E0E0;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: left;
                    padding-left: 15px;
                }
                QPushButton:hover {
                    background-color: #E3F2FD;
                    border: 2px solid #2196F3;
                }
                QPushButton:pressed {
                    background-color: #BBDEFB;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(item["callback"])
            grid.addWidget(btn, row, col)
        
        menu_layout.addLayout(grid)
        parent_layout.addWidget(menu_container)
    
    def _on_input_changed(self):
        """Enable/disable send button based on input"""
        has_text = bool(self.input_field.toPlainText().strip())
        self.send_btn.setEnabled(has_text)
    
    def _scroll_to_bottom(self):
        """Auto-scroll to bottom of chat"""
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    # User-facing prompt display strings (no metamodel/context references)
    _PROMPT_DISPLAY = {
        "define_entity": (
            "What is {user_input}? State what type of entity it is in requirements engineering. "
            "Provide a clear and concise explanation of what {user_input} is and why it matters. "
            "Make it so that even people who have no expert knowledge in the requirements engineering "
            "field can understand. Provide easy to understand examples."
        ),
        "decompose": (
            "An NFR softgoal can be decomposed into sub-softgoals. A decomposition helps define a "
            "softgoal, since it provides the components that makes up of the main softgoal. "
            "Decompose the {user_input} NFR softgoal."
        ),
        "show_operationalizations": (
            "Operationalizations are possible design alternatives for meeting or satisficing "
            "non-functional requirements in the system. "
            "List and explain all operationalizations for the {user_input} softgoal."
        ),
        "analyze_contributions": (
            "Every operationalization in the system can simultaneously have negative and positive "
            "effects on different non-functional requirements. Therefore, using one operationalization "
            "can help satisfice one NFR while hindering another. "
            "List each NFR the {user_input} operationalization affects, whether negatively or "
            "positively; analyze and list {user_input}'s trade-offs between NFRs."
        ),
    }

    def _get_prompt_display(self, action_type: str, user_input: str) -> str:
        """Get a clean user-facing prompt string (no metamodel/context references)."""
        template = self._PROMPT_DISPLAY.get(action_type)
        if not template:
            return user_input
        return template.format(user_input=user_input)
    
    @Slot(str, str, list)
    def _add_message(self, sender: str, message: str, buttons: List[Dict] = None) -> ChatMessage:
        """Add a message to the chat"""
        try:
            msg = ChatMessage(sender, message, buttons)
            
            # Connect button signals
            msg.button_clicked.connect(self._on_pipeline_button_click)
            
            self.chat_layout.addWidget(msg)
            self.chat_history.append(msg)
            self._scroll_to_bottom()
            
            return msg
            
        except Exception as e:
            print(f"Error in _add_message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _send_general_message(self):
        """Send a general chat message"""
        user_input = self.input_field.toPlainText().strip()
        if not user_input:
            return
        
        # Clear input
        self.input_field.clear()
        
        # Add user message
        self._add_message("user", user_input)
        
        # Show "thinking" indicator
        thinking_msg = self._add_message("assistant", "🤔 Thinking...")
        
        # Process in background thread
        def process():
            try:
                # Wait for model to be loaded
                self._model_ready.wait()

                # Call LLM for general chat
                response = ollama.chat(
                    model="llama3.1:8b",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for requirements engineering, with expertise in the NFR Framework."},
                        {"role": "user", "content": user_input}
                    ],
                    options={
                        "temperature": 0.7,
                        "num_predict": 500,
                    }
                )
                reply = response['message']['content']
                
                # Update UI
                self.update_thinking_signal.emit(thinking_msg, reply)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}\n\nPlease make sure Ollama is running:\n  ollama serve"
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    @Slot(object, str)
    def _update_thinking_message(self, msg: ChatMessage, new_text: str):
        """Update a thinking message with actual response"""
        try:
            # Remove the thinking message
            self.chat_layout.removeWidget(msg)
            msg.deleteLater()
            if msg in self.chat_history:
                self.chat_history.remove(msg)
            
            # Add actual response
            self._add_message("assistant", new_text)
            
        except Exception as e:
            print(f"Error in _update_thinking_message: {e}")
            import traceback
            traceback.print_exc()

    @Slot(str)
    def _update_loading_status(self, text: str):
        """Update the loading status label in the title bar"""
        self.loading_label.setText(text)

    def _on_pipeline_button_click(self, action: str, label: str):
        """Handle pipeline button clicks"""
        print(f"\n🔘 BUTTON CLICKED:")
        print(f"   Action: {action}")
        print(f"   Label: {label}")
        
        # Get the button that was clicked to access its data
        sender = self.sender()
        button_data = {}
        
        # Find the ChatMessage that contains this button
        # Must match BOTH action AND label (since multiple buttons can have same action)
        for msg in self.chat_history:
            if msg.sender == "assistant":
                for btn_widget in msg.button_widgets:
                    # Match both action AND label to get the correct button
                    if (btn_widget.property("action") == action and 
                        btn_widget.text() == label):
                        button_data = btn_widget.property("button_data")
                        print(f"   ✓ Found matching button: action={action}, label={label}")
                        print(f"   ✓ Button data: {button_data}")
                        break
        
        # Add user message showing the actual prompt (without context)
        if action == "whats_this":
            entity = button_data.get("entity", "")
            self._add_message("user", self._get_prompt_display("define_entity", entity))
            self._process_whats_this(entity)

        elif action == "decompose":
            entity = button_data.get("entity", "")
            self._add_message("user", self._get_prompt_display("decompose", entity))
            self._process_decompose(entity)

        elif action == "operationalize":
            entity = button_data.get("entity", "")
            self._add_message("user", self._get_prompt_display("show_operationalizations", entity))
            self._process_operationalize(entity)

        elif action == "side_effects":
            entity = button_data.get("entity", "")
            self._add_message("user", self._get_prompt_display("analyze_contributions", entity))
            self._process_side_effects(entity)
            
        
        elif action == "claims":
            entity = button_data.get("entity", "")
            prompt = f"Show claims for {entity}"
            self._add_message("user", prompt)
            self._process_claims(entity)
        
        elif action == "browse_category":
            category = button_data.get("category", "")
            prompt = f"Browse: {category}"
            self._add_message("user", prompt)
            self._process_browse_category(category)
        
        else:
            # Generic handling
            self._add_message("user", f"[{label}]")
            self._add_message("assistant", f"Processing: {action}")
    
    # ========================================================================
    # MENU BUTTON HANDLERS
    # ========================================================================
    
    def _menu_whats_this(self):
        """Handle 'What's This?' menu button"""
        dialog = InputDialog(
            "What would you like to know about?",
            "Enter an NFR type (e.g., 'Performance') or requirement text..."
        )
        
        if dialog.exec() == QDialog.Accepted:
            user_input = dialog.get_input()
            if not user_input:
                return
            
            # Add user message IMMEDIATELY (show actual prompt)
            self._add_message("user", self._get_prompt_display("define_entity", user_input))

            # Then process
            self._process_whats_this(user_input)
    
    def _process_whats_this(self, user_input: str):
        """Process What's This query - EXACT same logic as menu_windows.py"""
        thinking_msg = self._add_message("assistant", "📖 Looking up information...")

        def process():
            try:
                # Ensure MenuLLM is ready
                menu_llm = self._ensure_menu_llm()

                # EXACT same logic as menu_windows.py
                from nfr_queries import getEntity, whatIs

                text = user_input

                # Step 1: Fuzzy match
                matched_name, suggestion = fuzzy_match_entity(text)
                if not matched_name:
                    self.update_thinking_signal.emit(thinking_msg, suggestion)
                    return

                # Step 2: Get entity
                entity = getEntity(matched_name)
                if not entity:
                    error_msg = f"❌ Could not find entity: {text}\n\nTry: Softgoal, Performance, Security, Indexing, etc."
                    self.update_thinking_signal.emit(thinking_msg, error_msg)
                    return

                # Step 3: Get comprehensive info
                info = whatIs(entity, verbose=True)

                # Step 4: Call MenuLLM
                if menu_llm:
                    llm_response = menu_llm.respond(
                        action_type="define_entity",
                        user_input=text,
                        metamodel_context=info
                    )
                    final_response = llm_response
                else:
                    final_response = info

                # Step 5: Display in chat with buttons
                formatted_name = format_entity_name(matched_name)

                buttons = [
                    {"label": f"🌳 Decompose {formatted_name}", "action": "decompose", "data": {"entity": matched_name}},
                    {"label": f"🔧 How to achieve {formatted_name}?", "action": "operationalize", "data": {"entity": matched_name}},
                ]

                self.update_ui_signal.emit(thinking_msg, final_response, buttons)

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)

        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    @Slot(object, str, list)
    def _update_with_buttons(self, old_msg: ChatMessage, text: str, buttons: List[Dict]):
        """Replace a message with new text and buttons"""
        try:
            # Remove old message
            self.chat_layout.removeWidget(old_msg)
            old_msg.deleteLater()
            if old_msg in self.chat_history:
                self.chat_history.remove(old_msg)
            
            # Add new message with buttons
            self._add_message("assistant", text, buttons)
            
        except Exception as e:
            print(f"Error in _update_with_buttons: {e}")
            import traceback
            traceback.print_exc()
    
    def _menu_decompose(self):
        """Handle 'Decompose' menu button"""
        dialog = InputDialog(
            "What would you like to decompose?",
            "Enter an NFR type (e.g., 'Security', 'Performance')..."
        )
        
        if dialog.exec() == QDialog.Accepted:
            user_input = dialog.get_input()
            if not user_input:
                return
            
            self._add_message("user", self._get_prompt_display("decompose", user_input))
            self._process_decompose(user_input)
    
    def _process_decompose(self, user_input: str):
        """Process decomposition query - EXACT same logic as menu_windows.py"""
        thinking_msg = self._add_message("assistant", "🌳 Analyzing decomposition...")
        
        def process():
            try:
                # Ensure MenuLLM is ready
                menu_llm = self._ensure_menu_llm()
                
                # EXACT same logic as menu_windows.py DecompositionWindow
                matched_name, suggestion = fuzzy_match_entity(user_input)
                if not matched_name:
                    self.update_thinking_signal.emit(thinking_msg, suggestion)
                    return
                
                entity = getEntity(matched_name)
                decomps = getDecompositionsFor(entity)
                
                if not decomps:
                    response = f"ℹ️ {format_entity_name(matched_name)} has no decomposition methods defined."
                    self.update_thinking_signal.emit(thinking_msg, response)
                    return
                
                # Build context
                context = f"{format_entity_name(matched_name)} has {len(decomps)} decomposition method(s):\n\n"
                for i_decomp, decomp in enumerate(decomps, 1):
                    context += f"{i_decomp}. {decomp.name}\n"
                    if hasattr(decomp, 'offspring'):
                        offspring_names = [format_entity_name(o.__name__) for o in decomp.offspring]
                        context += f"   Offspring: {', '.join(offspring_names)}\n"
                    context += "\n"
                
                # Use MenuLLM
                llm_response = menu_llm.respond(
                    action_type="decompose",
                    user_input=format_entity_name(matched_name),
                    metamodel_context=context
                )
                full_response = llm_response

                # Add button for next pipeline step (to operationalize parent)
                formatted_name = format_entity_name(matched_name)
                buttons = [
                    {"label": f"🔧 How to achieve {formatted_name}?", "action": "operationalize", "data": {"entity": matched_name}},
                ]
                
                # Update UI
                self.update_ui_signal.emit(thinking_msg, full_response, buttons)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _menu_operationalize(self):
        """Handle 'Operationalize' menu button"""
        dialog = InputDialog(
            "How would you like to operationalize (achieve)?",
            "Enter an NFR type (e.g., 'Security', 'Performance')..."
        )
        
        if dialog.exec() == QDialog.Accepted:
            user_input = dialog.get_input()
            if not user_input:
                return
            
            self._add_message("user", self._get_prompt_display("show_operationalizations", user_input))
            self._process_operationalize(user_input)
    
    def _process_operationalize(self, user_input: str):
        """Process operationalization query - EXACT same logic as menu_windows.py OperationalizationWindow"""
        thinking_msg = self._add_message("assistant", "🔧 Finding techniques...")
        
        def process():
            try:
                # Ensure MenuLLM is ready
                menu_llm = self._ensure_menu_llm()
                
                # EXACT same logic as menu_windows.py OperationalizationDecompositionWindow.show_op_details()
                matched_name, suggestion = fuzzy_match_entity(user_input)
                if not matched_name:
                    self.update_thinking_signal.emit(thinking_msg, suggestion)
                    return
                
                entity = getEntity(matched_name)
                entity_name = getEntityName(entity)
                formatted_name = format_entity_name(entity_name)
                search_name = entity_name.replace('Type', '').replace('Softgoal', '')
                
                # Build list of entities to search for (entity + children + offspring)
                search_targets = [search_name]
                
                # Add children
                try:
                    children = getChildren(entity)
                    for child in children:
                        child_name = getEntityName(child).replace('Type', '').replace('Softgoal', '')
                        if child_name not in search_targets:
                            search_targets.append(child_name)
                except:
                    pass
                
                # Add decomposition offspring
                try:
                    decomps = getDecompositionsFor(entity)
                    for decomp in decomps:
                        if hasattr(decomp, 'offspring'):
                            for offspring in decomp.offspring:
                                offspring_name = getEntityName(offspring).replace('Type', '').replace('Softgoal', '')
                                if offspring_name not in search_targets:
                                    search_targets.append(offspring_name)
                except:
                    pass
                
                # Search metamodel for contributions to any of these targets
                # STRATEGY: Include operationalizations with at least one positive contribution,
                # but show ALL their contributions (positive and negative) for complete context
                positive_types = ['MAKE', 'HELP', 'SOME+']
                
                # Step 1: Find operationalizations that have at least one positive contribution
                ops_with_positive = set()
                all_contributions = []
                
                for name, obj in inspect.getmembers(metamodel):
                    if isinstance(obj, metamodel.Contribution):
                        target_match = any(obj.target.lower() == t.lower() for t in search_targets)
                        if target_match:
                            all_contributions.append((obj.source, obj.target, obj.type.value))
                            # Track if this operationalization has at least one positive
                            if obj.type.value in positive_types:
                                ops_with_positive.add(obj.source)
                
                # Step 2: Include ALL contributions from operationalizations that have at least one positive
                # Also verify entity names through fuzzy matching to avoid button mismatch issues
                contributions = []
                found_ops = []
                processed_sources = set()  # Track which raw sources we've already verified
                
                for source, target, effect in all_contributions:
                    if source in ops_with_positive:
                        contributions.append((source, target, effect))
                        # Only verify and add to found_ops once per unique source
                        if source not in processed_sources:
                            processed_sources.add(source)
                            # Verify this entity name exists through fuzzy matching
                            matched_name, _ = fuzzy_match_entity(source)
                            print(f"   Verified: '{source}' → '{matched_name}'")
                            if matched_name:
                                found_ops.append(matched_name)  # Use verified name
                            else:
                                found_ops.append(source)  # Fallback to raw name
                
                if not contributions:
                    response = f"ℹ️ No operationalizations found for '{formatted_name}'.\n\n"
                    response += "Try: Indexing→Performance, Encryption→Security, etc."
                    self.update_thinking_signal.emit(thinking_msg, response)
                    return
                
                # Build context for LLM
                context = f"{formatted_name} can be achieved by {len(contributions)} operationalization(s):\n\n"
                
                by_source = defaultdict(list)
                for source, target, effect in contributions:
                    by_source[source].append((target, effect))
                
                for source in sorted(by_source.keys()):
                    formatted_source = format_entity_name(source)
                    context += f"• {formatted_source} helps achieve:\n"
                    for target, effect in by_source[source]:
                        formatted_target = format_entity_name(target)
                        context += f"  - {formatted_target} ({effect})\n"
                    context += "\n"
                
                # Use MenuLLM
                llm_response = menu_llm.respond(
                    action_type="show_operationalizations",
                    user_input=formatted_name,
                    metamodel_context=context
                )
                full_response = llm_response

                # Add buttons for side effects for ALL operationalizations
                # Remove duplicates from found_ops first
                unique_ops = []
                seen = set()
                for op in found_ops:
                    if op not in seen:
                        seen.add(op)
                        unique_ops.append(op)
                
                print(f"\n🔘 DEBUG: found_ops = {found_ops}")
                print(f"🔘 DEBUG: found_ops length = {len(found_ops)}")
                print(f"🔘 DEBUG: unique_ops = {unique_ops}")
                print(f"🔘 DEBUG: unique count = {len(unique_ops)}")
                
                buttons = []
                for i, op in enumerate(unique_ops):  # Use deduplicated list
                    print(f"   Button {i}: op='{op}', type={type(op)}")
                    btn_label = f"⚡ Side effects of {op}"
                    btn_data = {"entity": op}
                    print(f"   Button {i}: label='{btn_label}', data={btn_data}")
                    buttons.append({
                        "label": btn_label,
                        "action": "side_effects",
                        "data": btn_data
                    })
                    print(f"   Button {i} added: {buttons[-1]}")
                
                
                # Add claims/justifications button
                buttons.append({
                    "label": "📜 View Claims/Justifications",
                    "action": "claims",
                    "data": {"entity": matched_name}
                })
                # Update UI
                self.update_ui_signal.emit(thinking_msg, full_response, buttons)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _menu_side_effects(self):
        """Handle 'Side Effects' menu button"""
        dialog = InputDialog(
            "Analyze side effects for which technique?",
            "Enter a technique (e.g., 'Encryption', 'Caching')..."
        )
        
        if dialog.exec() == QDialog.Accepted:
            user_input = dialog.get_input()
            if not user_input:
                return
            
            self._add_message("user", self._get_prompt_display("analyze_contributions", user_input))
            self._process_side_effects(user_input)
    
    def _process_side_effects(self, user_input: str):
        """Process side effects query - EXACT same logic as menu_windows.py SideEffectsWindow"""
        print(f"\n{'='*60}")
        print(f"SIDE EFFECTS DEBUG:")
        print(f"Input from button: '{user_input}'")
        print(f"{'='*60}")
        
        thinking_msg = self._add_message("assistant", "⚡ Analyzing contributions...")
        
        def process():
            try:
                # Ensure MenuLLM is ready
                menu_llm = self._ensure_menu_llm()
                
                # EXACT same logic as menu_windows.py SideEffectsWindow
                matched_name, suggestion = fuzzy_match_entity(user_input)
                print(f"Fuzzy matched to: '{matched_name}'")
                if not matched_name:
                    self.update_thinking_signal.emit(thinking_msg, suggestion)
                    return
                
                entity = getEntity(matched_name)
                entity_name = getEntityName(entity)
                formatted_name = format_entity_name(entity_name)
                search_name = entity_name.replace('Type', '').replace('Softgoal', '')
                
                # Search metamodel for contributions FROM this source
                contributions = []
                for name, obj in inspect.getmembers(metamodel):
                    if isinstance(obj, metamodel.Contribution):
                        # Check if this contribution comes FROM our entity
                        if obj.source.lower() == search_name.lower():
                            contributions.append((obj.target, obj.type.value))
                
                if not contributions:
                    response = f"ℹ️ No contribution information found for '{formatted_name}'."
                    self.update_thinking_signal.emit(thinking_msg, response)
                    return
                
                # Build context for LLM
                context = f"{formatted_name} has {len(contributions)} contribution(s):\n\n"
                
                by_type = defaultdict(list)
                for target, effect in contributions:
                    by_type[effect].append(target)
                
                for effect_type in sorted(by_type.keys()):
                    context += f"{effect_type}:\n"
                    for target in by_type[effect_type]:
                        formatted_target = format_entity_name(target)
                        context += f"  • {formatted_target}\n"
                    context += "\n"
                
                # Use MenuLLM
                llm_response = menu_llm.respond(
                    action_type="analyze_contributions",
                    user_input=formatted_name,
                    metamodel_context=context
                )
                # Update UI
                self.update_thinking_signal.emit(thinking_msg, llm_response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _menu_claims(self):
        """Handle 'Claims' menu button"""
        dialog = InputDialog(
            "Show claims/justifications for which NFR?",
            "Enter an NFR type (e.g., 'Security')..."
        )
        
        if dialog.exec() == QDialog.Accepted:
            user_input = dialog.get_input()
            if not user_input:
                return
            
            prompt = f"Show claims for {user_input}"
            self._add_message("user", prompt)
            self._process_claims(user_input)
    
    def _process_claims(self, user_input: str):
        """Process claims query - EXACT same logic as menu_windows.py ClaimSoftgoalsWindow"""
        thinking_msg = self._add_message("assistant", "📜 Looking up scholarly sources...")
        
        def process():
            try:
                # Just show structured data, no LLM needed
                matched_name, suggestion = fuzzy_match_entity(user_input)
                if not matched_name:
                    self.update_thinking_signal.emit(thinking_msg, suggestion)
                    return
                
                entity = getEntity(matched_name)
                entity_name = getEntityName(entity)
                formatted_name = format_entity_name(entity_name)
                
                # Get decompositions for this entity
                decomps = getDecompositionsFor(entity)
                
                if not decomps:
                    response = f"ℹ️ No decompositions (and therefore no claims) found for '{formatted_name}'."
                    self.update_thinking_signal.emit(thinking_msg, response)
                    return
                
                # Get claims for each decomposition with complete info
                all_claims = []
                claim_names = {}  # Map claim object to name
                
                # First, get all claim names from metamodel
                import inspect
                for name, obj in inspect.getmembers(metamodel):
                    if isinstance(obj, metamodel.ClaimSoftgoal):
                        claim_names[id(obj)] = name
                
                # Get claims for each decomposition
                for decomp in decomps:
                    claims = getClaimsFor(decomp)
                    for claim in claims:
                        claim_name = claim_names.get(id(claim), "Unknown Claim")
                        
                        # Get what this claim supports
                        supports_text = decomp.name if hasattr(decomp, 'name') else str(decomp)
                        
                        all_claims.append({
                            'claim_name': claim_name,
                            'decomposition': decomp.name,
                            'argument': claim.argument,
                            'supports': supports_text
                        })
                
                if not all_claims:
                    response = f"ℹ️ No claims found for decompositions of '{formatted_name}'."
                    self.update_thinking_signal.emit(thinking_msg, response)
                    return
                
                # Build response - show complete claim information
                response = f"📜 Claims/Justifications for {formatted_name}\n\n"
                response += f"Found {len(all_claims)} claim(s) supporting its decompositions:\n\n"
                
                for i, claim_data in enumerate(all_claims, 1):
                    response += f"{i}. {claim_data['claim_name']}\n"
                    response += f"   Supports: {claim_data['decomposition']}\n"
                    response += f"   Citation: {claim_data['argument']}\n"
                    response += "\n"
                
                response += "💡 These are scholarly sources supporting the decomposition methods."
                
                # Update UI - no LLM processing
                self.update_thinking_signal.emit(thinking_msg, response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _menu_domain_knowledge(self):
        """Handle 'Domain Knowledge' menu button"""
        dialog = InputDialog(
            "Explore domain knowledge",
            "Enter a claim or source to explore its domain context..."
        )
        
        if dialog.exec() == QDialog.Accepted:
            user_input = dialog.get_input()
            if not user_input:
                return
            
            # Add user message IMMEDIATELY
            self._add_message("user", f"Domain knowledge for: {user_input}")
            self._process_domain_knowledge(user_input)
    
    def _process_domain_knowledge(self, user_input: str):
        """Process domain knowledge query - PLACEHOLDER"""
        thinking_msg = self._add_message("assistant", "🎓 Analyzing domain knowledge...")
        
        def process():
            try:
                # Ensure MenuLLM is ready
                menu_llm = self._ensure_menu_llm()
                
                # PLACEHOLDER: This will tie claims/justifications with domains
                response = f"🎓 Domain Knowledge Feature (Placeholder)\n\n"
                response += f"This feature will connect claims and justifications with their academic/research domains.\n\n"
                response += f"Query: {user_input}\n\n"
                response += f"Coming soon: Domain categorization, source attribution, and cross-domain analysis."
                
                self.update_thinking_signal.emit(thinking_msg, response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _menu_classify(self):
        """Handle 'Classify' menu button - ONE dialog with text input AND two classification buttons"""
        # Create ONE dialog with everything
        dialog = QDialog(self)
        dialog.setWindowTitle("Classify Requirement")
        dialog.setModal(True)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("Requirement Classification")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Enter a requirement and choose classification type:")
        desc.setStyleSheet("font-size: 11pt; color: #666; margin-bottom: 15px;")
        layout.addWidget(desc)
        
        # Text input for requirement
        input_label = QLabel("Requirement:")
        input_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(input_label)
        
        text_input = QTextEdit()
        text_input.setPlaceholderText("Example: The system shall respond within 2 seconds...")
        text_input.setMinimumHeight(120)
        text_input.setMaximumHeight(150)
        text_input.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QTextEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        layout.addWidget(text_input)
        
        # Classification type label
        type_label = QLabel("Choose classification type:")
        type_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333; margin-top: 15px; margin-bottom: 10px;")
        layout.addWidget(type_label)
        
        # Button 1: FR vs NFR
        fr_nfr_btn = QPushButton("📊 Classify: FR vs NFR")
        fr_nfr_btn.setMinimumHeight(50)
        fr_nfr_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        layout.addWidget(fr_nfr_btn)
        
        # Button 2: Specific Type
        specific_btn = QPushButton("ℹ️ Classify: Specific Type (FR/NFR + Detailed)")
        specific_btn.setMinimumHeight(50)
        specific_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        layout.addWidget(specific_btn)
        
        # Close button
        close_btn = QPushButton("Cancel")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-size: 11pt;
                padding: 8px;
                border: none;
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        close_btn.clicked.connect(dialog.reject)
        layout.addWidget(close_btn)
        
        # Connect buttons
        choice = [None]
        def handle_fr_nfr():
            req = text_input.toPlainText().strip()
            if not req:
                QMessageBox.warning(dialog, "Input Required", "Please enter a requirement first.")
                return
            choice[0] = ("fr_nfr", req)
            dialog.accept()
        
        def handle_specific():
            req = text_input.toPlainText().strip()
            if not req:
                QMessageBox.warning(dialog, "Input Required", "Please enter a requirement first.")
                return
            choice[0] = ("specific", req)
            dialog.accept()
        
        fr_nfr_btn.clicked.connect(handle_fr_nfr)
        specific_btn.clicked.connect(handle_specific)
        
        # Show dialog
        if dialog.exec() == QDialog.Accepted and choice[0]:
            classify_type, requirement = choice[0]
            
            # Add user message IMMEDIATELY
            if classify_type == "fr_nfr":
                self._add_message("user", f"Classify (FR vs NFR): {requirement}")
                # Add loading indicator IMMEDIATELY
                thinking_msg = self._add_message("assistant", "⏳ Classifying FR vs NFR...")
                self._process_classify_fr_nfr(requirement, thinking_msg)
            else:
                self._add_message("user", f"Classify (Specific Type): {requirement}")
                # Add loading indicator IMMEDIATELY
                thinking_msg = self._add_message("assistant", "⏳ Classifying specific type...")
                self._process_classify_specific(requirement, thinking_msg)

    def _process_classify_fr_nfr(self, requirement: str, thinking_msg):
        """Classify as FR or NFR only (Stage 1) - EXACT menu_windows logic"""
        # thinking_msg already created by caller
        
        def process():
            try:
                print(f"\n{'='*60}")
                print(f"CLASSIFICATION: FR vs NFR")
                print(f"{'='*60}")
                print(f"Requirement: {requirement}")
                print(f"{'='*60}\n")
                
                result = classify_fr_nfr(requirement)
                print(f"Result: {result}\n")
                
                if result == 'NFR':
                    response = "✅ Classification: Non-Functional Requirement (NFR)\n\n"
                    response += "This requirement describes a quality attribute or constraint on how the system should perform.\n\n"
                    response += "💡 Use 'Classify: Specific Type' to identify which NFR type (Performance, Security, etc.)"
                elif result == 'FR':
                    response = "✅ Classification: Functional Requirement (FR)\n\n"
                    response += "This requirement describes what the system should do - a specific function or behavior.\n\n"
                    response += "💡 Use 'Classify: Specific Type' to identify which FR type (Process, Display, etc.)"
                else:
                    response = f"Classification: {result}"
                
                self.update_thinking_signal.emit(thinking_msg, response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    def _process_classify_specific(self, requirement: str, thinking_msg):
        """Classify into specific type (Stage 2) - EXACT menu_windows logic"""
        # thinking_msg already created by caller
        
        def process():
            try:
                # First determine FR vs NFR
                print(f"\n{'='*60}")
                print(f"CLASSIFICATION: Specific Type")
                print(f"{'='*60}")
                print(f"Requirement: {requirement}")
                print(f"{'='*60}\n")
                
                category = classify_fr_nfr(requirement)
                print(f"Category: {category}")
                
                if category == "NFR":
                    # Classify NFR type - returns (type, warning)
                    print("Classifying NFR type...")
                    result, warning = classify_nfr_type(requirement)
                    print(f"NFR Type: {result}, Warning: {warning}")
                    formatted_name = format_entity_name(result)
                    
                    if warning:
                        response = f"ℹ️ **NFR Type: {formatted_name}**\n\n"
                        response += f"**Note:** {warning}\n\n"
                        response += "The classifier could not find an exact match in the metamodel.\n"
                        response += "The above type is suggested by the LLM but may not be in the knowledge base."
                        
                        self.update_thinking_signal.emit(thinking_msg, response)
                    else:
                        response = f"✅ **NFR Type: {formatted_name}**\n\n"
                        
                        # Get description from metamodel
                        entity = getEntity(result)
                        if entity and hasattr(entity, 'description'):
                            response += f"**Description:** {entity.description}\n\n"
                        
                        response += "This is a non-functional requirement focusing on quality attributes."
                        
                        # Add exploration buttons
                        buttons = [
                            {"label": f"📖 What is {formatted_name}?", "action": "whats_this", "data": {"entity": result}},
                            {"label": f"🌳 Decompose {formatted_name}", "action": "decompose", "data": {"entity": result}},
                        ]
                        
                        self.update_ui_signal.emit(thinking_msg, response, buttons)
                    
                else:  # FR
                    # Classify FR type - returns (type, warning)
                    print("Classifying FR type...")
                    result, warning = classify_fr_type(requirement)
                    print(f"FR Type: {result}, Warning: {warning}")
                    formatted_name = format_entity_name(result)
                    
                    if warning:
                        response = f"ℹ️ **FR Type: {formatted_name}**\n\n"
                        response += f"**Note:** {warning}\n\n"
                        response += "The classifier used LLM fallback for this type."
                    else:
                        response = f"✅ **FR Type: {formatted_name}**\n\n"
                        response += "This is a functional requirement describing system behavior."
                    
                    self.update_thinking_signal.emit(thinking_msg, response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    def _menu_browse(self):
        """Handle Browse menu button - Chatbot style with category buttons"""
        message = "📚 Browse NFR Framework\n\n"
        message += "Choose a category to explore:"
        
        buttons = [
            {"label": "📋 NFR Types", "action": "browse_category", "data": {"category": "NFR Types"}},
            {"label": "🔧 Operationalizing Softgoals", "action": "browse_category", "data": {"category": "Operationalizing Softgoals"}},
            {"label": "⚙️ Functional Requirement Types", "action": "browse_category", "data": {"category": "Functional Requirement Types"}},
            {"label": "📜 Claim Softgoals", "action": "browse_category", "data": {"category": "Claim Softgoals"}},
            {"label": "🌳 Decomposition Methods", "action": "browse_category", "data": {"category": "Decomposition Methods"}},
            {"label": "🔗 Contribution Links", "action": "browse_category", "data": {"category": "Contribution Links"}},
            {"label": "💭 Correlation Links", "action": "browse_category", "data": {"category": "Correlation Links"}},
        ]
        
        self._add_message("assistant", message, buttons)
    
    def _process_browse_category(self, category: str):
        """Process browse category - show both type hierarchy AND ground instances"""
        print(f"\n{'='*60}")
        print(f"BROWSE CATEGORY: {category}")
        print(f"{'='*60}\n")
        
        thinking_msg = self._add_message("assistant", f"📚 Loading {category}...")
        
        def process():
            try:
                print(f"Processing category: {category}")
                examples = []
                
                if category == "NFR Types":
                    # Get all NFR types
                    for name, obj in inspect.getmembers(metamodel):
                        if inspect.isclass(obj) and hasattr(metamodel, 'NFRSoftgoalType'):
                            try:
                                if issubclass(obj, metamodel.NFRSoftgoalType) and obj != metamodel.NFRSoftgoalType:
                                    if not name.endswith('MetaClass') and 'Type' in name:
                                        # Get type hierarchy (children classes)
                                        type_children = []
                                        try:
                                            child_objs = getChildren(obj)
                                            for child in child_objs:
                                                child_name = getEntityName(child)
                                                type_children.append(("type", child_name))
                                        except:
                                            pass
                                        
                                        # Get ground instances (actual objects)
                                        # Ground instances are instances of Softgoal classes, not Type classes
                                        # e.g., performanceNFR1 is instance of TimePerformanceSoftgoal
                                        instance_children = []
                                        
                                        # Find corresponding Softgoal class for this Type
                                        softgoal_name = name.replace('Type', 'Softgoal')
                                        softgoal_class = None
                                        if hasattr(metamodel, softgoal_name):
                                            softgoal_class = getattr(metamodel, softgoal_name)
                                        
                                        if softgoal_class:
                                            for inst_name, inst_obj in inspect.getmembers(metamodel):
                                                if not inspect.isclass(inst_obj) and not inspect.isfunction(inst_obj):
                                                    try:
                                                        # Check if instance of this softgoal or its children
                                                        if isinstance(inst_obj, softgoal_class):
                                                            instance_children.append(("instance", inst_name))
                                                        # Also check children softgoals
                                                        try:
                                                            for child_class in getChildren(softgoal_class):
                                                                if isinstance(inst_obj, child_class):
                                                                    instance_children.append(("instance", inst_name))
                                                                    break
                                                        except:
                                                            pass
                                                    except:
                                                        pass
                                        
                                        examples.append((name, obj, type_children, instance_children))
                            except TypeError:
                                pass
                
                elif category == "Operationalizing Softgoals":
                    for name, obj in inspect.getmembers(metamodel):
                        if inspect.isclass(obj) and hasattr(metamodel, 'OperationalizingSoftgoalType'):
                            try:
                                if issubclass(obj, metamodel.OperationalizingSoftgoalType) and obj != metamodel.OperationalizingSoftgoalType:
                                    if not name.endswith('MetaClass') and 'Type' in name:
                                        # Type hierarchy
                                        type_children = []
                                        try:
                                            child_objs = getChildren(obj)
                                            for child in child_objs:
                                                child_name = getEntityName(child)
                                                type_children.append(("type", child_name))
                                        except:
                                            pass
                                        
                                        # Ground instances
                                        instance_children = []
                                        softgoal_name = name.replace('Type', 'Softgoal')
                                        softgoal_class = None
                                        if hasattr(metamodel, softgoal_name):
                                            softgoal_class = getattr(metamodel, softgoal_name)
                                        
                                        if softgoal_class:
                                            for inst_name, inst_obj in inspect.getmembers(metamodel):
                                                if not inspect.isclass(inst_obj) and not inspect.isfunction(inst_obj):
                                                    try:
                                                        if isinstance(inst_obj, softgoal_class):
                                                            instance_children.append(("instance", inst_name))
                                                        try:
                                                            for child_class in getChildren(softgoal_class):
                                                                if isinstance(inst_obj, child_class):
                                                                    instance_children.append(("instance", inst_name))
                                                                    break
                                                        except:
                                                            pass
                                                    except:
                                                        pass
                                        
                                        examples.append((name, obj, type_children, instance_children))
                            except TypeError:
                                pass
                
                elif category == "Functional Requirement Types":
                    for name, obj in inspect.getmembers(metamodel):
                        if inspect.isclass(obj) and hasattr(metamodel, 'FunctionalRequirementType'):
                            try:
                                if issubclass(obj, metamodel.FunctionalRequirementType) and obj != metamodel.FunctionalRequirementType:
                                    if not name.endswith('MetaClass'):
                                        type_children = []
                                        try:
                                            child_objs = getChildren(obj)
                                            for child in child_objs:
                                                child_name = getEntityName(child)
                                                type_children.append(("type", child_name))
                                        except:
                                            pass
                                        
                                        instance_children = []
                                        # FR instances would be instances of FRSoftgoal, not FRType
                                        softgoal_name = name.replace('Type', 'Softgoal')
                                        softgoal_class = None
                                        if hasattr(metamodel, softgoal_name):
                                            softgoal_class = getattr(metamodel, softgoal_name)
                                        
                                        if softgoal_class:
                                            for inst_name, inst_obj in inspect.getmembers(metamodel):
                                                if not inspect.isclass(inst_obj) and not inspect.isfunction(inst_obj):
                                                    try:
                                                        if isinstance(inst_obj, softgoal_class):
                                                            instance_children.append(("instance", inst_name))
                                                    except:
                                                        pass
                                        
                                        examples.append((name, obj, type_children, instance_children))
                            except TypeError:
                                pass
                
                elif category == "Claim Softgoals":
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'ClaimSoftgoal'):
                            if isinstance(obj, metamodel.ClaimSoftgoal):
                                examples.append((name, obj, [], []))
                
                elif category == "Decomposition Methods":
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'NFRDecompositionMethod'):
                            if isinstance(obj, metamodel.NFRDecompositionMethod):
                                examples.append((name, obj, [], []))
                        elif hasattr(metamodel, 'OperationalizationDecompositionMethod'):
                            if isinstance(obj, metamodel.OperationalizationDecompositionMethod):
                                examples.append((name, obj, [], []))
                
                elif category == "Contribution Links":
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'Contribution'):
                            if isinstance(obj, metamodel.Contribution):
                                info = f"{obj.source} → {obj.target} ({obj.type.value})"
                                examples.append((name, obj, [(info, "")], []))
                
                elif category == "Correlation Links":
                    for name, obj in inspect.getmembers(metamodel):
                        if hasattr(metamodel, 'Correlation'):
                            if isinstance(obj, metamodel.Correlation):
                                examples.append((name, obj, [], []))
                
                # Format output with BOTH type hierarchy and ground instances
                if examples:
                    response = f"📚 {category.upper()}\n\n"

                    response += f"Found {len(examples)} item(s):\n\n"

                    
                    for i, item in enumerate(examples, 1):
                        if len(item) == 4:  # Has type_children and instance_children
                            name, obj, type_children, instance_children = item
                        else:  # Old format
                            name, obj = item[0], item[1]
                            type_children = []
                            instance_children = []
                        
                        display_name = format_entity_name(name) if 'Type' in name else name
                        response += f"{i}. **{display_name}**\n"
                        
                        # Show type hierarchy
                        if type_children:
                            response += "   Types:\n"
                            for kind, child_name in type_children[:5]:
                                child_display = format_entity_name(child_name)
                                response += f"     ↳ {child_display}\n"
                            if len(type_children) > 5:
                                response += f"     ↳ ... and {len(type_children) - 5} more\n"
                        
                        # Show ground instances
                        if instance_children:
                            response += "   Instances:\n"
                            for kind, inst_name in instance_children:
                                response += f"     ⚡ {inst_name}\n"
                        
                        response += "\n"
                    
                    response += f"💡 Total: {len(examples)} items"
                    
                    # Add helpful hint instead of limited buttons
                    response += "\n💬 **Tip:** Type any item name above to explore it in detail!"
                    buttons = []
                else:
                    response = f"ℹ️ No items found for {category}"
                    buttons = []
                
                # Update UI
                if buttons:
                    self.update_ui_signal.emit(thinking_msg, response, buttons)
                else:
                    self.update_thinking_signal.emit(thinking_msg, response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                import traceback
                traceback.print_exc()
                self.update_thinking_signal.emit(thinking_msg, error_msg)
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    def _show_info(self):
        """Show information about the tool"""
        info_text = """ℹ️ **NFR Framework Assistant**

This tool helps you work with Non-Functional Requirements using the NFR Framework metamodel.

**Key Features:**
• 📖 Explore 47+ NFR types and their decompositions
• 🌳 Understand hierarchical relationships
• 🔧 Find operationalization techniques
• ⚡ Analyze side effects and trade-offs
• ✅ Classify requirements automatically
• 📜 Access scholarly sources and justifications

**How to Use:**
1. Click a menu button for specific actions
2. Or type freely to chat about requirements
3. Follow suggested buttons to explore deeper

**Tips:**
• Start with "What's This?" to learn about any NFR type
• Use "Classify" to analyze your requirements
• Explore "Side Effects" to understand trade-offs

Powered by the NFR Framework metamodel and local LLM (Llama 3.1)
"""
        
        self._add_message("assistant", info_text)
    
    def _start_background_loading(self):
        """Start loading components in background without blocking UI"""
        def load():
            try:
                self.loading_status_signal.emit("Loading AI model...")

                # Initialize MenuLLM
                self.menu_llm = MenuLLM()

                # Pre-load metamodel
                import metamodel

                # Pre-load classifier
                from classifier_v6 import classify_fr_nfr

                # Warm up LLM (loads model into memory)
                import ollama
                ollama.chat(
                    model="llama3.1:8b",
                    messages=[{"role": "user", "content": "hi"}],
                    options={"num_predict": 1}
                )

                self.components_loaded = True
                self._model_ready.set()
                self.loading_status_signal.emit("")

            except Exception as e:
                print(f"Background loading error: {e}")
                import traceback
                traceback.print_exc()
                # Unblock waiters even on failure so the app doesn't hang
                self._model_ready.set()
                self.loading_status_signal.emit("")

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def _ensure_menu_llm(self):
        """Ensure MenuLLM is initialized, waiting for background loading if needed"""
        if not self._model_ready.is_set():
            self._model_ready.wait()
        if self.menu_llm is None:
            try:
                self.menu_llm = MenuLLM()
            except Exception as e:
                print(f"Failed to initialize MenuLLM: {e}")
                raise
        return self.menu_llm


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Launch the chat interface"""
    print("="*70)
    print("NFR ELICITATION ASSISTANT - CHAT INTERFACE")
    print("="*70)
    print("Version: 3.0 (Unified Chat - FIXED)")
    print("="*70)
    print()
    
    app = QApplication(sys.argv)
    
    # Set application font
    app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)
    
    # Create and show chat interface
    chat = ChatInterface()
    chat.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()