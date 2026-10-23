# Benchmark tasks

Ten small coding tasks (`t01`..`t10`) for comparing agent setups. t01-t06 can be solved by reading
the files; t07-t10 (`needs_execution: true`) need information that only exists at runtime, so a
system that cannot run code cannot solve them.

```
bench/tasks/tNN-short-name/
  task.json          id, title, prompt, difficulty (easy|medium|hard), needs_execution, why
  workspace/         starting project files the agent sees (plain Python 3.12, stdlib only)
  hidden/test_hidden.py   pytest checker; never copied into the workspace while the agent runs
  solution/          oracle fix: full-file overlays onto workspace/
  setup.py           optional: def setup(workspace: Path, task_dir: Path) -> None
  private/           optional: inputs for setup.py that must never be visible to the agent
```

Runner contract: copy `workspace/` to a sandbox, run `setup()` if present, let the system work,
then run `python -m pytest -q <task>/hidden -p no:cacheprovider` with cwd = sandbox and
`PYTHONPATH` = sandbox. The hidden test must fail on the untouched sandbox and pass with
`solution/` overlaid; `tests/test_bench_tasks.py` checks this for every task.
