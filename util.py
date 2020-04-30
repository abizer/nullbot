import asyncio
import traceback

def async_retry_except(coro):
    async def rerun_on_exception(*args, **kwargs):
        while True:
            try:
                await coro(*args, **kwargs)
            except asyncio.CancelledError:
                # don't interfere with cancellations
                raise
            except Exception:
                print("Caught exception")
                traceback.print_exc()

    return rerun_on_exception
