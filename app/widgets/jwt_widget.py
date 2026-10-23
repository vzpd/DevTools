import base64
import binascii
import json
from datetime import UTC, datetime

import jwt
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core.components import EditorPanel, StatusLabel
from app.utils.json_tools import reject_constant
from app.widgets import BaseWidget


class JwtWidget(BaseWidget):
    name = "jwt"

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        split = QSplitter(Qt.Horizontal)
        input_panel = EditorPanel("Encoded token", "粘贴 JWT（header.payload.signature）")
        self.jwt_pte = input_panel.editor
        input_panel.menu.addAction("清空 Token 和密钥", self.clear)
        self.jwt_pte.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        split.addWidget(input_panel)
        decoded = QWidget()
        decoded_layout = QVBoxLayout(decoded)
        decoded_layout.setContentsMargins(0, 0, 0, 0)
        header = EditorPanel("Header", read_only=True, json_mode=True)
        payload = EditorPanel("Payload", read_only=True, json_mode=True)
        self.jwt_header_te = header.editor
        self.jwt_payload_te = payload.editor
        decoded_layout.addWidget(header, 1)
        decoded_layout.addWidget(payload, 2)
        split.addWidget(decoded)
        split.setSizes([480, 600])
        split.setChildrenCollapsible(False)
        layout.addWidget(split, 1)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("验签算法"))
        self.algorithm = QComboBox()
        self.algorithm.addItems(["HS256", "HS384", "HS512"])
        controls.addWidget(self.algorithm)
        self.secret_te = QLineEdit()
        self.secret_te.setEchoMode(QLineEdit.Password)
        self.secret_te.setPlaceholderText("输入 HMAC 密钥后验证签名")
        controls.addWidget(self.secret_te, 1)
        show_secret = QCheckBox("显示密钥")
        show_secret.toggled.connect(
            lambda checked: self.secret_te.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        controls.addWidget(show_secret)
        layout.addLayout(controls)
        options = QHBoxLayout()
        options.addWidget(QLabel("验证范围"))
        self.validation_mode = QComboBox()
        self.validation_mode.addItems(["仅签名", "签名和时间声明"])
        options.addWidget(self.validation_mode)
        self.check_identity = QCheckBox("校验 issuer / audience")
        options.addWidget(self.check_identity)
        options.addStretch()
        layout.addLayout(options)
        self.identity_options = QWidget()
        identity_layout = QHBoxLayout(self.identity_options)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        self.issuer = QLineEdit()
        self.issuer.setPlaceholderText("预期 issuer（可留空）")
        self.audience = QLineEdit()
        self.audience.setPlaceholderText("预期 audience（可留空）")
        identity_layout.addWidget(self.issuer)
        identity_layout.addWidget(self.audience)
        self.identity_options.hide()
        self.check_identity.toggled.connect(self.identity_options.setVisible)
        layout.addWidget(self.identity_options)
        self.status = StatusLabel("等待输入 JWT · 解码不代表签名已验证")
        self.claims = StatusLabel()
        layout.addWidget(self.status)
        layout.addWidget(self.claims)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.decode_jwt)
        self.jwt_pte.textChanged.connect(self.schedule_decode)
        self.secret_te.textChanged.connect(self.schedule_decode)
        self.algorithm.currentIndexChanged.connect(self.schedule_decode)
        self.validation_mode.currentIndexChanged.connect(self.schedule_decode)
        self.check_identity.toggled.connect(self.schedule_decode)
        self.issuer.textChanged.connect(self.schedule_decode)
        self.audience.textChanged.connect(self.schedule_decode)

    def schedule_decode(self):
        self.jwt_header_te.clear()
        self.jwt_payload_te.clear()
        self.claims.clear()
        self.status.set_status("等待输入完成…")
        self.timer.start()

    @staticmethod
    def decode_segment(segment):
        import re

        if not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", segment):
            raise ValueError("无效 Base64URL 字符")
        raw = base64.b64decode(segment + "=" * (-len(segment) % 4), altchars=b"-_", validate=True)
        value = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        if not isinstance(value, dict):
            raise ValueError("Header 和 Payload 必须是 JSON 对象")
        return value

    def decode_jwt(self):
        self.timer.stop()
        self.jwt_header_te.clear()
        self.jwt_payload_te.clear()
        self.claims.clear()
        text = self.jwt_pte.toPlainText().strip()
        if text[:7].lower() == "bearer ":
            text = text[7:].strip()
        if not text:
            self.status.set_status("等待输入 JWT · 解码不代表签名已验证")
            return
        try:
            segments = text.split(".")
            if len(segments) != 3 or not segments[0] or not segments[1]:
                raise ValueError("JWT 必须包含 Header、Payload 和 Signature 三段")
            header, payload = (self.decode_segment(segment) for segment in segments[:2])
            if not isinstance(header.get("alg"), str):
                raise ValueError("缺少 alg 算法声明")
            self.jwt_header_te.setPlainText(json.dumps(header, indent=2, ensure_ascii=False))
            self.jwt_payload_te.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))
        except (ValueError, UnicodeError, binascii.Error, RecursionError):
            self.status.set_status("JWT 格式错误：检查三段结构、Base64URL 编码及 JSON 对象", "error")
            return
        self.describe_claims(payload)
        if not self.secret_te.text():
            self.status.set_status(f"已解码 · alg={header.get('alg', '未指定')} · 签名未验证")
            return
        check_time = self.validation_mode.currentIndex() == 1
        issuer = self.issuer.text().strip() if self.check_identity.isChecked() else ""
        audience = self.audience.text().strip() if self.check_identity.isChecked() else ""
        if self.check_identity.isChecked() and not (issuer or audience):
            self.status.set_status("请填写预期 issuer 或 audience", "error")
            return
        try:
            jwt.decode(
                text,
                self.secret_te.text(),
                algorithms=[self.algorithm.currentText()],
                issuer=issuer or None,
                audience=audience or None,
                options={
                    "verify_exp": check_time,
                    "verify_nbf": check_time,
                    "verify_iat": check_time,
                    "verify_aud": bool(audience),
                    "verify_iss": bool(issuer),
                    "verify_sub": False,
                    "verify_jti": False,
                },
            )
        except jwt.ExpiredSignatureError:
            self.status.set_status("验证失败：Token 已过期", "error")
            return
        except jwt.ImmatureSignatureError:
            self.status.set_status("验证失败：Token 尚未生效或签发时间在未来", "error")
            return
        except (jwt.InvalidIssuerError, jwt.InvalidAudienceError, jwt.MissingRequiredClaimError):
            self.status.set_status("验证失败：issuer / audience 缺失或不匹配", "error")
            return
        except (jwt.InvalidTokenError, ValueError, TypeError):
            self.status.set_status("签名验证失败：检查密钥、签名及所选算法", "error")
            return
        checked = ["签名验证通过"]
        checked.append("已校验存在的时间声明" if check_time else "未校验时间有效性")
        checked.append(
            "已校验 " + "/".join(name for name, value in (("issuer", issuer), ("audience", audience)) if value)
            if issuer or audience
            else "未校验 issuer / audience"
        )
        self.status.set_status(" · ".join(checked), "success")

    def describe_claims(self, payload):
        descriptions = []
        now = datetime.now(UTC).timestamp()
        for key, label in (("iat", "签发"), ("nbf", "生效"), ("exp", "过期")):
            if key not in payload:
                continue
            value = payload[key]
            try:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ValueError()
                date = datetime.fromtimestamp(value, UTC)
                state = (
                    "（已过期）"
                    if key == "exp" and value <= now
                    else "（尚未生效）" if key == "nbf" and value > now else ""
                )
                descriptions.append(f"{label}：{date.strftime('%Y-%m-%d %H:%M:%S')} UTC{state}")
            except (ValueError, OverflowError, OSError):
                descriptions.append(f"{label}：无效 NumericDate")
        self.claims.set_status("  ·  ".join(descriptions) or "无 iat / nbf / exp 时间声明")

    def clear(self):
        self.jwt_pte.clear()
        self.secret_te.clear()
        self.decode_jwt()

    def switch_in(self):
        self.jwt_pte.setFocus()
