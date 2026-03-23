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

    async def get_labs_raw(self) -> dict:
        """Get raw items data (labs and tasks).
        
        Returns the raw list from the API.
        """
        try:
            client = await self._get_client()
            response = await client.get("/items/")
            response.raise_for_status()
            return {"items": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_learners(self) -> dict:
        """Get list of enrolled learners.
        
        Returns a dict with 'learners' list or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/learners/")
            response.raise_for_status()
            return {"learners": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_scores_analytics(self, lab: str) -> dict:
        """Get score distribution analytics for a lab.
        
        Returns a dict with scores or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/scores", params={"lab": lab})
            response.raise_for_status()
            return {"scores": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_pass_rates(self, lab: str) -> dict:
        """Get per-task pass rates for a lab.
        
        Returns a dict with pass rates or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/pass-rates", params={"lab": lab})
            response.raise_for_status()
            return {"pass_rates": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_timeline(self, lab: str) -> dict:
        """Get submission timeline for a lab.
        
        Returns a dict with timeline data or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/timeline", params={"lab": lab})
            response.raise_for_status()
            return {"timeline": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_groups(self, lab: str) -> dict:
        """Get per-group performance for a lab.
        
        Returns a dict with group data or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/groups", params={"lab": lab})
            response.raise_for_status()
            return {"groups": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_top_learners(self, lab: str, limit: int = 5) -> dict:
        """Get top learners for a lab.
        
        Returns a dict with top learners or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/top-learners", params={"lab": lab, "limit": limit})
            response.raise_for_status()
            return {"top_learners": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_completion_rate(self, lab: str) -> dict:
        """Get completion rate for a lab.
        
        Returns a dict with completion rate or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/completion-rate", params={"lab": lab})
            response.raise_for_status()
            return {"completion_rate": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def trigger_sync(self) -> dict:
        """Trigger ETL pipeline sync.
        
        Returns a dict with sync status or 'error' message.
        """
        try:
            client = await self._get_client()
            response = await client.post("/pipeline/sync", json={})
            response.raise_for_status()
            return {"sync": response.json()}
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

# Task 2: Backend Integration - LMS API client
