import requests
from typing import Optional


class PLMClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.session = requests.Session()

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def login(self, username: str, password: str) -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    def get_me(self) -> dict:
        resp = self.session.get(
            f"{self.base_url}/api/auth/me", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def search_parts(self, query: str = "") -> list:
        params = {}
        if query:
            params["search"] = query
        resp = self.session.get(
            f"{self.base_url}/api/parts/", headers=self._headers(), params=params
        )
        resp.raise_for_status()
        return resp.json()

    def get_part(self, part_id: str) -> dict:
        resp = self.session.get(
            f"{self.base_url}/api/parts/{part_id}", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def get_templates(self) -> list:
        resp = self.session.get(
            f"{self.base_url}/api/templates/", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def get_next_part_number(self, template_id: str, subsystem_code: str) -> dict:
        resp = self.session.get(
            f"{self.base_url}/api/parts/next-number",
            headers=self._headers(),
            params={"template_id": template_id, "subsystem_code": subsystem_code},
        )
        resp.raise_for_status()
        return resp.json()

    def check_part_number(self, number: str) -> dict:
        resp = self.session.get(
            f"{self.base_url}/api/parts/check-number",
            headers=self._headers(),
            params={"number": number},
        )
        resp.raise_for_status()
        return resp.json()

    def auto_create_part(
        self, name: str, part_type: str, subsystem: str,
        template_id: str, file_path: str
    ) -> dict:
        with open(file_path, "rb") as f:
            resp = self.session.post(
                f"{self.base_url}/api/parts/auto-create",
                headers={"Authorization": f"Bearer {self.token}"},
                data={"name": name, "type": part_type, "subsystem": subsystem, "template_id": template_id},
                files={"file": (file_path.split("\\")[-1].split("/")[-1], f)},
            )
        resp.raise_for_status()
        return resp.json()

    def checkout(self, part_id: str) -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/parts/{part_id}/checkout", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def checkin(self, part_id: str, file_path: str, comment: str = "") -> dict:
        with open(file_path, "rb") as f:
            resp = self.session.post(
                f"{self.base_url}/api/parts/{part_id}/checkin",
                headers={"Authorization": f"Bearer {self.token}"},
                data={"comment": comment},
                files={"file": (file_path.split("\\")[-1].split("/")[-1], f)},
            )
        resp.raise_for_status()
        return resp.json()

    def publish(self, part_id: str) -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/parts/{part_id}/publish", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()

    def unpublish(self, part_id: str, change_notice_id: str) -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/parts/{part_id}/unpublish",
            headers={"Authorization": f"Bearer {self.token}"},
            data={"change_notice_id": change_notice_id},
        )
        resp.raise_for_status()
        return resp.json()

    def download_file(self, part_id: str, save_path: str) -> str:
        resp = self.session.get(
            f"{self.base_url}/api/parts/{part_id}/download",
            headers=self._headers(),
            stream=True,
        )
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path

    def create_change_notice(self, part_id: str, title: str, reason: str, description: str = "") -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/change-notices/",
            headers=self._headers(),
            json={"part_id": part_id, "title": title, "reason": reason, "description": description},
        )
        resp.raise_for_status()
        return resp.json()

    def get_change_notices(self, part_id: str) -> list:
        resp = self.session.get(
            f"{self.base_url}/api/change-notices/",
            headers=self._headers(),
            params={"part_id": part_id},
        )
        resp.raise_for_status()
        return resp.json()

    def approve_change_notice(self, notice_id: str, approved: bool) -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/change-notices/{notice_id}/approve",
            headers=self._headers(),
            json={"approved": approved},
        )
        resp.raise_for_status()
        return resp.json()

    def upload_thumbnail(self, part_id: str, image_path: str) -> dict:
        with open(image_path, "rb") as f:
            resp = self.session.post(
                f"{self.base_url}/api/parts/{part_id}/thumbnail",
                headers={"Authorization": f"Bearer {self.token}"},
                files={"file": (image_path.split("\\")[-1].split("/")[-1], f)},
            )
        resp.raise_for_status()
        return resp.json()

    def get_thumbnail(self, part_id: str) -> Optional[bytes]:
        resp = self.session.get(
            f"{self.base_url}/api/parts/{part_id}/thumbnail",
            headers=self._headers(),
            stream=True,
        )
        if resp.status_code == 200:
            return resp.content
        return None

    def get_versions(self, part_id: str) -> list:
        resp = self.session.get(
            f"{self.base_url}/api/parts/{part_id}/versions", headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()
