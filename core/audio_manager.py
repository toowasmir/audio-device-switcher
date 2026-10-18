import ctypes
from ctypes import wintypes, c_wchar_p, c_uint
from dataclasses import dataclass
from typing import List, Optional, Tuple
import comtypes
import comtypes.client
from comtypes import GUID, IUnknown, HRESULT, COMMETHOD

# --- GUIDs & Constants ---
CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
IID_IMMDeviceEnumerator = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")

CLSID_CPolicyConfigClient = GUID("{870af99c-171d-4f9e-af0d-e63df40c2bc9}")
IID_IPolicyConfig = GUID("{f8679f50-850a-41cf-9c72-430f290290c8}")

# Windows Core Audio Roles
class ERole:
    eConsole = 0
    eMultimedia = 1
    eCommunications = 2

# Data flow
E_RENDER = 0          # Audio rendering (playback)
DEVICE_STATE_ACTIVE = 1

ole32 = ctypes.windll.ole32


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [
        ("fmtid", GUID),
        ("pid", wintypes.DWORD)
    ]

PKEY_Device_FriendlyName = PROPERTYKEY(GUID("{A45C254E-DF1C-4EFD-8020-67D146A850E0}"), 14)
PKEY_DeviceInterface_FriendlyName = PROPERTYKEY(GUID("{026E516E-B814-414B-83CD-856D6FEF4822}"), 2)


class PROPVARIANT_UNION(ctypes.Union):
    _fields_ = [
        ("pwszVal", wintypes.LPWSTR),
        ("pszVal", ctypes.c_char_p),
        ("bstrVal", comtypes.BSTR),
        ("lVal", wintypes.LONG),
        ("ulVal", wintypes.ULONG),
        ("raw", ctypes.c_byte * 16)
    ]


class PROPVARIANT(ctypes.Structure):
    _fields_ = [
        ("vt", wintypes.WORD),
        ("wReserved1", wintypes.WORD),
        ("wReserved2", wintypes.WORD),
        ("wReserved3", wintypes.WORD),
        ("u", PROPVARIANT_UNION)
    ]


class IPropertyStore(IUnknown):
    _iid_ = GUID("{886d8eeb-8cf2-4446-8d02-cdba1dbdcf99}")
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount", (['out'], ctypes.POINTER(wintypes.DWORD), "cProps")),
        COMMETHOD([], HRESULT, "GetAt", (['in'], wintypes.DWORD, "iProp"), (['out'], ctypes.POINTER(PROPERTYKEY), "pkey")),
        COMMETHOD([], HRESULT, "GetValue", (['in'], ctypes.POINTER(PROPERTYKEY), "key"), (['out'], ctypes.POINTER(PROPVARIANT), "pv")),
        COMMETHOD([], HRESULT, "SetValue", (['in'], ctypes.POINTER(PROPERTYKEY), "key"), (['in'], ctypes.POINTER(PROPVARIANT), "propvar")),
        COMMETHOD([], HRESULT, "Commit"),
    ]


class IMMDevice(IUnknown):
    _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
    _methods_ = [
        COMMETHOD([], HRESULT, "Activate", (['in'], ctypes.POINTER(GUID), "iid"), (['in'], wintypes.DWORD, "dwClsCtx"), (['in'], ctypes.c_void_p, "pActivationParams"), (['out'], ctypes.POINTER(ctypes.c_void_p), "ppInterface")),
        COMMETHOD([], HRESULT, "OpenPropertyStore", (['in'], wintypes.DWORD, "stgmAccess"), (['out'], ctypes.POINTER(ctypes.POINTER(IPropertyStore)), "ppProperties")),
        COMMETHOD([], HRESULT, "GetId", (['out'], ctypes.POINTER(wintypes.LPWSTR), "ppstrId")),
        COMMETHOD([], HRESULT, "GetState", (['out'], ctypes.POINTER(wintypes.DWORD), "pdwState")),
    ]


class IMMDeviceCollection(IUnknown):
    _iid_ = GUID("{0BD7A1BE-7A1A-44DB-8397-CC5392387B5E}")
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount", (['out'], ctypes.POINTER(wintypes.UINT), "pcDevices")),
        COMMETHOD([], HRESULT, "Item", (['in'], wintypes.UINT, "nDevice"), (['out'], ctypes.POINTER(ctypes.POINTER(IMMDevice)), "ppDevice")),
    ]


