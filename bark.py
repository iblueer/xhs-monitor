import requests


class BarkClient:
    def __init__(self, base_url: str, device_key: str, group: str = "", sound: str = "", icon: str = ""):
        self.base_url = base_url.rstrip("/")
        self.device_key = device_key
        self.group = group
        self.sound = sound
        self.icon = icon

    def send(self, title: str, body: str, url: str = "", group: str = None) -> bool:
        if not self.device_key:
            print("Bark device key missing, notification skipped")
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

        try:
            endpoint = f"{self.base_url}/{self.device_key}/"
            response = requests.post(endpoint, json=payload, timeout=10)
            if response.status_code // 100 == 2:
                return True
            print(f"Bark push failed: {response.status_code} {response.text}")
        except Exception as exc:
            print(f"Bark push exception: {exc}")
        return False
