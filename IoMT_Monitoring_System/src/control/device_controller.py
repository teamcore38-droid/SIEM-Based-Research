from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

import requests

from src.common.models import ControlCommand
from src.common.settings import get_settings
from src.control.hardware_registry import build_control_message, resolve_hardware_device


logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


class DeviceController:
    """
    Safe control adapter for the backend-to-sensor path.

    The controller keeps the current placeholder flow intact, but it can now
    forward the same command payload either to:
    - an HTTP endpoint such as Node-RED, or
    - a direct MQTT broker for the ESP32 devices.

    Transport selection:
    - DEVICE_CONTROL_TRANSPORT=http  -> use DEVICE_CONTROL_ENDPOINT
    - DEVICE_CONTROL_TRANSPORT=mqtt  -> use MQTT broker settings
    - DEVICE_CONTROL_TRANSPORT=auto  -> prefer HTTP if configured, else MQTT
    """

    def __init__(self, response_collection=None):
        self.response_collection = response_collection
        self.settings = get_settings()

    def _selected_transport(self) -> str:
        mode = (self.settings.device_control_transport or "auto").lower()
        if mode in {"http", "mqtt"}:
            return mode
        if self.settings.device_control_endpoint:
            return "http"
        if self.settings.device_control_mqtt_broker:
            return "mqtt"
        return "backend_only"

    def _dispatch_http(self, payload: Dict[str, Any]) -> bool:
        if not self.settings.device_control_endpoint:
            return False
        response = requests.post(self.settings.device_control_endpoint, json=payload, timeout=5)
        response.raise_for_status()
        return True

    def _dispatch_mqtt(self, payload: Dict[str, Any]) -> bool:
        if not self.settings.device_control_mqtt_broker:
            return False
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError(
                "paho-mqtt is required for MQTT control transport. Install paho-mqtt or use an HTTP endpoint."
            ) from exc

        client_id = self.settings.device_control_mqtt_client_id or f"iomt-control-{uuid.uuid4().hex[:8]}"
        client = mqtt.Client(client_id=client_id)
        if self.settings.device_control_mqtt_username:
            client.username_pw_set(
                self.settings.device_control_mqtt_username,
                self.settings.device_control_mqtt_password,
            )

        client.connect(
            self.settings.device_control_mqtt_broker,
            self.settings.device_control_mqtt_port,
            self.settings.device_control_mqtt_keepalive,
        )
        client.loop_start()
        try:
            info = client.publish(
                payload["command_topic"],
                json.dumps(payload, default=str),
                qos=self.settings.device_control_mqtt_qos,
                retain=False,
            )
            info.wait_for_publish(timeout=5)
        finally:
            client.loop_stop()
            client.disconnect()
        return True

    def issue(
        self,
        device_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        requested_by: str = "system",
    ) -> ControlCommand:
        command = ControlCommand(
            command_id=f"CMD-{uuid.uuid4().hex[:8].upper()}",
            device_id=device_id,
            action=action,
            requested_by=requested_by,
            metadata=metadata or {},
        )

        target = resolve_hardware_device(device_id)
        payload = build_control_message(
            command.command_id,
            device_id,
            action,
            metadata=command.metadata,
        )
        command.metadata = _json_safe({
            **command.metadata,
            "resolved_device_id": payload["device_id"],
            "source_device_id": payload["source_device_id"],
            "command_topic": payload["command_topic"],
            "telemetry_topic": payload.get("telemetry_topic"),
            "requested_action": payload["requested_action"],
            "resolved_command": payload["command"],
            "hardware_device": target.device_type if target is not None else None,
        })

        transport = self._selected_transport()
        dispatched = False
        dispatch_error: Optional[str] = None

        try:
            if transport == "http":
                dispatched = self._dispatch_http(payload)
            elif transport == "mqtt":
                dispatched = self._dispatch_mqtt(payload)
            elif transport == "auto":
                if self.settings.device_control_endpoint:
                    dispatched = self._dispatch_http(payload)
                    transport = "http"
                elif self.settings.device_control_mqtt_broker:
                    dispatched = self._dispatch_mqtt(payload)
                    transport = "mqtt"
        except Exception as exc:  # pragma: no cover - transport failures are environmental
            dispatch_error = str(exc)
            logger.warning("Control dispatch failed for %s via %s: %s", device_id, transport, exc)

        command.status = "sent" if dispatched else ("failed" if dispatch_error else "recorded")
        command.metadata = _json_safe({
            **command.metadata,
            "transport": transport,
            "backend_only": transport == "backend_only",
            "dispatched": dispatched,
            "dispatch_error": dispatch_error,
        })

        if self.response_collection is not None:
            self.response_collection.insert_one(_json_safe(command.__dict__))

        return command