class IMMDeviceEnumerator(IUnknown):
    _iid_ = IID_IMMDeviceEnumerator
    _methods_ = [
        COMMETHOD([], HRESULT, "EnumAudioEndpoints", (['in'], wintypes.DWORD, "dataFlow"), (['in'], wintypes.DWORD, "dwStateMask"), (['out'], ctypes.POINTER(ctypes.POINTER(IMMDeviceCollection)), "ppDevices")),
        COMMETHOD([], HRESULT, "GetDefaultAudioEndpoint", (['in'], wintypes.DWORD, "dataFlow"), (['in'], wintypes.DWORD, "role"), (['out'], ctypes.POINTER(ctypes.POINTER(IMMDevice)), "ppEndpoint")),
        COMMETHOD([], HRESULT, "GetDevice", (['in'], wintypes.LPCWSTR, "pwstrId"), (['out'], ctypes.POINTER(ctypes.POINTER(IMMDevice)), "ppDevice")),
        COMMETHOD([], HRESULT, "RegisterEndpointNotificationCallback", (['in'], ctypes.c_void_p, "pClient")),
        COMMETHOD([], HRESULT, "UnregisterEndpointNotificationCallback", (['in'], ctypes.c_void_p, "pClient")),
    ]


class IPolicyConfig(IUnknown):
    _iid_ = IID_IPolicyConfig
    _methods_ = [
        COMMETHOD([], HRESULT, "GetMixFormat", (['in'], c_wchar_p, "pszDeviceName"), (['out'], ctypes.c_void_p, "ppFormat")),
        COMMETHOD([], HRESULT, "GetDeviceFormat", (['in'], c_wchar_p, "pszDeviceName"), (['in'], wintypes.INT, "bDefault"), (['out'], ctypes.c_void_p, "ppFormat")),
        COMMETHOD([], HRESULT, "ResetDeviceFormat", (['in'], c_wchar_p, "pszDeviceName")),
        COMMETHOD([], HRESULT, "SetDeviceFormat", (['in'], c_wchar_p, "pszDeviceName"), (['in'], ctypes.c_void_p, "pEndpointFormat"), (['in'], ctypes.c_void_p, "pMixFormat")),
        COMMETHOD([], HRESULT, "GetProcessingPeriod", (['in'], c_wchar_p, "pszDeviceName"), (['in'], wintypes.INT, "bDefault"), (['out'], ctypes.c_void_p, "pmftDefaultPeriod"), (['out'], ctypes.c_void_p, "pmftMinimumPeriod")),
        COMMETHOD([], HRESULT, "SetProcessingPeriod", (['in'], c_wchar_p, "pszDeviceName"), (['in'], ctypes.c_void_p, "pmftPeriod")),
        COMMETHOD([], HRESULT, "GetShareMode", (['in'], c_wchar_p, "pszDeviceName"), (['out'], ctypes.c_void_p, "pMode")),
        COMMETHOD([], HRESULT, "SetShareMode", (['in'], c_wchar_p, "pszDeviceName"), (['in'], ctypes.c_void_p, "mode")),
        COMMETHOD([], HRESULT, "GetPropertyValue", (['in'], c_wchar_p, "pszDeviceName"), (['in'], ctypes.c_void_p, "pKey"), (['out'], ctypes.c_void_p, "pv")),
        COMMETHOD([], HRESULT, "SetPropertyValue", (['in'], c_wchar_p, "pszDeviceName"), (['in'], ctypes.c_void_p, "pKey"), (['in'], ctypes.c_void_p, "pv")),
        COMMETHOD([], HRESULT, "SetDefaultEndpoint", (['in'], c_wchar_p, "wszDeviceId"), (['in'], c_uint, "eRole")),
        COMMETHOD([], HRESULT, "SetEndpointVisibility", (['in'], c_wchar_p, "wszDeviceId"), (['in'], wintypes.INT, "bVisible")),
    ]


@dataclass
class AudioDevice:
    id: str
    name: str
    is_default: bool = False

    def __repr__(self):
        return f"<AudioDevice name='{self.name}' default={self.is_default}>"


