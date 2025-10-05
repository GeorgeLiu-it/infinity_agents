import requests

class MCPClient:
    """
    Client to connect to MCP Personal Info Checker server.
    """
    def __init__(self, base_url: str):
        """
        :param base_url: URL of the MCP server, e.g., "http://192.168.1.100:8000"
        """
        self.base_url = base_url.rstrip("/")

    def check_email(self, email: str) -> dict:
        """
        Query MCP server by email.

        :param email: email string to query
        :return: dict of personal info if found
        :raises: ValueError if email not found or server error
        """
        url = f"{self.base_url}/check/"
        try:
            resp = requests.get(url, params={"email": email}, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 404:
                raise ValueError(f"Email {email} not found") from e
            else:
                raise RuntimeError(f"MCP server error: {resp.text}") from e
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error connecting to MCP server: {e}") from e
