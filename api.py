import strawberry
import asyncio
import asyncio.subprocess as subprocess
from asyncio import streams
from typing import Any, AsyncGenerator, AsyncIterator, Coroutine, Optional


async def wait_for_call(coro: Coroutine[Any, Any, bytes]) -> Optional[bytes]:
    """
    wait_for_call calls the the supplied coroutine in a wait_for block.

    This mitigates cases where the coroutine doesn't yield until it has
    completed its task. In this case, reading a line from a StreamReader; if
    there are no `\n` line chars in the stream the function will never exit
    """
    try:
        return await asyncio.wait_for(coro(), timeout=0.1)
    except asyncio.TimeoutError:
        pass


async def lines(stream: streams.StreamReader) -> AsyncIterator[str]:
    """
    lines reads all lines from the provided stream, decoding them as UTF-8
    strings.
    """
    while True:
        b = await wait_for_call(stream.readline)
        if b:
            yield b.decode("UTF-8").rstrip()
        else:
            break


async def exec_proc(target: int) -> subprocess.Process:
    """
    exec_proc starts a sub process and returns the handle to it.
    """
    return await asyncio.create_subprocess_exec(
        "/bin/bash",
        "-c",
        f"for ((i = 0 ; i < {target} ; i++)); do echo $i; sleep 0.2; done",
        stdout=subprocess.PIPE,
    )


async def tail(proc: subprocess.Process) -> AsyncGenerator[str, None]:
    """
    tail reads from stdout until the process finishes
    """
    # Note: race conditions are possible here since we're in a subprocess. In
    # this case the process can finish between the loop predicate and the call
    # to read a line from stdout. This is a good example of why you need to
    # be defensive by using asyncio.wait_for in wait_for_call().
    while proc.returncode is None:
        async for l in lines(proc.stdout):
            yield l
    else:
        # read anything left on the pipe after the process has finished
        async for l in lines(proc.stdout):
            yield l

@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def run_command(self, target: int = 100) -> AsyncGenerator[str, None]:
        proc = await exec_proc(target)
        return tail(proc)


schema = strawberry.Schema(query=Query, subscription=Subscription)