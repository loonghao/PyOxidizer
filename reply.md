已全面审计了 `.github/workflows/` 下全部 9 个 workflow 文件，以下是升级方案：

## 过时流水线诊断

| 问题 | 严重度 | 涉及文件数 |
|------|--------|-----------|
| `macos-13` runner 即将退役（GitHub 已宣布逐步下线 Intel macOS runner） | 高 | 7 个 workflow |
| `ubuntu-22.04` runner 较旧，不统一 | 中 | 7 个 workflow |
| `sign-apple-exe.yml` 引用不存在的 `rcodesign.yml` | 中 | 1 个 |
| macOS wheel 只构建 x86_64，缺少 aarch64 | 中 | 1 个 |
| `cargo-deny-action@v2` 可升级到 v3 | 低 | 1 个 |

## 升级计划

1. **macOS runner**: `macos-13` → `macos-14`（Apple Silicon M 系列），同时调整交叉编译逻辑
2. **Ubuntu runner**: 统一 `ubuntu-22.04` → `ubuntu-24.04`
3. **移除或修复 `sign-apple-exe.yml`**（引用不存在的 workflow，且我们不需要 Apple 签名）
4. **macOS wheel 增加 aarch64** 构建

由于我们不支持 Mac 机器，可以考虑两种策略：
- **策略 A**: 移除所有 macOS job，只保留 Linux + Windows 构建
- **策略 B**: 将 macOS runner 升级到 `macos-14`（GitHub 托管，无需自建 Mac）

请确认方向，我马上开始改。
