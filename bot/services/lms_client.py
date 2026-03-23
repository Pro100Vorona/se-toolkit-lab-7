"""LMS API client — makes HTTP requests to the backend."""

import httpx
from typing import Optional


class LMSClient:
    """Client for the LMS backend API.
    
    Uses Bearer token authentication. All URLs and keys come from config.
    """
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def health_check(self) -> dict:
        """Check if the backend is healthy.
        
        Returns a dict with 'status' and optional 'message' or 'error'.
        """
        try:
            client = await self._get_client()
            response = await client.get("/items/")
            response.raise_for_status()
            data = response.json()
            item_count = len(data) if isinstance(data, list) else 0
            return {"status": "healthy", "item_count": item_count}
        except httpx.ConnectError as e:
            return {"status": "error", "error": f"connection refused ({self.base_url}). Check that the services are running."}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."}
        except httpx.TimeoutException:
            return {"status": "error", "error": f"timeout connecting to {self.base_url}. The backend may be overloaded."}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_labs(self) -> dict:
        """Get list of available labs.
        
        Returns a dict with 'labs' list or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/items/")
            response.raise_for_status()
            data = response.json()
            
            # Parse the response — filter for labs and extract titles
            labs = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("type") == "lab":
                        title = item.get("title", "Unknown Lab")
                        labs.append(title)
            
            return {"labs": labs}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_scores(self, lab: str) -> dict:
        """Get pass rates for a specific lab.
        
        Returns a dict with 'scores' list or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/pass-rates", params={"lab": lab})
            response.raise_for_status()
            data = response.json()
            
            # Parse the response — adjust based on actual API format
            scores = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        task = item.get("task", item.get("name", "Unknown"))
                        rate = item.get("pass_rate", item.get("rate", 0))
                        attempts = item.get("attempts", 0)
                        scores.append({"task": task, "pass_rate": rate, "attempts": attempts})
            
            return {"scores": scores, "lab": lab}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
