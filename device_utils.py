"""
Device detection and capability probing
Automatically detects hardware and optimizes for device type
"""
import platform
import psutil
import os
from dataclasses import dataclass


@dataclass
class DeviceCapabilities:
    device_type: str  # 'laptop', 'raspberry_pi', 'android', 'mac'
    cpu_cores: int
    ram_gb: float
    has_gpu: bool
    is_arm: bool
    is_low_power: bool
    
    recommended_detection: str  # 'mediapipe_full', 'mediapipe_lite', 'framediff'
    max_streams: int
    batch_size: int


def detect_device() -> DeviceCapabilities:
    """
    Detect device type and capabilities
    """
    system = platform.system()
    machine = platform.machine()
    
    cpu_cores = psutil.cpu_count()
    ram_gb = psutil.virtual_memory().total / (1024**3)
    is_arm = machine in ['armv7l', 'armv8l', 'aarch64', 'arm64']
    
    # Check GPU availability (basic check)
    has_gpu = _check_gpu()
    
    # Detect device type
    device_type = _detect_device_type(system, machine, ram_gb)
    is_low_power = device_type in ['raspberry_pi', 'android']
    
    # Recommend detection mode based on hardware
    if cpu_cores >= 8 and ram_gb >= 4 and has_gpu:
        recommended_detection = 'mediapipe_full'
        batch_size = 8
        max_streams = 2
    elif cpu_cores >= 4 and ram_gb >= 2:
        recommended_detection = 'mediapipe_lite'
        batch_size = 4
        max_streams = 1
    elif is_arm and ram_gb >= 1:
        recommended_detection = 'mediapipe_lite'
        batch_size = 2
        max_streams = 1
    else:
        recommended_detection = 'framediff'
        batch_size = 1
        max_streams = 1
    
    return DeviceCapabilities(
        device_type=device_type,
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        has_gpu=has_gpu,
        is_arm=is_arm,
        is_low_power=is_low_power,
        recommended_detection=recommended_detection,
        max_streams=max_streams,
        batch_size=batch_size
    )


def _detect_device_type(system: str, machine: str, ram_gb: float) -> str:
    """Detect device type from system info"""
    
    # Check if Raspberry Pi
    if os.path.exists('/proc/cpuinfo'):
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'BCM' in cpuinfo or 'ARMv7' in cpuinfo or 'ARMv8' in cpuinfo:
                    return 'raspberry_pi'
        except:
            pass
    
    # Check if Android (Termux)
    if 'ANDROID_ROOT' in os.environ or 'TERMUX_APP_PID' in os.environ:
        return 'android'
    
    # Check if Mac
    if system == 'Darwin':
        return 'mac'
    
    # Check if Linux
    if system == 'Linux':
        return 'linux_server'
    
    # Default to laptop/desktop
    if system == 'Windows':
        return 'windows_laptop'
    
    return 'laptop'


def _check_gpu() -> bool:
    """
    Check if GPU is available
    Supports CUDA (NVIDIA) and Metal (Apple)
    """
    try:
        import torch
        return torch.cuda.is_available()
    except:
        pass
    
    # Check for Apple Silicon
    try:
        import torch
        return hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    except:
        pass
    
    return False


def print_device_info():
    """Print device capabilities for debugging"""
    caps = detect_device()
    
    print("\n" + "="*60)
    print("🖥️  DEVICE CAPABILITIES")
    print("="*60)
    print(f"Device Type:        {caps.device_type}")
    print(f"CPU Cores:          {caps.cpu_cores}")
    print(f"RAM:                {caps.ram_gb:.1f} GB")
    print(f"GPU Available:      {caps.has_gpu}")
    print(f"ARM Architecture:   {caps.is_arm}")
    print(f"Low Power Mode:     {caps.is_low_power}")
    print(f"\nRecommended Settings:")
    print(f"  Detection Mode:   {caps.recommended_detection}")
    print(f"  Max Streams:      {caps.max_streams}")
    print(f"  Batch Size:       {caps.batch_size}")
    print("="*60 + "\n")


if __name__ == '__main__':
    print_device_info()
