"""
Pydantic models for system information endpoints
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoadAverage(BaseModel):
    """System load average over different time periods"""
    one_min: float = Field(..., alias="1min", description="Load average over 1 minute")
    five_min: float = Field(..., alias="5min", description="Load average over 5 minutes")
    fifteen_min: float = Field(..., alias="15min", description="Load average over 15 minutes")
    
    class Config:
        populate_by_name = True


class CPUInfo(BaseModel):
    """CPU usage and performance information"""
    usage_percent: float = Field(..., description="Overall CPU usage percentage")
    per_core: list[float] = Field(..., description="CPU usage per core")
    cores: int = Field(..., description="Number of CPU cores")
    frequency_mhz: Optional[float] = Field(None, description="Current CPU frequency in MHz")
    load_average: LoadAverage = Field(..., description="System load averages")


class MemoryInfo(BaseModel):
    """Memory usage information"""
    total_gb: float = Field(..., description="Total memory in GB")
    used_gb: float = Field(..., description="Used memory in GB")
    available_gb: float = Field(..., description="Available memory in GB")
    percent: float = Field(..., description="Memory usage percentage")


class SwapInfo(BaseModel):
    """Swap memory information"""
    total_gb: float = Field(..., description="Total swap in GB")
    used_gb: float = Field(..., description="Used swap in GB")
    percent: float = Field(..., description="Swap usage percentage")


class DiskInfo(BaseModel):
    """Disk usage information"""
    total_gb: float = Field(..., description="Total disk space in GB")
    used_gb: float = Field(..., description="Used disk space in GB")
    free_gb: float = Field(..., description="Free disk space in GB")
    percent: float = Field(..., description="Disk usage percentage")


class TemperatureInfo(BaseModel):
    """System temperature information"""
    celsius: float = Field(..., description="Temperature in Celsius")
    fahrenheit: float = Field(..., description="Temperature in Fahrenheit")
    sensor: Optional[str] = Field(None, description="Temperature sensor name")


class UptimeInfo(BaseModel):
    """System uptime information"""
    seconds: int = Field(..., description="Uptime in seconds")
    hours: float = Field(..., description="Uptime in hours")
    boot_time: str = Field(..., description="System boot time (ISO format)")


class CameraInfo(BaseModel):
    """Camera streaming information"""
    active_streams: int = Field(..., description="Number of active camera streams")
    total_viewers: int = Field(..., description="Total number of viewers across all streams")
    total_cameras: int = Field(..., description="Total number of cameras configured")


class SystemInfo(BaseModel):
    """Complete system information response"""
    timestamp: str = Field(..., description="Current timestamp (ISO format)")
    cpu: CPUInfo = Field(..., description="CPU information")
    memory: MemoryInfo = Field(..., description="Memory information")
    swap: SwapInfo = Field(..., description="Swap memory information")
    disk: DiskInfo = Field(..., description="Disk usage information")
    temperature: Optional[TemperatureInfo] = Field(None, description="System temperature information")
    uptime: UptimeInfo = Field(..., description="System uptime information")
    cameras: CameraInfo = Field(..., description="Camera streaming information")
