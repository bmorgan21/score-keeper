class ProxyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if "server" not in scope or "headers" not in scope:
            return await self.app(scope, receive, send)

        host, port = scope["server"]
        headers = []
        headers_seen = set()
        for header, value in scope["headers"]:
            if header != b"host":
                headers.append((header, value))

            if header == b"host" and b"x-forwarded-host" not in headers_seen:
                host = value.decode("utf-8")
            elif header == b"x-forwarded-host":
                host = value.decode("utf-8")
                headers_seen.add(header)
            elif header == b"x-forwarded-port":
                port = int(value)
            elif scope["scheme"] != "ws":
                if header == b"x-forwarded-proto":
                    scope["scheme"] = value.decode("utf-8")
                elif header == b"x-scheme":
                    scope["scheme"] = value.decode("utf-8")

        headers.append((b"host", host.encode("utf-8")))
        scope["headers"] = headers
        scope["server"] = (host, port)
        return await self.app(scope, receive, send)
