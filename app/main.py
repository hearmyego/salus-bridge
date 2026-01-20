from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from pyit600.gateway import IT600Gateway
import os

from __version__ import __version__

# Configuration from environment (required)
GATEWAY_HOST = os.getenv("SALUS_GATEWAY_HOST")
GATEWAY_EUID = os.getenv("SALUS_GATEWAY_EUID")

if not GATEWAY_HOST or not GATEWAY_EUID:
    raise ValueError(
        "SALUS_GATEWAY_HOST and SALUS_GATEWAY_EUID environment variables are required"
    )

# Global gateway instance
gateway: IT600Gateway | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage gateway connection lifecycle."""
    global gateway
    gateway = IT600Gateway(host=GATEWAY_HOST, euid=GATEWAY_EUID)
    await gateway.connect()
    await gateway.poll_status()
    print(f"Connected to Salus gateway at {GATEWAY_HOST}")
    yield
    await gateway.close()


app = FastAPI(
    title="Salus Bridge",
    description="REST API bridge for Salus iT600 heating system",
    version=__version__,
    lifespan=lifespan,
)


# Request models
class TemperatureRequest(BaseModel):
    temperature: float


class ModeRequest(BaseModel):
    mode: str  # "off", "heat", "auto"


class PresetRequest(BaseModel):
    preset: str  # "Follow Schedule", "Permanent Hold", "Off"


# Response models
class DeviceResponse(BaseModel):
    id: str
    name: str
    current_temperature: float | None
    target_temperature: float | None
    hvac_mode: str | None
    hvac_action: str | None
    preset_mode: str | None
    available: bool


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
    count: int


# Helper function
def device_to_response(device_id: str, device) -> DeviceResponse:
    return DeviceResponse(
        id=device_id,
        name=device.name,
        current_temperature=device.current_temperature,
        target_temperature=device.target_temperature,
        hvac_mode=device.hvac_mode,
        hvac_action=device.hvac_action,
        preset_mode=device.preset_mode,
        available=device.available,
    )


# Endpoints
@app.get("/")
async def root():
    return {"status": "ok", "gateway": GATEWAY_HOST}


@app.get("/devices", response_model=DeviceListResponse)
async def get_devices():
    """Get all climate devices."""
    await gateway.poll_status()
    devices = gateway.get_climate_devices()
    
    return DeviceListResponse(
        devices=[device_to_response(did, d) for did, d in devices.items()],
        count=len(devices),
    )


@app.get("/device/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str):
    """Get a single climate device."""
    await gateway.poll_status()
    device = gateway.get_climate_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    return device_to_response(device_id, device)


@app.post("/device/{device_id}/temperature")
async def set_temperature(device_id: str, request: TemperatureRequest):
    """Set target temperature for a device."""
    await gateway.poll_status()
    device = gateway.get_climate_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    await gateway.set_climate_device_temperature(device_id, request.temperature)
    
    return {
        "status": "ok",
        "device_id": device_id,
        "temperature": request.temperature,
    }


@app.post("/device/{device_id}/mode")
async def set_mode(device_id: str, request: ModeRequest):
    """Set HVAC mode (off/heat/auto)."""
    await gateway.poll_status()
    device = gateway.get_climate_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    valid_modes = ["off", "heat", "auto"]
    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid mode. Must be one of: {valid_modes}"
        )
    
    await gateway.set_climate_device_mode(device_id, request.mode)
    
    return {
        "status": "ok",
        "device_id": device_id,
        "mode": request.mode,
    }


@app.post("/device/{device_id}/preset")
async def set_preset(device_id: str, request: PresetRequest):
    """Set preset mode (Follow Schedule/Permanent Hold/Off)."""
    await gateway.poll_status()
    device = gateway.get_climate_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    valid_presets = ["Follow Schedule", "Permanent Hold", "Off"]
    if request.preset not in valid_presets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset. Must be one of: {valid_presets}"
        )
    
    await gateway.set_climate_device_preset(device_id, request.preset)
    
    return {
        "status": "ok",
        "device_id": device_id,
        "preset": request.preset,
    }


# Convenience endpoints for zones
class ZoneTemperatureRequest(BaseModel):
    device_ids: list[str]
    temperature: float


class ZonePresetRequest(BaseModel):
    device_ids: list[str]
    preset: str


@app.post("/zone/temperature")
async def set_zone_temperature(request: ZoneTemperatureRequest):
    """Set temperature for multiple devices (zone)."""
    await gateway.poll_status()
    
    results = []
    for device_id in request.device_ids:
        device = gateway.get_climate_device(device_id)
        if device:
            await gateway.set_climate_device_temperature(device_id, request.temperature)
            results.append({"device_id": device_id, "status": "ok"})
        else:
            results.append({"device_id": device_id, "status": "not_found"})
    
    return {
        "status": "ok",
        "temperature": request.temperature,
        "results": results,
    }


@app.post("/zone/preset")
async def set_zone_preset(request: ZonePresetRequest):
    """Set preset for multiple devices (zone)."""
    await gateway.poll_status()
    
    valid_presets = ["Follow Schedule", "Permanent Hold", "Off"]
    if request.preset not in valid_presets:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset. Must be one of: {valid_presets}"
        )
    
    results = []
    for device_id in request.device_ids:
        device = gateway.get_climate_device(device_id)
        if device:
            await gateway.set_climate_device_preset(device_id, request.preset)
            results.append({"device_id": device_id, "status": "ok"})
        else:
            results.append({"device_id": device_id, "status": "not_found"})
    
    return {
        "status": "ok",
        "preset": request.preset,
        "results": results,
    }
