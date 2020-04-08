import uvicorn


class Server(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        pass
