"""
邮件服务抽象层 —— EmailProvider

- MockEmailProvider：开发环境，不真发邮件，仅打掩码日志
- SmtpEmailProvider：SMTP 真发（如 QQ 邮箱授权码）
"""
import logging
from abc import ABC, abstractmethod
from email.message import EmailMessage

logger = logging.getLogger("email")


def _mask_email(to: str) -> str:
    at = to.find("@")
    return f"{to[:2]}***{to[at:]}" if at > 0 else "***"


class EmailProvider(ABC):
    """邮件服务抽象接口"""

    @abstractmethod
    async def send(self, to: str, code: str, subject: str = "您的验证码") -> bool:
        """发送邮箱验证码，返回是否成功"""
        ...

    @abstractmethod
    async def send_password_reset(
        self,
        to: str,
        reset_token: str,
        *,
        expires_minutes: int = 15,
        subject: str = "密码重置",
    ) -> bool:
        """发送密码重置邮件（含 reset_token），返回是否成功"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """检查邮件服务是否可用"""
        ...


class MockEmailProvider(EmailProvider):
    """开发环境 Mock —— 不真发邮件，OTP / reset_token 仍由业务写入 Redis"""

    async def send(self, to: str, code: str, subject: str = "您的验证码") -> bool:
        logger.info(
            f"[MOCK EMAIL] to={_mask_email(to)} code_length={len(code)} subject={subject}"
        )
        return True

    async def send_password_reset(
        self,
        to: str,
        reset_token: str,
        *,
        expires_minutes: int = 15,
        subject: str = "密码重置",
    ) -> bool:
        # 本地无真邮：INFO 打出 token，便于联调（勿在生产开 mock）
        logger.info(
            f"[MOCK EMAIL] password_reset to={_mask_email(to)} "
            f"expires_minutes={expires_minutes} subject={subject} "
            f"reset_token={reset_token}"
        )
        return True

    async def health_check(self) -> bool:
        return True


class SmtpEmailProvider(EmailProvider):
    """SMTP 发送（QQ / 163 / 企业邮等）"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_addr: str,
        from_name: str = "",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr or username
        self.from_name = from_name

    def _build_message(self, to: str, body: str, subject: str) -> EmailMessage:
        msg = EmailMessage()
        if self.from_name:
            msg["From"] = f"{self.from_name} <{self.from_addr}>"
        else:
            msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        return msg

    async def _deliver(self, to: str, body: str, subject: str) -> bool:
        try:
            import aiosmtplib
        except ImportError:
            logger.error("[SMTP EMAIL] aiosmtplib 未安装，无法发送邮件")
            return False

        msg = self._build_message(to, body, subject)
        use_tls = self.port == 465
        start_tls = self.port == 587

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=use_tls,
                start_tls=start_tls,
            )
            logger.info(f"[SMTP EMAIL] sent to={_mask_email(to)} subject={subject}")
            return True
        except Exception as e:
            logger.error(f"[SMTP EMAIL] send failed: {e}")
            return False

    async def send(self, to: str, code: str, subject: str = "您的验证码") -> bool:
        body = f"您的验证码是 {code}，5 分钟内有效。如非本人操作请忽略此邮件。"
        return await self._deliver(to, body, subject)

    async def send_password_reset(
        self,
        to: str,
        reset_token: str,
        *,
        expires_minutes: int = 15,
        subject: str = "密码重置",
    ) -> bool:
        body = (
            "您正在申请重置密码。\n\n"
            f"请使用以下重置令牌（{expires_minutes} 分钟内有效）：\n"
            f"{reset_token}\n\n"
            "在重置密码页面填入该令牌与新密码即可完成重置。\n"
            "如非本人操作请忽略此邮件。"
        )
        return await self._deliver(to, body, subject)

    async def health_check(self) -> bool:
        return bool(self.host and self.username and self.password)
