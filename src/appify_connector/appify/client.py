import json
import logging

import httpx

from ..config import Settings
from ..exceptions import AppifyAuthError, AppifyUpstreamError, ObjectNotFound
from ..session_store import UpstreamSession
from .schema import RawField, RawObject, RawSor

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class AppifyClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def login(self, business_name: str, email: str, password: str) -> UpstreamSession:
        url = f"{self._settings.appify_login_url.rstrip('/')}/api/toc/flex/login"
        payload = {"body": {"businessName": business_name, "email": email, "password": password}}
        headers = {
            "Content-Type": "application/json",
            "Authorization": self._settings.appify_gateway_auth,
        }
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
            except httpx.RequestError as err:
                raise AppifyUpstreamError(f"Could not reach Appify login: {err}") from err

        if resp.status_code != 200:
            logger.warning(
                "Appify login non-200: status=%s body=%s", resp.status_code, _truncate(resp.text)
            )
            msg = _extract_message(resp) or f"HTTP {resp.status_code}: {_truncate(resp.text)}"
            if resp.status_code in (401, 403):
                raise AppifyAuthError(msg)
            raise AppifyUpstreamError(f"Appify login upstream error: {msg}")

        data = resp.json()
        users = data.get("users") or []
        if not users:
            raise AppifyAuthError("Appify login response missing user")
        user = users[0]

        iam_keys_raw = data.get("iamKeys")
        if not iam_keys_raw:
            raise AppifyAuthError("Appify login response missing iamKeys")
        try:
            iam_keys = json.loads(iam_keys_raw).get("IAMKeys", [])
        except (TypeError, ValueError) as err:
            raise AppifyAuthError("Appify login response: malformed iamKeys") from err
        studio = next((k for k in iam_keys if k.get("group") == "studio"), None)
        if not studio:
            raise AppifyAuthError("Appify login response missing studio IAM key")

        return UpstreamSession(
            instance_url=data["instanceUrl"],
            tac_id=data["tacId"],
            user_id=str(user["id"]),
            upstream_jwt=user["jwtToken"],
            iam_access_id=studio["iam_access_id"],
            iam_access_secret=studio["iam_access_key"],
            business_name=business_name,
            user_email=email,
        )

    async def list_sors(self, session: UpstreamSession) -> list[RawSor]:
        data = await self._get(session, "/sor")
        return [RawSor.model_validate(item) for item in (data or [])]

    async def list_objects(self, session: UpstreamSession, sor: str | None = None) -> list[RawObject]:
        sor_short = sor or "flex"
        data = await self._get(session, f"/signActionAddIn/{sor_short}/businessobjects")
        return [RawObject.model_validate(item) for item in (data or [])]

    async def describe_object(
        self, session: UpstreamSession, native_api_name: str
    ) -> tuple[RawObject, list[RawField]]:
        objects = await self.list_objects(session)
        match = next((o for o in objects if o.native_api_name == native_api_name), None)
        if match is None:
            raise ObjectNotFound(f"Object '{native_api_name}' not found")
        data = await self._get(session, f"/getFieldsByObjName/{match.flex_name}")
        fields = [RawField.model_validate(item) for item in (data or [])]
        return match, fields

    async def get_me(
        self, session: UpstreamSession
    ) -> tuple[dict, dict | None, list[dict]]:
        async with self._http(session) as client:
            try:
                details_resp = await client.get("/getLoggedInUserDetails")
                if details_resp.status_code >= 400:
                    raise AppifyUpstreamError(
                        f"getLoggedInUserDetails {details_resp.status_code}: {_truncate(details_resp.text)}"
                    )
                details = details_resp.json()

                profile_id = details.get("profileID")
                profile_meta: dict | None = None
                permissions: list[dict] = []
                if profile_id:
                    perms_resp = await client.get(
                        f"/flex/profile/permissions?profiles={profile_id}"
                    )
                    if perms_resp.status_code == 200:
                        data = perms_resp.json()
                        records = data if isinstance(data, list) else (data.get("records") or [])
                        if records:
                            rec = records[0]
                            profile_meta = {
                                "id": profile_id,
                                "name": rec.get("profileName"),
                                "title": rec.get("title"),
                                "description": rec.get("description"),
                            }
                            permissions = rec.get("permissions") or []
            except httpx.RequestError as err:
                raise AppifyUpstreamError(f"Appify upstream unreachable: {err}") from err
        return details, profile_meta, permissions

    async def _get(self, session: UpstreamSession, path: str) -> object:
        async with self._http(session) as client:
            try:
                resp = await client.get(path)
            except httpx.RequestError as err:
                raise AppifyUpstreamError(f"Appify upstream unreachable: {err}") from err
        if resp.status_code == 401:
            raise AppifyAuthError("Upstream rejected authentication")
        if resp.status_code >= 400:
            raise AppifyUpstreamError(
                f"Appify upstream {resp.status_code} on {path}: {_truncate(resp.text)}"
            )
        return resp.json()

    def _http(self, session: UpstreamSession) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=session.instance_url,
            auth=(session.iam_access_id, session.iam_access_secret),
            headers={
                "X-Tenant-Id": session.tac_id,
                "X-User-Id": session.user_id,
                "XF-Session-Id": session.upstream_jwt,
                "Accept": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
        )


def _extract_message(resp: httpx.Response) -> str | None:
    try:
        body = resp.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        return body.get("message") or body.get("error")
    return None


def _truncate(text: str, limit: int = 200) -> str:
    return text if len(text) <= limit else text[:limit] + "…"
