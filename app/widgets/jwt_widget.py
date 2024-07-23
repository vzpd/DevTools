import base64
import json

import jwt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from app.core.toast import Toast
from app.widgets import BaseWidget


class JwtWidget(BaseWidget):
    name = "jwt"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jwt Viewer")

        self.secret_te = QLineEdit(self)
        self.jwt_pte = QPlainTextEdit(self)
        self.jwt_header_te = QTextEdit(self)
        self.jwt_payload_te = QTextEdit(self)
        self.signature_check_cb = QCheckBox("valid")

        self.set_ui()

    def set_ui(self):
        check_h_box = QHBoxLayout()
        self.signature_check_cb.setDisabled(True)
        check_h_box.addWidget(self.secret_te)
        check_h_box.addWidget(self.signature_check_cb)

        parse_jwt_vbox = QVBoxLayout()
        self.jwt_pte.setPlaceholderText("input your jwt here")
        self.jwt_pte.setFixedHeight(100)
        self.jwt_header_te.setFixedHeight(100)
        self.jwt_header_te.setPlaceholderText("Header")
        self.jwt_payload_te.setFixedHeight(100)
        self.jwt_payload_te.setPlaceholderText("Payload")
        self.secret_te.setPlaceholderText("input your secret here")

        self.jwt_payload_te.setReadOnly(True)
        self.jwt_header_te.setReadOnly(True)
        self.jwt_pte.textChanged.connect(
            lambda: self.decode_jwt(
                self.jwt_pte.toPlainText(), self.secret_te.text(), self.jwt_header_te, self.jwt_payload_te
            )
        )
        self.secret_te.textChanged.connect(
            lambda: self.decode_jwt(
                self.jwt_pte.toPlainText(), self.secret_te.text(), self.jwt_header_te, self.jwt_payload_te
            )
        )

        parse_jwt_vbox.addWidget(self.jwt_pte)
        parse_jwt_vbox.addLayout(check_h_box)
        parse_jwt_vbox.addWidget(self.jwt_header_te)
        parse_jwt_vbox.addWidget(self.jwt_payload_te)
        parse_jwt_vbox.addStretch()

        h_box = QHBoxLayout()
        h_box.addLayout(parse_jwt_vbox)
        self.setLayout(h_box)

    def set_signature_validation(self, validation: bool):
        self.signature_check_cb.setEnabled(True)
        self.signature_check_cb.setChecked(validation)
        self.signature_check_cb.setDisabled(True)

    def decode_jwt(self, jwt_str, secret_str, header_te: QTextEdit, payload_lt: QTextEdit):
        self.set_signature_validation(False)
        jwt_str = jwt_str.strip()

        jwt_content = jwt_str.split(".")
        if len(jwt_content) != 3:
            payload_lt.setText("Invalid Jwt")
            return

        try:
            header = self.parse_header(jwt_content[0])
            header_te.setText(str(header))
        except ValueError:
            header_te.setText("Invalid Jwt Header")
            return

        try:
            if secret_str:
                payload = jwt.decode(jwt_str, key=secret_str, algorithms=header.get("alg"))
                self.set_signature_validation(True)
            else:
                payload = json.loads(self.decode_base64url(jwt_content[1]).decode("utf-8"))
            payload_lt.setText(str(payload))
        except jwt.ExpiredSignatureError:
            payload_lt.setText("Jwt is expired")
        except jwt.InvalidTokenError:
            payload_lt.setText("Invalid Jwt")

    @classmethod
    def decode_base64url(cls, data):
        padding = "=" * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    @classmethod
    def parse_header(cls, header) -> dict | None:
        decoded_header = cls.decode_base64url(header).decode("utf-8")
        header_json = json.loads(decoded_header)

        return header_json

    def switch_in(self):
        self.jwt_pte.setFocus()
