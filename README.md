# Infinity Agents

## Components

### Run mcp remote server docker container

```bash
docker run -dit --name remote-mcp-server -v ~/mcp_server:/app -w /app  -p 8000:8000 python:3.12.11-slim-bookworm
```

### Start mcp client in 20.5.137.123

```bash
source .venv/bin/activate
sudo /home/george/mcp_langchain/.venv/bin/python server.py
```

### Start local mcp server using weather.py in 20.5.137.123

```bash
source .venv/bin/activate
python server/weather.py
```

### Remote mcp server running as container in 106.13.91.222

### Remote 3rd party service running as container in 106.13.91.222

### Postgres:18 running as container in 106.13.91.222
