const ws = new WebSocket("{url}");
ws.onmessage = () => window.location.reload();
