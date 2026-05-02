# Node-RED HTTP Control Bridge

This folder contains an importable Node-RED flow for the backend-to-hardware control bridge.

## Import

1. Open Node-RED.
2. Import `http-control-bridge.json`.
3. Edit the MQTT broker config node.
4. Deploy the flow.

## Backend configuration

Set these environment variables for the FastAPI backend:

```bash
DEVICE_CONTROL_TRANSPORT=http
DEVICE_CONTROL_ENDPOINT=http://<node-red-host>:1880/iomt/control
```

## Payload shape

The backend can send:

```json
{
  "command_id": "CMD-1234",
  "device_id": "TEMP_ESP32_003",
  "action": "quarantine",
  "requested_by": "dashboard",
  "metadata": {
    "reason": "manual test"
  }
}
```

The flow converts that into a device command payload and republishes it to the matching MQTT topic.

## Later hardware swap

When you are ready to connect real sensor shutdowns and telemetry, keep the same HTTP endpoint but replace the backend-triggered payload or Node-RED routing logic as needed.
