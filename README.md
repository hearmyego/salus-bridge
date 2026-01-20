# Salus Bridge

REST API bridge for Salus iT600 heating system. Wraps the local gateway protocol so you can control your heating from any HTTP client.

## Requirements

- Salus iT600 gateway on your local network
- Gateway EUID (printed on the bottom of your gateway)
- Docker

## Quick Start

1. Copy the example compose file:
   ```bash
   cp compose.example.yml compose.yml
   ```

2. Edit `compose.yml` with your gateway details:
   - `SALUS_GATEWAY_HOST` - IP address of your gateway
   - `SALUS_GATEWAY_EUID` - EUID from bottom of gateway

3. Start the service:
   ```bash
   docker compose up -d
   ```

4. Verify it's running:
   ```bash
   curl http://localhost:8000/
   ```

## Configuration

| Variable | Description |
|----------|-------------|
| `SALUS_GATEWAY_HOST` | IP address of your Salus gateway |
| `SALUS_GATEWAY_EUID` | EUID from bottom of gateway |

## API Endpoints

### Get all devices
```bash
curl http://localhost:8000/devices
```

### Get single device
```bash
curl http://localhost:8000/device/{device_id}
```

### Set temperature
```bash
curl -X POST http://localhost:8000/device/{device_id}/temperature \
  -H "Content-Type: application/json" \
  -d '{"temperature": 22.5}'
```

### Set mode
```bash
# Options: off, heat, auto
curl -X POST http://localhost:8000/device/{device_id}/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "heat"}'
```

### Set preset
```bash
# Options: "Follow Schedule", "Permanent Hold", "Off"
curl -X POST http://localhost:8000/device/{device_id}/preset \
  -H "Content-Type: application/json" \
  -d '{"preset": "Permanent Hold"}'
```

### Zone control (multiple devices)
```bash
# Set temperature for multiple devices
curl -X POST http://localhost:8000/zone/temperature \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": ["device_id_1", "device_id_2"],
    "temperature": 22.0
  }'

# Set preset for multiple devices
curl -X POST http://localhost:8000/zone/preset \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": ["device_id_1", "device_id_2"],
    "preset": "Off"
  }'
```

## Finding Your Device IDs

Call the `/devices` endpoint to get a list of all devices and their IDs:
```bash
curl http://localhost:8000/devices | jq
```

## Using with Docker Compose

Add to your existing `compose.yml`:

```yaml
services:
  salus-bridge:
    image: ghcr.io/hearmyego/salus-bridge:latest
    container_name: salus-bridge
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - SALUS_GATEWAY_HOST=192.168.1.100
      - SALUS_GATEWAY_EUID=001E5E09XXXXXXXX
```

## API Documentation

Interactive Swagger docs available at: `http://localhost:8000/docs`

## Troubleshooting

**Can't connect to gateway?**
- Verify the gateway IP is correct
- Try using `network_mode: host` in your compose file
- Ensure the gateway is on the same network

## Credits

Built on top of [pyit600](https://github.com/jvitkauskas/pyit600).
