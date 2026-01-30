# dpw

Die per wafer calculator（DPW 计算器）。

## 安装（含测试）

需要 `python3`（建议 3.9+）。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

运行测试：

```bash
python -m pytest
```

## VPS 上跑

在 VPS 上按同样步骤创建 venv 并安装，然后直接 `pytest` 即可。

## VPS 一键部署（推荐）

在你本机执行一条命令即可完成 VPS 上的 clone/pull + venv + 安装（可选跑测试）：

```bash
ssh user@vps 'bash -s -- --dir /opt/dpw --repo <YOUR_GIT_URL> --branch main --run-tests' < scripts/deploy_vps.sh
```

部署完成后：

- Python 解释器：`/opt/dpw/.venv/bin/python`
- 更新：重复执行同一条命令（会自动 pull 并重装）

## 飞书→VPS→调用 dpw 的测试建议

如果你的飞书 bot 是通过 `subprocess` 去调用远程 VPS 上的 `dpw`（或封装后的脚本），建议把“命令拼接/参数校验/超时/错误回传”抽成独立函数，然后：

- 单元测试：mock `subprocess.run`，覆盖成功/超时/非 0 退出码/输出过长等分支
- 集成测试：在 VPS 上跑一条真实命令（固定参数），断言返回 JSON 或关键字段
