"""Validate real HTTP and A2A Compose services without benchmarking the host."""

import asyncio
import os

from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.supervisor import NullProbe, supervise
from agent_boundary_bench.domain.credit import fixture


async def main() -> None:
    """Use both clients against the declared network endpoints."""
    values = []
    for scenario, url in (
        ("http", os.getenv("ABB_HTTP_URL", "http://http:8100")),
        ("a2a", os.getenv("ABB_A2A_URL", "http://a2a:8100")),
    ):
        delegate = RemoteDelegate(url, scenario, NullProbe(), False, 5)
        try:
            await delegate.prepare()
            result = await supervise(delegate, fixture(1024), 0, False, 5, NullProbe())
            values.append([value.result for value in result.invocations])
        finally:
            await delegate.close()
    if values[0] != values[1]:
        raise ValueError("Compose business results differ")
    print("HTTP and A2A services are functionally equivalent")


if __name__ == "__main__":
    asyncio.run(main())
