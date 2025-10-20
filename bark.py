import requests
from typing import Iterable, List, Union


class BarkClient:
    def __init__(
        self,
        base_url: str,
        device_key: Union[str, Iterable[str]],
        group: str = "",
        sound: str = "",
        icon: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.device_keys = self._normalize_keys(device_key)
        self.group = group
        self.sound = sound
        self.icon = icon

    def send(self, title: str, body: str, url: str = "", group: str = None) -> bool:
        if not self.device_keys:
            print("Bark device keys missing, notification skipped")
            return False

        payload = {
            "title": title,
            "body": body,
        }

        if url:
            payload["url"] = url
        target_group = group if group is not None else self.group
        if target_group:
            payload["group"] = target_group
        if self.sound:
            payload["sound"] = self.sound
        if self.icon:
            payload["icon"] = self.icon

        results = []
        for key in self.device_keys:
            try:
                endpoint = f"{self.base_url}/{key}/"
                response = requests.post(endpoint, json=payload, timeout=10)
                if response.status_code // 100 == 2:
                    results.append(True)
                else:
                    print(f"Bark push failed ({key}): {response.status_code} {response.text}")
                    results.append(False)
            except Exception as exc:
                print(f"Bark push exception ({key}): {exc}")
                results.append(False)

        return any(results)

    def _normalize_keys(self, keys: Union[str, Iterable[str]]) -> List[str]:
        if isinstance(keys, str):
            return [keys.strip()] if keys.strip() else []
        normalized: List[str] = []
        for item in keys:
            item = (item or "").strip()
            if item:
                normalized.append(item)
        return normalized
