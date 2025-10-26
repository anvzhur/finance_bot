# --api_client.py--
import aiohttp
from config import BASE_URL, HEADERS
from typing import List, Dict, Any

class ReportFinanceAPI:
    def __init__(self, api_key: str):
        self.base_url = BASE_URL.rstrip()
        self.headers = {
            "accept": "application/json",
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

    async def get_projects(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        params = {"offset": offset, "limit": limit}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/Projects",
                headers=self.headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    raise PermissionError("Ошибка авторизации: проверьте API-ключ")
                else:
                    resp.raise_for_status()

    async def fetch_all_projects(self) -> List[Dict[str, Any]]:
        all_projects = []
        offset = 0
        limit = 100
        while True:
            data = await self.get_projects(offset=offset, limit=limit)
            projects = data.get("listProject", [])
            all_projects.extend(projects)
            total = data.get("totalLineCount", 0)
            if not projects or offset + limit >= total:
                break
            offset += limit
        return all_projects

    async def get_accounts(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        params = {"offset": offset, "limit": limit}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/Accounts",
                headers=self.headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    raise PermissionError("Ошибка авторизации при загрузке счетов")
                else:
                    resp.raise_for_status()

    async def fetch_all_accounts(self) -> List[Dict[str, Any]]:
        all_accounts = []
        offset = 0
        limit = 100
        while True:
            data = await self.get_accounts(offset=offset, limit=limit)
            accounts = data.get("listAccount", [])
            all_accounts.extend(accounts)
            total = data.get("totalLineCount", 0)
            if not accounts or offset + limit >= total:
                break
            offset += limit
        return all_accounts

    async def get_organisations(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        params = {"offset": offset, "limit": limit}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/Organisations",
                headers=self.headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    raise PermissionError("Ошибка авторизации при загрузке организаций")
                else:
                    resp.raise_for_status()

    async def fetch_all_organisations(self) -> List[Dict[str, Any]]:
        all_orgs = []
        offset = 0
        limit = 100
        while True:
            data = await self.get_organisations(offset=offset, limit=limit)
            orgs = data.get("listOrganisation", [])
            all_orgs.extend(orgs)
            total = data.get("totalLineCount", 0)
            if not orgs or offset + limit >= total:
                break
            offset += limit
        return all_orgs

    async def get_fact_streams(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/FactStreams",
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 401:
                    raise PermissionError("Ошибка авторизации при загрузке фактических статей")
                else:
                    resp.raise_for_status()

    async def fetch_all_fact_streams(self) -> List[Dict[str, Any]]:
        return await self.get_fact_streams()

    async def create_payment(self, payment_data: Dict[str, Any]) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/Payments",
                headers=self.headers,
                json=[payment_data],
                params={"isRunRules": "false"}
            ) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    error_text = await resp.text()
                    raise RuntimeError(f"Ошибка API ({resp.status}): {error_text}")