class AudioManager:
    """Handles discovery, querying and switching of Windows playback audio devices."""

    def __init__(self):
        pass

    def _ensure_com(self):
        try:
            comtypes.CoInitialize()
        except Exception:
            pass

    def get_enumerator(self) -> IMMDeviceEnumerator:
        self._ensure_com()
        return comtypes.client.CreateObject(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator)

    def get_default_device_id(self) -> Optional[str]:
        """Returns endpoint ID of the current default console playback device."""
        try:
            enumerator = self.get_enumerator()
            default_endpoint = enumerator.GetDefaultAudioEndpoint(E_RENDER, ERole.eConsole)
            return default_endpoint.GetId()
        except Exception as e:
            print(f"[AudioManager] GetDefaultAudioEndpoint hatası: {e}")
            return None

    def get_active_devices(self) -> List[AudioDevice]:
        """Enumerates all currently active and connected playback devices."""
        devices: List[AudioDevice] = []
        try:
            enumerator = self.get_enumerator()
            current_default_id = self.get_default_device_id()
            collection = enumerator.EnumAudioEndpoints(E_RENDER, DEVICE_STATE_ACTIVE)
            count = collection.GetCount()

            for i in range(count):
                dev = collection.Item(i)
                dev_id = dev.GetId()

                # Read device name from property store
                store = dev.OpenPropertyStore(0) # STGM_READ = 0
                friendly_name = None
                try:
                    pv = store.GetValue(ctypes.byref(PKEY_Device_FriendlyName))
                    friendly_name = pv.u.pwszVal
                except Exception:
                    pass

                if not friendly_name:
                    try:
                        pv = store.GetValue(ctypes.byref(PKEY_DeviceInterface_FriendlyName))
                        friendly_name = pv.u.pwszVal
                    except Exception:
                        pass

                if not friendly_name:
                    friendly_name = f"Ses Cihazı ({dev_id[-8:]})"

                is_def = (dev_id == current_default_id)
                devices.append(AudioDevice(id=dev_id, name=friendly_name, is_default=is_def))

        except Exception as e:
            print(f"[AudioManager] Cihaz tarama hatası: {e}")

        return devices

    def set_default_device(self, device_id: str) -> bool:
        """Sets the specified device as Windows default for Console, Multimedia & Communications."""
        self._ensure_com()
        try:
            policy_config = comtypes.CoCreateInstance(
                CLSID_CPolicyConfigClient,
                interface=IPolicyConfig,
                clsctx=comtypes.CLSCTX_INPROC_SERVER
            )
            # Set for Console, Multimedia, Communications
            hr1 = policy_config.SetDefaultEndpoint(device_id, ERole.eConsole)
            hr2 = policy_config.SetDefaultEndpoint(device_id, ERole.eMultimedia)
            hr3 = policy_config.SetDefaultEndpoint(device_id, ERole.eCommunications)
            return (hr1 == 0 and hr2 == 0 and hr3 == 0)
        except Exception as e:
            print(f"[AudioManager] SetDefaultEndpoint hatası: {e}")
            return False

    def toggle_next_device(self, cycle_device_ids: Optional[List[str]] = None) -> Optional[Tuple[AudioDevice, int, int]]:
        """
        Switches to the next audio playback device.
        - If cycle_device_ids is given, cycles only among those devices.
        - If exactly 2 devices are in the cycle, acts as direct A/B toggle.
        - If > 2 devices, cycles sequentially (0 -> 1 -> 2 -> ... -> 0).
        - Skips any disconnected or missing devices automatically.

        Returns: (AudioDevice, current_1_based_index, total_count) or None.
        """
        all_active = self.get_active_devices()
        if not all_active:
            print("[AudioManager] Etkin ses aygıtı bulunamadı.")
            return None

        # Build candidate list based on user cycle selection
        if cycle_device_ids:
            active_dict = {d.id: d for d in all_active}
            candidates = [active_dict[did] for did in cycle_device_ids if did in active_dict]
            # Fallback to all active if selected devices are currently disconnected
            if not candidates:
                candidates = all_active
        else:
            candidates = all_active

        total_count = len(candidates)
        if total_count == 0:
            return None

        current_default_id = self.get_default_device_id()

        # Find current index in candidates
        current_index = -1
        for idx, dev in enumerate(candidates):
            if dev.id == current_default_id:
                current_index = idx
                break

        # Calculate next index
        if total_count == 1:
            next_index = 0
        elif total_count == 2:
            # A/B Toggle:
            # If current is A (0) -> B (1)
            # If current is B (1) -> A (0)
            # If current is neither -> A (0)
            if current_index == 0:
                next_index = 1
            else:
                next_index = 0
        else:
            # Cycle through N devices
            if current_index == -1:
                next_index = 0
            else:
                next_index = (current_index + 1) % total_count

        target_device = candidates[next_index]

        # Apply switch
        success = self.set_default_device(target_device.id)
        if success:
            target_device.is_default = True
            return target_device, next_index + 1, total_count
        else:
            # In case the target failed (e.g. unplugged right now), try remaining candidates
            for idx, alt_device in enumerate(candidates):
                if alt_device.id != target_device.id:
                    if self.set_default_device(alt_device.id):
                        alt_device.is_default = True
                        return alt_device, idx + 1, total_count

        return None
