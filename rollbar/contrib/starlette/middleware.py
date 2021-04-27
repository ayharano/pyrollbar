import logging
import sys

from starlette.requests import Request
from starlette.types import Receive, Scope, Send

import rollbar
from rollbar.contrib.asgi import ASGIMiddleware
from rollbar.contrib.starlette.requests import store_current_request
from rollbar.lib._async import RollbarAsyncError, try_report

log = logging.getLogger(__name__)


class StarletteMiddleware(ASGIMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            store_current_request(scope, receive)
            await self.app(scope, receive, send)
        except Exception:
            if scope['type'] == 'http':
                request = Request(scope, receive, send)

                # Consuming the request body in Starlette middleware is problematic
                # See: https://github.com/encode/starlette/issues/495#issuecomment-494008175
                # Uncomment line below if you know the risk
                # await request.body()

                exc_info = sys.exc_info()

                try:
                    await try_report(exc_info, request)
                except RollbarAsyncError:
                    log.warn(
                        f'Detected {rollbar.SETTINGS["handler"]} handler while'
                        f' reporting via {self.__class__.__name__}.'
                        ' Recommended handler settings: default or async.'
                    )

                    rollbar.report_exc_info(exc_info, request)
            raise
