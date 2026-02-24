import json
import logging
from typing import Dict, Any, Tuple
from src.rules.models import ChannelTypeEnum

logger = logging.getLogger(__name__)


class BaseChannel:
    def __init__(self, config: dict):
        self.config = config

    def dispatch(self) -> Tuple[bool, str]:
        raise NotImplementedError


class WebhookChannel(BaseChannel):
    def dispatch(self) -> Tuple[bool, str]:
        url = self.config.get("url")
        if not url:
            return False, "Missing required 'url' in webhook config"

        logger.info(f"Webhook would be sent to: {url}")
        return True, ""


class EmailChannel(BaseChannel):
    def dispatch(self) -> Tuple[bool, str]:
        to = self.config.get("to")
        if not to:
            return False, "Missing required 'to' in email config"

        logger.info(f"Email would be sent to: {to}")
        return True, ""


class LogChannel(BaseChannel):
    def dispatch(self) -> Tuple[bool, str]:
        logger.info("Log channel dispatched")
        return True, ""


CHANNEL_REGISTRY: Dict[str, type[BaseChannel]] = {
    ChannelTypeEnum.WEBHOOK.value: WebhookChannel,
    ChannelTypeEnum.EMAIL.value: EmailChannel,
    ChannelTypeEnum.LOG.value: LogChannel,
}


def dispatch_to_channel(channel_type: str, config: dict) -> Tuple[bool, str]:
    channel_class = CHANNEL_REGISTRY.get(channel_type)
    if not channel_class:
        return False, f"Unknown channel type: {channel_type}"

    channel = channel_class(config)
    return channel.dispatch()


def validate_channel_config(channel_type: str, config: dict) -> Tuple[bool, str]:
    if channel_type == ChannelTypeEnum.WEBHOOK.value:
        if not config.get("url"):
            return False, "Webhook channel requires 'url' in config"
    elif channel_type == ChannelTypeEnum.EMAIL.value:
        if not config.get("to"):
            return False, "Email channel requires 'to' in config"

    return True, ""
