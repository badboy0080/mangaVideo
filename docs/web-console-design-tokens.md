# 漫剧流水线 Web 控制台 — 设计语言速查

面向 **PM / 非设计师**：下面这些词决定页面「长得像谁」。[**设计令牌（Design tokens）**](https://en.wikipedia.org/wiki/Design_system)：把颜色、圆角等抽成命名变量，一改全站跟着变。

## 一句话气质

**暗色工作台 + 大块低对比分层 + 两处彩色信号**：暖色点主操作（[`--accent-warm`](../web/src/index.css)）、冷蓝点信息与链接焦点（[`--accent-cool`](../web/src/index.css)）。

**UI-rich**：界面里控件多（侧栏、步骤卡、日志），不是靠大图讲故事。

字体：**Geist Variable**（可变字体），见 [`web/src/index.css`](../web/src/index.css) 里的 `.theme`。

## 语义颜色（必读）

| 令牌 | 作用 |
|------|------|
| `--background` | 整张页面底色 |
| `--card` | 卡片 / 条形工具区底色，比画布略「抬」一层 |
| `--foreground` | 主文字 |
| `--muted-foreground` | 说明次要文字 |
| `--border` / `--input` | 分割线、输入框边界（刻意很弱） |
| `--primary` | 默认实心按钮（本项目里是中灰面，不占彩） |
| `--accent-warm` | 「创建」「新建」等暖色 CTA |
| `--accent-cool` | 链接色、选中环、次要强调 |

破坏态仍用 **`--destructive`**；其上可读文字 **`--destructive-foreground`** 仍是 **不带 `oklch` 的 hsl 分量**（形如 `210 40% 98%`），与其它令牌的写法不同。

## Tailwind 怎么接 CSS 变量

语义色写在 [`web/tailwind.config.js`](../web/tailwind.config.js)：**值里已是完整颜色的写 `var(--xxx)`**，不要外面再包一层 **`hsl()`**，否则 **`hsl(oklch(...))`** 在浏览器里是非法值，整块颜色会失效。

## 分割线（细线）

需要「一条很淡的分割线」时用工具类 **`border-line-soft`**（定义在 [`web/src/index.css`](../web/src/index.css)）：把当前主题的 `--foreground` 与透明做 **`color-mix`**，明暗模式都会自动合拍，不会出现刺眼的白线框。

## 组件约定

| 控件 | Variant | 语义 |
|------|---------|------|
| `Button` | `cta` | 主流程显眼操作 |
| `Button` | `cool` | 单步「执行」等工具色 |
| `Button` | `link` | 类链接文案，默认冷色 |

更多历史迭代思路见交接日志与工作区 **`docs/superpowers/plans`** 中与 Web 相关的条目。
