# -*- coding: utf-8 -*-
"""Restore corrupted Chinese strings in web/src/App.tsx."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "web" / "src" / "App.tsx"
t = p.read_text(encoding="utf-8", errors="replace")

REPLACEMENTS: list[tuple[str, str]] = [
    ('return "?????"', 'return "未命名项目"'),
    ('useState("????")', 'useState("电影短片")'),
    ('useState("??????????")', 'useState("电影短片")'),
    (': "????????"', ': "（加载日志失败）"'),
    ("text: `???????\\n${msg}`", "text: `加载产物失败：\\n${msg}`"),
    (
        '"?? /api/health ??? step_log???????????**??????**???python -m uvicorn server.main:app --host 127.0.0.1 --port 8765"',
        '"后端 /api/health 未列出 step_log（多半是旧进程）。请在**本仓库根目录**重启：python -m uvicorn server.main:app --host 127.0.0.1 --port 8765"',
    ),
    (
        "setApiWarn(`???? API?${API_BASE}?????????`)",
        "setApiWarn(`无法连接 API（${API_BASE}）。请先启动后端。`)",
    ),
    ('setErr("???????????7 ??????")', 'setErr("请选择有效的风格类型（7 种预设之一）")'),
    (
        "if (!window.confirm(`????${topic}???????\\n??????????????? outputs/_trash??`))",
        "if (!window.confirm(`确定将「${topic}」移入回收站？\\n列表与历史中将不再显示（文件在 outputs/_trash）。`))",
    ),
    ('{errCopied ? "???" : "??"}', '{errCopied ? "已复制" : "复制"}'),
    ('{errCopied ? "?????" : "????"}', '{errCopied ? "已复制" : "复制"}'),
    (">\n                    ??\n                  </Button>", ">\n                    返回\n                  </Button>"),
    (">\n                  ??\n                </Button>", ">\n                  刷新\n                </Button>"),
    (">\n                    ????????\n                  </button>", ">\n                    本次会话关闭提示\n                  </button>"),
    (
        '<p className="text-sm font-medium text-foreground">??????????</p>',
        '<p className="text-sm font-medium text-foreground">全流程执行（自动化）</p>',
    ),
    (
        "??????????<strong>??</strong>??????? 1 ??? 8????????????????????????????????",
        "点一次按钮后，系统会<strong>排队</strong>按顺序做完步骤 1 到步骤 8。已经显示为「完成」的步骤会自动跳过，从下一项待做的继续往下跑。",
    ),
    (
        'title="????????????????????"',
        'title="当前步骤尽量收尾后停止，不再执行后续步骤"',
    ),
    (">\n                          ????\n                        </Button>", ">\n                          停止执行\n                        </Button>"),
    (
        'title="?????????????????"',
        'title="从当前未完成步骤一路执行到成片拼接"',
    ),
    (">\n                        ????????\n                      </Button>", ">\n                        一键执行全部步骤\n                      </Button>"),
    (">\n                      ???\n                    </Button>", ">\n                      上一步\n                    </Button>"),
    ('<span className="text-muted-foreground">??</span>', '<span className="text-muted-foreground">步骤</span>'),
    (">\n                      ???\n                      <ChevronRight", ">\n                      下一步\n                      <ChevronRight"),
]

for old, new in REPLACEMENTS:
    if old in t:
        t = t.replace(old, new)
    elif "?" in old:
        pass  # already fixed or pattern changed

# Fix latin-1 middle dot if present
b = t.encode("utf-8")
if b"\xb7 {" in b and b"\xc2\xb7 {" not in b:
    b = b.replace(b" \xb7 {", b" \xc2\xb7 {")
    t = b.decode("utf-8")

p.write_text(t, encoding="utf-8")

# verify
remaining = [line for line in t.splitlines() if "?" in line and "??" in line and "?" * 3 in line]
print("written", p)
print("suspicious lines", len([l for l in t.splitlines() if '???' in l or '????' in l]))
for line in t.splitlines():
    if "????" in line and "??" in line.replace("??", "", 1):
        print("still:", line.strip()[:80])
