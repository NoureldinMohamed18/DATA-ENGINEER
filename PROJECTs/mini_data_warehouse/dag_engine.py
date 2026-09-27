"""
dag_engine.py
--------------
A tiny Directed Acyclic Graph (DAG) execution engine, implementing the exact
algorithm described in the Data Pipeline material (Session 2):

    1. For each open (uncompleted) task:
       1.1 Check if all its upstream dependencies are completed.
       1.2 If so, add it to the execution queue.
    2. Execute every task in the queue, mark it completed.
    3. Repeat until all tasks are completed.

This is a simplified, single-process stand-in for what a real orchestrator
like Apache Airflow does. It's here to demonstrate the *concept* of DAG-based
execution (dependency resolution, no re-running the whole pipeline if only
one step changes) without requiring a full Airflow installation.

Usage as a library:

    dag = DAG()
    dag.add_task("extract_sales", extract_sales_fn)
    dag.add_task("extract_weather", extract_weather_fn)
    dag.add_task("transform", transform_fn, depends_on=["extract_sales", "extract_weather"])
    dag.run()
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Task:
    name: str
    func: Callable
    depends_on: list[str] = field(default_factory=list)
    completed: bool = False


class DAG:
    def __init__(self):
        self.tasks: dict[str, Task] = {}

    def add_task(self, name: str, func: Callable, depends_on: list[str] | None = None) -> None:
        self.tasks[name] = Task(name=name, func=func, depends_on=depends_on or [])

    def _validate_acyclic(self) -> None:
        """Basic cycle check using depth-first search, so we fail loudly instead
        of hanging in an infinite loop if someone creates a circular dependency."""
        visiting, visited = set(), set()

        def visit(name: str):
            if name in visited:
                return
            if name in visiting:
                raise ValueError(f"Cycle detected in DAG involving task '{name}'")
            visiting.add(name)
            for dep in self.tasks[name].depends_on:
                visit(dep)
            visiting.remove(name)
            visited.add(name)

        for task_name in self.tasks:
            visit(task_name)

    def run(self) -> None:
        """Executes tasks in dependency order, following the loop-based algorithm
        from the course material: find ready tasks, run them, repeat."""
        self._validate_acyclic()
        print(f"[DAG] Starting execution of {len(self.tasks)} tasks")

        loop_num = 0
        while not all(t.completed for t in self.tasks.values()):
            loop_num += 1
            ready_tasks = [
                t for t in self.tasks.values()
                if not t.completed and all(self.tasks[dep].completed for dep in t.depends_on)
            ]

            if not ready_tasks:
                remaining = [t.name for t in self.tasks.values() if not t.completed]
                raise RuntimeError(f"[DAG] Deadlock: no task is ready to run. Remaining: {remaining}")

            print(f"\n[DAG] Loop {loop_num}: ready tasks -> {[t.name for t in ready_tasks]}")
            for task in ready_tasks:
                print(f"[DAG]   Running '{task.name}'...")
                task.func()
                task.completed = True
                print(f"[DAG]   '{task.name}' completed.")

        print(f"\n[DAG] All {len(self.tasks)} tasks completed successfully.")
