# gitcheck

**提交前检查暂存区：冲突标记、超大文件、分支命名。**

`commit` 之前跑一遍，把那些"推上去才发现"的问题挡在本地。纯标准库，只读，可作 pre-commit 钩子或 CI 步骤。

[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Zero deps](https://img.shields.io/badge/dependencies-0-brightgreen)](#设计取舍)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![CI](https://github.com/eathink/gitcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/eathink/gitcheck/actions/workflows/ci.yml)

## 快速开始

```bash
pipx install git+https://github.com/eathink/gitcheck

git add .
gitcheck
```

```console
$ gitcheck --max-size 1K --branch-pattern '^feat/.*$'
检查 /home/me/project（分支 main，暂存 2 个文件）

[高] conflict.txt:1  存在冲突标记
[高] conflict.txt:3  存在冲突标记
[高] conflict.txt:5  存在冲突标记
[中] big.bin  2.0 KiB，超过上限 1.0 KiB
[中] main  分支名不符合命名规则

5 个问题
```

有发现返回 1，干净返回 0，可以直接当门禁。

## 检查项

| 检查 | 级别 | 说明 |
| --- | --- | --- |
| 冲突标记 | 高 | 暂存内容里还有 `<<<<<<<` / `=======` / `>>>>>>>` |
| 超大文件 | 中 | 暂存 blob 超过 `max_file_size`（默认 1 MiB） |
| 分支命名 | 中 | 当前分支不匹配 `branch_pattern`（未配置则跳过） |

- 只看**暂存区**，不扫描工作区或历史
- 文件大小取 git blob 的实际字节数，不是磁盘块占用
- 符号链接、子模块不参与大小检查
- detached HEAD 时跳过分支检查

## 配置

在仓库根放 `.gitcheck.json`：

```json
{
  "max_file_size": 1048576,
  "branch_pattern": "^(main|master|develop|(feat|fix|chore|docs|refactor|test)/[a-z0-9._-]+)$"
}
```

- `max_file_size`：正整数，单位字节
- `branch_pattern`：Python 正则，**必须匹配整个分支名**（`re.fullmatch`）；写前缀时记得加 `.*`
- 未知字段会报错，避免拼写错误静默生效

### 用法

```bash
gitcheck [PATH] [--config FILE] [--max-size SIZE] [--branch-pattern REGEX] [--format text|json]
```

| 参数 | 说明 |
| --- | --- |
| `PATH` | 仓库路径，默认当前目录 |
| `--config FILE` | 指定配置；默认读取仓库根的 `.gitcheck.json` |
| `--max-size SIZE` | 覆盖大小上限，支持 `1K` / `1.5M` / `2G` |
| `--branch-pattern REGEX` | 覆盖分支规则 |
| `-f, --format` | `text`（默认）或 `json` |
| `--version` | 版本号 |

### 退出码

| 码 | 含义 |
| --- | --- |
| 0 | 未发现问题 |
| 1 | 有问题 |
| 2 | 不是 git 仓库、配置错误或 git 调用失败 |

### 作为 pre-commit 钩子

`.git/hooks/pre-commit`：

```bash
#!/bin/sh
exec gitcheck --max-size 1M
```

```bash
chmod +x .git/hooks/pre-commit
```

## 设计取舍

- **只检查暂存区**：pre-commit 的职责是拦下"这次要提交的东西"，工作区里的无关改动不该导致失败
- **调用 git 而不是重写 git**：冲突标记交给 `git diff --cached --check`，文件大小用 `git cat-file --batch-check`，结果与 git 本身一致
- **默认不强制分支规范**：没有配置就不检查；团队想用再开
- **零依赖**：钩子应该在任何环境可运行，不该因为装不上依赖而失效

## 已知边界

- 不检查提交信息格式（pre-commit 阶段还没有信息；commit-msg 钩子是另一个场景）
- 不做密钥扫描（交给 `envscan` 这类专门工具）
- 不检查未跟踪文件、忽略规则或历史提交
- 分支正则使用 `fullmatch`，不是搜索

## 开发

```bash
git clone https://github.com/eathink/gitcheck
cd gitcheck

# 仅用标准库，无需安装依赖
PYTHONPATH=src python3 -m unittest discover -s tests -v

# 本地运行
PYTHONPATH=src python3 -m gitcheck . --format text
```

## License

[MIT](LICENSE)
