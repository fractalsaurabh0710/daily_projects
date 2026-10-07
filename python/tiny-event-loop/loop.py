"""A cooperative event loop in one file: generators, a heap, and a virtual clock.

asyncio's machinery is large, but the core idea is small. A task is a generator
that yields a *request* to the scheduler and gets suspended; the scheduler
decides when to resume it and with what value. Four requests are enough for
sleeping, spawning, and joining:

    yield None            -> yield the CPU, resume on the next turn
    yield Sleep(seconds)  -> resume once the clock reaches now + seconds
    yield Spawn(gen)      -> start gen as a task, resume with its Task handle
    yield Join(task)      -> resume with task's return value once it finishes

The clock is virtual: it jumps straight to the next deadline instead of
sleeping, so a program that waits two hours runs in microseconds and its
timings are exactly reproducible.
"""

import heapq
from dataclasses import dataclass, field
from typing import Any, Generator, List


@dataclass
class Sleep:
    seconds: float


@dataclass
class Spawn:
    coro: Generator


@dataclass
class Join:
    task: "Task"


@dataclass
class Task:
    coro: Generator
    name: str
    done: bool = False
    result: Any = None
    waiters: List["Task"] = field(default_factory=list)


class Loop:
    def __init__(self) -> None:
        self.now = 0.0
        self.trace: List[tuple] = []   # (virtual time, task name) per completion
        self._ready: list = []         # heap of (when, seq, task, value_to_send)
        self._seq = 0                  # tiebreaker: keeps the heap FIFO-stable

    # -- scheduling ---------------------------------------------------------
    def _schedule(self, task: Task, when: float = None, value: Any = None) -> None:
        heapq.heappush(self._ready, (self.now if when is None else when,
                                     self._seq, task, value))
        self._seq += 1

    def spawn(self, coro: Generator, name: str = None) -> Task:
        task = Task(coro, name or getattr(coro, "__name__", "task"))
        self._schedule(task)
        return task

    def run(self, coro: Generator) -> Any:
        """Run until every task is finished; return the main task's value."""
        main = self.spawn(coro, "main")
        while self._ready:
            when, _, task, value = heapq.heappop(self._ready)
            self.now = max(self.now, when)   # the clock only ever moves forward
            try:
                request = task.coro.send(value)
            except StopIteration as stop:
                self._finish(task, stop.value)
                continue
            self._handle(task, request)
        return main.result

    # -- the four requests --------------------------------------------------
    def _handle(self, task: Task, request: Any) -> None:
        if request is None:
            self._schedule(task)
        elif isinstance(request, Sleep):
            self._schedule(task, when=self.now + request.seconds)
        elif isinstance(request, Spawn):
            self._schedule(task, value=self.spawn(request.coro))
        elif isinstance(request, Join):
            if request.task.done:
                self._schedule(task, value=request.task.result)
            else:
                request.task.waiters.append(task)   # parked, not on the heap
        else:
            raise TypeError(f"{task.name} yielded something unknown: {request!r}")

    def _finish(self, task: Task, result: Any) -> None:
        task.done, task.result = True, result
        self.trace.append((round(self.now, 6), task.name))
        for waiter in task.waiters:
            self._schedule(waiter, value=result)
        task.waiters.clear()


def gather(*coros: Generator) -> Generator:
    """Run coros concurrently; return their results in argument order."""
    tasks = []
    for coro in coros:
        tasks.append((yield Spawn(coro)))
    results = []
    for task in tasks:
        results.append((yield Join(task)))
    return results


# -- tests ------------------------------------------------------------------
if __name__ == "__main__":
    def worker(name, delay):
        yield Sleep(delay)
        return f"{name} after {delay}"

    # 1. Concurrency: three 'slow' jobs take as long as the slowest, not the sum.
    def main():
        return (yield from gather(worker("a", 3), worker("b", 1), worker("c", 2)))

    loop = Loop()
    assert loop.run(main()) == ["a after 3", "b after 1", "c after 2"], "argument order"
    assert loop.now == 3, loop.now                      # not 1 + 2 + 3
    assert [t for t, _ in loop.trace][:3] == [1, 2, 3], loop.trace   # completion order

    # 2. A bare `yield` round-robins between tasks. Note the one-turn offset:
    #    `b` starts a turn behind `a` because each Spawn costs the parent a turn.
    log = []

    def counter(label, n):
        for i in range(n):
            log.append(f"{label}{i}")
            yield

    def interleave():
        a = yield Spawn(counter("a", 3))
        b = yield Spawn(counter("b", 3))
        yield Join(a)
        yield Join(b)

    Loop().run(interleave())
    assert log == ["a0", "a1", "b0", "a2", "b1", "b2"], log

    # 3. Joining a task that already finished returns its value immediately.
    def join_late():
        t = yield Spawn(worker("early", 1))
        yield Sleep(10)
        assert t.done
        return (yield Join(t))

    loop = Loop()
    assert loop.run(join_late()) == "early after 1"
    assert loop.now == 10

    # 4. Sleeps compose: sequential sleeps add up, nested spawns do not.
    def chain():
        yield Sleep(1.5)
        yield Sleep(2.5)

    def tree():
        yield from gather(chain(), chain(), worker("z", 0.5))

    loop = Loop()
    loop.run(tree())
    assert loop.now == 4.0, loop.now

    # 5. A task can wait on a task it did not spawn (two joiners, one result).
    def two_joiners():
        shared = yield Spawn(worker("shared", 2))
        both = yield from gather(_wait(shared), _wait(shared))
        return both

    def _wait(task):
        return (yield Join(task))

    loop = Loop()
    assert loop.run(two_joiners()) == ["shared after 2"] * 2
    assert loop.now == 2

    # 6. Unknown requests are a programming error, not silent breakage.
    def bad():
        yield 42

    try:
        Loop().run(bad())
    except TypeError as e:
        assert "unknown" in str(e)
    else:
        raise AssertionError("expected TypeError")

    print("all tests passed -- 6 scenarios, 0 real seconds slept")
