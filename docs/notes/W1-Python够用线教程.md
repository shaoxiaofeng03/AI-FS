# W1 · Python 够用线教程（Java 开发者版）

> **给谁看**：3 年+ Java 后端，Python 从零或半吊子，目标不是「精通 Python」，是**能写评测脚本、能调 SDK、能读开源项目、能写 RAG/Agent 服务**。
> **怎么用**：不要通读。按 §0 的路线走，**看 20 分钟，写 100 分钟**。
> **2026-11 适配版**：原笔记来自旧版计划；已把环境升级为 **Python 3.12 + uv**，旧路径与示例项目名改为通用写法。配套 [`10-分阶段知识清单与学习资源`](../10-分阶段知识清单与学习资源.md) P0 与 [`02-每周执行手册`](../02-每周执行手册.md) W1–W2。
> **环境**：Python 3.12（用 uv 管理），本文代码在 3.12 可跑；3.11+ 的特性会标注。

---

## 0. 怎么用这份文档（重要）

### 你的定位

| 你以为要学的 | 你实际需要的 |
|---|---|
| Python 全语法、装饰器、元类、GIL 原理 | 数据结构、函数、类、typing、异常 |
| 面向对象设计模式 | 能读懂别人的代码 |
| 「Pythonic」写法大全 | 能写出**正确、可维护**的代码 |

**你的优势**：编程思维、工程规范、并发模型你都有。Python 只是换语法。
**你的风险**：用 Java 的思维写 Python（到处写 class、到处 `for i in range(len(x))`），写出来能跑但很别扭，且会踩坑。

### 三轮走法

```
第 1 轮（2h）  §1 环境 + §2 速查表 + §3 容器 + §4 函数   → 动手敲一遍
第 2 轮（2h）  §5 类 + §6 typing + §7 异常 + §8 JSON    → 改造你的 step 文件
第 3 轮（2h）  §9 pydantic + §10 async + §11 httpx      → 写一个并发调用脚本
```

**每一步都必须自己敲，不许复制粘贴。** Python 的坑全在细节里（缩进、可变默认参数、`is` vs `==`），复制粘贴学不到。

---

## 1. 环境与依赖管理

### 1.1 三个概念对应关系

| Java | Python | 说明 |
|---|---|---|
| JDK | Python 解释器 | 系统装一个 |
| `pom.xml` | `requirements.txt` / `pyproject.toml` | 依赖清单 |
| Maven 本地仓库 | 全局 site-packages | 默认所有项目共享 |
| **Maven 的隔离？** | **venv** | 每个项目一个虚拟环境 |
| `mvn install` | `pip install -r requirements.txt` | 装依赖 |

> **为什么一定要 venv**：Python 默认所有项目共用一个全局包目录。项目 A 要 `openai==1.0`，项目 B 要 `openai==2.0`，不隔离就打架。**venv 相当于给每个项目一个独立 classpath。**

### 1.2 用 venv（备选；先理解隔离）

```bash
cd ~/Documents/context/AI全栈/projects/hello-ai

# 创建虚拟环境（会在当前目录生成 .venv/）
python3 -m venv .venv

# 激活（每次开新终端都要执行一次）
source .venv/bin/activate

# 激活后命令行前面出现 (.venv)，说明生效
# 装包
pip install openai httpx pydantic python-dotenv

# 导出版本清单（相当于锁定依赖）
pip freeze > requirements.txt

# 退出
deactivate
```

> 新项目建议直接用 §1.3 的 `uv`；venv 只用于理解隔离或兼容旧项目。

### 1.3 用 uv（推荐，直接用这个）

`uv` 是 Rust 写的包管理器，现在 Python 圈的事实标准。**W1 直接用它**：

```bash
# 安装（会装到 ~/.local/bin，可能需要重开终端或 source ~/.bashrc）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证
uv --version
```

**uv 的用法**（比 pip 顺手）：

```bash
uv venv                      # 创建 .venv
source .venv/bin/activate

uv pip install openai        # 装包（兼容 pip 语法，但快得多）
uv add openai                # 或用 pyproject.toml 管理（类似 maven）
uv sync                      # 按 pyproject.toml 还原环境
uv run script.py             # 不激活也能跑，自动用项目环境
```

> **建议**：直接用 `uv`（本项目 W1 就用它）；venv 只用于理解隔离或兼容旧项目。

### 1.4 项目结构约定

```
hello-ai/
├── .venv/                 # 虚拟环境（进 .gitignore）
├── .env                   # 密钥（进 .gitignore，绝对不提交）
├── pyproject.toml         # uv 管理依赖（或 requirements.txt）
├── src/
│   ├── __init__.py
│   ├── config.py          # 读环境变量
│   └── llm_utils.py       # 可复用工具
└── hello.py
```

**`.env` 内容**：

```bash
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

**`.gitignore` 里必须有**：

```text
.venv/
.env
__pycache__/
*.pyc
```

> **为什么强调**：把 API Key 提交到 Git 是最常见的生产事故，Key 会被爬虫扫到，一晚上能烧掉几千块。**这是面试也会问的安全常识。**

---

## 2. Java ↔ Python 速查表（先扫一眼）

| Java | Python | 备注 |
|---|---|---|
| `System.out.println(x)` | `print(x)` | |
| `String s = "a" + b` | `s = f"a{b}"` | **f-string 是主力** |
| `List<String> = new ArrayList<>()` | `xs = []` | 不用声明类型 |
| `Map<String,Integer>` | `d = {}` | dict 就是 HashMap |
| `Set<String>` | `s = set()` | 注意 `{}` 是空 dict 不是空 set |
| `null` | `None` | 且 `None` 是单例，用 `is None` 判断 |
| `for (String x : xs)` | `for x in xs:` | |
| `for (int i=0; i<n; i++)` | `for i in range(n):` | 但通常用 `enumerate(xs)` |
| `xs.stream().map(f).toList()` | `[f(x) for x in xs]` | 推导式 |
| `xs.stream().filter(p).toList()` | `[x for x in xs if p(x)]` | |
| `xs.size()` | `len(xs)` | 内置函数，不是方法 |
| `map.get(k)` | `d.get(k)` | 都返回 None/null |
| `map.getOrDefault(k, 0)` | `d.get(k, 0)` | |
| `String.format("%.2f", x)` | `f"{x:.2f}"` | |
| `x.equals(y)` | `x == y` | **Python 的 `==` 就是值比较** |
| `x == y`（引用比较） | `x is y` | `is` 是比较对象身份 |
| `try/catch/finally` | `try/except/finally` | |
| `throw new RuntimeException(msg)` | `raise RuntimeError(msg)` | |
| `interface` | `Protocol` / 抽象基类 | 鸭子类型为主 |
| `record` | `@dataclass` | 最接近的对应 |
| `Optional<T>` | `T \| None` | Python 3.10+ |
| `CompletableFuture` | `asyncio.Task` | |
| `CompletableFuture.allOf` | `asyncio.gather` | |
| `ExecutorService` | `asyncio.Semaphore` 限流 | 模型不同，见 §10 |
| `Thread.sleep(1000)` | `await asyncio.sleep(1)` | |
| `synchronized` | `asyncio.Lock` | 单线程事件循环，锁的需求少 |
| `@Valid` + Bean Validation | **pydantic** | 见 §9 |
| `ObjectMapper` | `json` 模块 | |
| `Path` | `pathlib.Path` | |
| `@Value("${x}")` | `os.environ["X"]` / pydantic-settings | |

---

## 3. 语法：数据类型与容器

> 这一节假设你完全没写过 Python。有基础就跳到 §4。

### 3.1 变量、类型、真值

```python
# 不用声明类型，赋值即创建
name = "sky"
age = 30
price = 19.9
is_active = True
nothing = None

# 一次赋多个
a, b = 1, 2
a, b = b, a          # 交换，不需要临时变量

# 类型查询
print(type(age))          # <class 'int'>
print(isinstance(age, int))   # True  ← 相当于 Java 的 instanceof
```

**真值判断（Java 人最容易写错的地方）**：

```python
# 以下全部为 False（falsy）
bool(None)      # False
bool(0)         # False
bool("")        # False      ← 空字符串
bool([])        # False      ← 空列表
bool({})        # False      ← 空字典
bool(set())     # False

# 所以 Python 里判断空集合，不要写 len(x) > 0
if items:                 # ✅ Pythonic
    ...
if len(items) > 0:        # ❌ 能跑但很 Java
    ...
```

> ⚠️ **坑**：`if x:` 在 `x` 可能是 `0` 或 `""` 时会误判。**如果 0 是合法值，必须写 `if x is not None:`**。

### 3.2 字符串

```python
s = "hello"
t = 'world'              # 单双引号等价

# f-string（最常用）
name, score = "sky", 95.678
print(f"{name} 得分 {score:.1f}")          # sky 得分 95.7
print(f"{score:>10.2f}")                   # 右对齐宽度 10
print(f"{name=}")                          # name='sky'  调试神器

# 多行字符串
prompt = """
你是企业工单助手。
只依据资料回答。
"""

# 常用方法
s.upper()                  # 'HELLO'
s.strip()                  # 去首尾空白
s.split(",")               # 切分 → list
",".join(["a", "b"])       # 拼接 → 'a,b'
s.replace("l", "L")
s.startswith("he")
"ell" in s                 # True  ← 用 in 判断包含，不是 contains()
s * 3                      # 重复
```

**拼接性能**：Java 有 `StringBuilder`，Python 直接用 `"".join(list)`，**绝不要在循环里 `s += x`**（和 Java 的 `String +=` 一样是 O(n²)）。

```python
# ✅
parts = [f"第{i}条" for i in range(1000)]
text = "\n".join(parts)

# ❌
text = ""
for i in range(1000):
    text += f"第{i}条\n"
```

### 3.3 list（≈ ArrayList）

```python
nums = [3, 1, 2]
nums.append(4)             # 尾部加     → [3,1,2,4]
nums.insert(0, 9)          # 指定位置插 → [9,3,1,2,4]
nums.pop()                 # 弹尾部
nums.pop(0)                # 弹指定位置
nums.remove(1)             # 按值删（只删第一个）
nums.index(2)              # 找索引
nums.count(1)
nums.sort()                # 原地排序
nums.sort(reverse=True)
nums.sort(key=lambda x: -x)

# 切片（Java 没有，非常好用）
xs = [0, 1, 2, 3, 4, 5]
xs[0:2]      # [0, 1]
xs[2:]       # [2, 3, 4, 5]
xs[:2]       # [0, 1]
xs[-1]       # 5       ← 倒数第一个
xs[-3:]      # [3, 4, 5]
xs[::-1]     # 反转

# 合并
a + b        # 新列表
a.extend(b)  # 原地追加

# 解包
first, *rest = [1, 2, 3]      # first=1, rest=[2,3]
```

**排序稳定性与多字段排序**（对应 Java 的 Comparator）：

```python
users = [{"name": "b", "age": 30}, {"name": "a", "age": 30}]
users.sort(key=lambda u: (u["age"], u["name"]))   # 先年龄后姓名
```

### 3.4 dict（≈ HashMap）——**用得最多的容器**

```python
user = {"name": "sky", "age": 30}

user["name"]              # 取值，key 不存在会 KeyError
user.get("email")         # 返回 None，不报错   ← 优先用这个
user.get("email", "无")   # 给默认值
user["email"] = "a@b.com" # 新增/覆盖
"name" in user            # 判断 key 存在
del user["age"]
user.pop("age", None)     # 安全删除

# 遍历
for k in user:                       # 只 key
for k, v in user.items():            # key + value   ← 最常用
for v in user.values():

# 合并（3.9+）
merged = {**a, **b}
merged = a | b                       # 3.9+

# 字典推导式
squares = {x: x * x for x in range(5)}
```

**翻转为值为 key、按值分组**：

```python
from collections import defaultdict, Counter

# 分组
groups = defaultdict(list)
for item in items:
    groups[item.type].append(item)      # key 不存在自动创建 []

# 计数
Counter(["a", "b", "a"])                # {'a': 2, 'b': 1}
```

> **Java 对照**：`defaultdict(list)` ≈ `map.computeIfAbsent(k, k -> new ArrayList<>()).add(x)`。

### 3.5 set（≈ HashSet）

```python
s = {1, 2, 3}          # 注意：空集合必须写 set()，{} 是空 dict
s.add(4)
s.discard(1)           # 删除，不存在也不报错
s.remove(1)            # 不存在会 KeyError
1 in s                 # O(1)
a | b                  # 并集
a & b                  # 交集
a - b                  # 差集
```

**去重 + 保序**：

```python
unique = list(dict.fromkeys(items))    # 保序去重  ← 记住这个
unique = list(set(items))              # 不保序
```

### 3.6 tuple（不可变，≈ 只读 record）

```python
point = (1, 2)
x, y = point
```

**用途**：dict 的 key、函数返回多个值、不可变常量。

```python
def parse(s):
    a, b = s.split("-")
    return int(a), int(b)      # 实际上返回一个 tuple

x, y = parse("1-2")
```

### 3.7 推导式（Python 最标志性的写法）

```python
# 列表推导式
squares = [x * x for x in range(5)]                 # [0,1,4,9,16]
evens = [x for x in nums if x % 2 == 0]
names = [u["name"].upper() for u in users]

# 条件表达式（三元）
label = "高" if score >= 90 else "低"

# 推导式里带 if-else（注意位置不同）
vals = [x if x > 0 else 0 for x in nums]            # 这是「变换」
vals = [x for x in nums if x > 0]                   # 这是「过滤」

# 嵌套
flat = [x for row in matrix for x in row]

# 字典 / 集合推导式
d = {u["id"]: u for u in users}
st = {u["name"] for u in users}

# 生成器表达式（不立即占内存，用于大文件/大列表）
total = sum(x * x for x in range(10_000_000))
```

> **Java 对照**：`xs.stream().filter(p).map(f).collect(toList())` ≈ `[f(x) for x in xs if p(x)]`。
> **但**：推导式只适合简单逻辑，超过一层嵌套就老老实实写 for 循环，**可读性优先**。

### 3.8 可变 vs 不可变（重要的坑）

```python
# 不可变：int / float / str / tuple / frozenset
a = "abc"
b = a.upper()          # 返回新字符串，a 不变

# 可变：list / dict / set
a = [1, 2]
b = a                  # ← 这不是拷贝！b 和 a 指向同一个对象
b.append(3)
print(a)               # [1, 2, 3]  ← a 也变了

# 浅拷贝
b = a.copy()           # 或 a[:] 或 list(a)
b = dict(d)            # dict 浅拷贝

# 深拷贝（嵌套结构必须用）
import copy
b = copy.deepcopy(a)
```

> ⚠️ **这是 Python 最经典的 bug 来源之一**。Java 里 `b = a` 也是引用，但 Java 程序员常常在 Python 里忘了这一点，因为 Python 没有类型声明提醒你。

---

## 4. 语法：函数

### 4.1 基本形态

```python
def greet(name: str, greeting: str = "你好") -> str:
    """返回问候语。（这是 docstring，写在函数体第一行）"""
    return f"{greeting}，{name}"

greet("sky")                       # 位置参数
greet(name="sky", greeting="hi")   # 关键字参数  ← Java 没有，很好用
greet(greeting="hi", name="sky")   # 顺序随意
```

### 4.2 默认参数的**致命坑**

```python
# ❌ 错误：默认值在函数定义时只创建一次，所有调用共享同一个 list
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket

add_item(1)     # [1]
add_item(2)     # [1, 2]  ← 你以为会是 [2]

# ✅ 正确：默认值用 None，函数内部创建
def add_item(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

> **面试常问**。原因：Python 的默认参数在 `def` 执行时求值一次，之后复用。

### 4.3 `*args` / `**kwargs`

```python
def log(level, *args, **kwargs):
    print(level, args, kwargs)

log("INFO", "a", "b", user="sky")
# INFO ('a', 'b') {'user': 'sky'}
```

| 写法 | 含义 | Java 对照 |
|---|---|---|
| `*args` | 任意个位置参数 → tuple | `Object... args` |
| `**kwargs` | 任意个关键字参数 → dict | 无直接对应 |

**调用时反向使用（把容器展开成参数）**：

```python
def f(a, b, c):
    return a + b + c

nums = [1, 2, 3]
f(*nums)              # 等价 f(1, 2, 3)

d = {"a": 1, "b": 2, "c": 3}
f(**d)                # 等价 f(a=1, b=2, c=3)
```

> 这个机制在 LLM 代码里到处都是：`client.create(**params)`、`asyncio.gather(*tasks)`。

### 4.4 函数是一等公民

```python
def apply(fn, value):
    return fn(value)

apply(str.upper, "abc")            # 'ABC'
apply(lambda x: x * 2, 3)          # 6

# 常用高阶函数
nums = [3, 1, 2]
sorted(nums, key=lambda x: -x)     # [3, 2, 1]
list(map(str, nums))               # ['3','1','2']
list(filter(lambda x: x > 1, nums))
any(x > 2 for x in nums)           # True
all(x > 0 for x in nums)           # True
sum(nums), max(nums), min(nums)
```

> **Java 对照**：`Function<T,R>` / `Predicate<T>` / `Comparator<T>` 都能用 lambda 表达，几乎一一对应。

### 4.5 装饰器（看懂即可，不用会写）

```python
import functools, time

def timing(fn):
    @functools.wraps(fn)                      # 保留原函数名，必须有
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        print(f"{fn.__name__} 耗时 {time.perf_counter()-start:.3f}s")
        return result
    return wrapper

@timing
def slow():
    time.sleep(0.1)

slow()      # 输出：slow 耗时 0.101s
```

> **Java 对照**：≈ Spring 的 AOP `@Around`。Python 装饰器是**函数包装函数**，没有代理、没有容器。
> **在 LLM 代码里你会见到**：`@tool`（LangChain 的工具声明）、`@retry`（重试）、`@field_validator`（pydantic 校验）。

### 4.6 作用域与闭包（坑）

```python
# ❌ 经典闭包坑：lambda 在调用时才读 i
funcs = []
for i in range(3):
    funcs.append(lambda: i)
print([f() for f in funcs])     # [2, 2, 2]  ← 不是 [0,1,2]

# ✅ 用默认参数把当前值「绑死」
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])     # [0, 1, 2]

# ✅ 或用 functools.partial
```

> **Java 对照**：Java 的 lambda 捕获的是 effectively-final 变量，所以没这个问题。Python 捕获的是**变量本身**，不是值。

**修改外层变量要 `nonlocal`**：

```python
def counter():
    n = 0
    def inc():
        nonlocal n       # 不加这句会报 UnboundLocalError
        n += 1
        return n
    return inc
```

---

## 5. 语法：类与 dataclass

### 5.1 普通类

```python
class Order:
    # 类属性（所有实例共享）
    currency = "CNY"

    def __init__(self, order_id: str, amount: float):
        # 实例属性
        self.order_id = order_id
        self.amount = amount

    def total(self, tax_rate: float = 0.0) -> float:
        return self.amount * (1 + tax_rate)

    def __str__(self) -> str:              # ≈ toString()
        return f"Order({self.order_id}, {self.amount})"

    def __repr__(self) -> str:             # 调试显示
        return f"Order(order_id={self.order_id!r}, amount={self.amount!r})"

    def __eq__(self, other) -> bool:       # ≈ equals()
        return isinstance(other, Order) and self.order_id == other.order_id


o = Order("ORD-001", 99.5)
print(o.total(0.1))        # 109.45
print(o)                   # Order(ORD-001, 99.5)
```

**必知差异**：

| Java | Python |
|---|---|
| `this` | `self`（**必须显式写在参数里**，名字可换但不建议） |
| 构造器 `new` | `__init__`，调用不带 `new` |
| `private` 字段 | 约定 `_name`（单下划线=内部用），`__name` 会名字改写 |
| `@Override` | 不检查签名，靠类型标注和测试 |
| `final` | 无，靠约定 |
| `getter/setter` | **不要写**，直接访问属性 |
| `interface` | `Protocol` / 抽象基类，或干脆鸭子类型 |

> **给 Java 人的忠告**：**不要给每个字段写 getter/setter**。Python 的惯用法是直接访问 `o.amount`，需要校验/计算时再用 `@property`。

### 5.2 `@dataclass`（≈ Java record）——**写数据类首选**

```python
from dataclasses import dataclass, field

@dataclass
class Message:
    role: str
    content: str
    tokens: int = 0
    tags: list[str] = field(default_factory=list)   # 可变默认值必须这样写

msgs = [
    Message("system", "你是助手"),
    Message("user", "你好"),
]
print(msgs[0].role)        # system
print(msgs[0])             # Message(role='system', content='你是助手', tokens=0, tags=[])
```

**dataclass 自动生成**：`__init__` / `__repr__` / `__eq__`。

```python
@dataclass(frozen=True)        # 不可变（≈ record）
class Point:
    x: int
    y: int

@dataclass(slots=True)         # 3.10+，省内存、防手误写错属性名
class User:
    id: int
    name: str
```

> ⚠️ **`field(default_factory=list)` 是必须记住的写法**，原因和 §4.2 的可变默认参数坑完全一样。

### 5.3 继承（用得少，但要看懂）

```python
class BaseTool:
    name: str = "base"

    def run(self, **kwargs):
        raise NotImplementedError

class WeatherTool(BaseTool):
    name = "weather"

    def run(self, city: str) -> str:
        return f"{city} 晴"

t = WeatherTool()
print(t.run(city="北京"))
print(isinstance(t, BaseTool))     # True
```

### 5.4 `@property`（需要计算或校验时才用）

```python
class Invoice:
    def __init__(self, amount: float):
        self._amount = amount

    @property
    def amount(self) -> float:          # 像字段一样访问：invoice.amount
        return self._amount

    @amount.setter
    def amount(self, value: float):     # 赋值时触发校验
        if value < 0:
            raise ValueError("金额不能为负")
        self._amount = value
```

### 5.5 模块与导入

```python
import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from mypackage.utils import helper
```

| 概念 | Python |
|---|---|
| 一个 `.java` 文件 = 一个 public 类 | 一个 `.py` 文件 = 一个模块 |
| `package` | 目录 + `__init__.py` |
| `import static` | `from x import y` |
| `public/private` | 下划线约定 |

**`if __name__ == "__main__":`**（≈ Java 的 `public static void main`）：

```python
def main():
    print("被直接运行时才执行")

if __name__ == "__main__":
    main()
```

> 作用：这个文件被 `import` 时不执行 `main()`，只有 `python file.py` 直接运行时才执行。

---

## 6. typing：类型注解（以及它的局限）

### 6.1 基本用法

```python
from typing import Any, Optional, Union, Callable, Literal, TypeVar

def process(items: list[str], limit: int = 10) -> dict[str, Any]:
    ...
```

| Java | Python 3.10+ |
|---|---|
| `List<String>` | `list[str]` |
| `Map<String, Object>` | `dict[str, Any]` |
| `Optional<T>` | `T \| None` 或 `Optional[T]` |
| `T`（泛型） | `TypeVar("T")` |
| `Function<T,R>` | `Callable[[T], R]` |
| 枚举值约束 | `Literal["a", "b"]` |
| `Object` | `object` / `Any` |

### 6.2 **关键认知：类型注解运行时完全不生效**

```python
def add(a: int, b: int) -> int:
    return a + b

add("1", "2")      # 返回 "12"，不报错！
```

Python 的类型注解**只是给 IDE 和静态检查器（mypy / pyright）看的**，解释器不做任何检查。

> **这一点直接引出 pydantic 的存在意义**：
> **typing 负责「写代码时的提示」，pydantic 负责「运行时真的校验」。**
> 你的 LLM 结构化输出，必须用 pydantic，不能用 typing。

### 6.3 什么时候写类型注解

**写**：
- 所有函数签名（参数 + 返回值）
- 数据类字段
- 复杂数据结构

**不写**：
- 局部变量（能从上下文看出来）
- 一眼可见的简单场景

> 你是 Java 出身，**保持写类型注解的习惯**，这对后面用 pydantic 和理解开源代码极有帮助。

---

## 7. 异常处理

### 7.1 基本语法

```python
try:
    result = risky()
except ValueError as e:
    print(f"参数错误: {e}")
except (TimeoutError, ConnectionError) as e:
    print(f"网络问题: {e}")
except Exception as e:
    print(f"未知错误: {e}")
    raise                      # 重新抛出（类似 throw e）
else:
    print("没异常才执行")       # Java 没有，很少用
finally:
    print("一定执行")           # ≈ finally
```

### 7.2 自定义异常

```python
class LLMError(Exception):
    """所有 LLM 相关异常的基类"""

class RateLimitError(LLMError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"限流，{retry_after}s 后重试")

class OutputTruncated(LLMError):
    pass
```

> **Java 对照**：Python 没有 checked exception，所有异常都是 unchecked。**所以你必须靠文档和约定**，这反而要求你在代码里显式处理。

### 7.3 异常链（保留根因）

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    raise OutputTruncated("模型输出的 JSON 不合法") from e    # ← from e 保留原始堆栈
```

> **`raise ... from e` ≈ Java 的 `new XxxException(msg, e)`**。不写 `from` 会丢失根因，调试时很痛苦。

### 7.4 三大禁忌

```python
# ❌ 裸 except（会吞掉 KeyboardInterrupt / SystemExit）
try:
    ...
except:
    pass

# ❌ 只打日志不处理（等于吞异常）
try:
    ...
except Exception as e:
    print(e)

# ❌ 用异常做流程控制
try:
    v = d["key"]
except KeyError:
    v = None
# ✅ 应该写成
v = d.get("key")
```

### 7.5 上下文管理器（≈ try-with-resources）

```python
with open("data.txt") as f:        # 退出自动 close
    content = f.read()

# 多个
with open("a.txt") as fa, open("b.txt") as fb:
    ...

# 自己写一个
from contextlib import contextmanager

@contextmanager
def timer(name):
    import time
    start = time.perf_counter()
    yield                          # ← 分界点
    print(f"{name}: {time.perf_counter()-start:.3f}s")

with timer("请求"):
    do_something()
```

> **Java 对照**：`with` ≈ try-with-resources。httpx 的 `client.stream(...)` 就是靠这个自动关闭连接。

---

## 8. JSON 与文件

### 8.1 JSON（用得极多）

```python
import json

# 字符串 → 对象
data = json.loads('{"a": 1}')
# 对象 → 字符串
s = json.dumps({"a": 1})

# 文件
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)
with open("out.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**三个必设参数**：

```python
json.dumps(
    obj,
    ensure_ascii=False,      # 中文不转 \uXXXX    ← 必设
    indent=2,                # 格式化（调试用）
    default=str,             # 遇到 datetime 等不可序列化对象时的兜底
)
```

**只读 JSON 文件的安全写法**：

```python
def load_json(path: str | Path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
```

### 8.2 文件与路径（用 pathlib，别用 os.path）

```python
from pathlib import Path

p = Path(".")
(p / "notes" / "a.md").exists()
p.glob("*.py")                        # 当前目录 py 文件
list(p.rglob("*.md"))                 # 递归
p.mkdir(parents=True, exist_ok=True)  # 建目录，已存在不报错

text = Path("a.txt").read_text(encoding="utf-8")
Path("b.txt").write_text("内容", encoding="utf-8")

# 按行读大文件（不占内存）
for line in open("big.log", encoding="utf-8"):
    ...
```

> **Java 对照**：`Path` ↔ `java.nio.file.Path`，`glob` ↔ `Files.walk`。

### 8.3 环境变量与 `.env`

```python
import os
key = os.environ.get("DEEPSEEK_API_KEY")     # 不存在返回 None
key = os.environ["DEEPSEEK_API_KEY"]         # 不存在抛 KeyError

# ❌ 不要这么写（会把 key 提交到 git）
key = "sk-xxxx"

# ✅ 从 .env 加载（开发环境）
from dotenv import load_dotenv
load_dotenv()                                # 读项目根目录的 .env
key = os.environ["DEEPSEEK_API_KEY"]
```

**更好的方式：pydantic-settings**（见 §9.5）。

---

## 9. pydantic：运行时校验（重点）

> **这一节是「Python 够用线」里最重要的。** 你的结构化输出、配置管理、Agent 状态全部靠它。

### 9.1 为什么需要它

```python
# typing 不校验
def f(x: int) -> int:
    return x
f("abc")            # 不报错

# pydantic 会校验
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

User(id="abc", name="sky")     # ❌ ValidationError
User(id="123", name="sky")     # ✅ 自动转成 id=123（pydantic v2 默认宽松转换）
```

### 9.2 基本模型

```python
from pydantic import BaseModel, Field
from typing import Literal

class Ticket(BaseModel):
    category: Literal["refund", "logistics", "other"]
    priority: int = Field(ge=1, le=5, description="1 最低，5 最高")
    summary: str = Field(min_length=1, max_length=200)
    order_id: str | None = None

t = Ticket(category="refund", priority=3, summary="要退货")
print(t.priority)              # 3
print(t.model_dump())          # {'category': 'refund', ...}   ← 转 dict
print(t.model_dump_json())     # 转 JSON 字符串
```

**常用 Field 约束**：

| 约束 | 含义 |
|---|---|
| `ge` / `le` | 大于等于 / 小于等于 |
| `gt` / `lt` | 大于 / 小于 |
| `min_length` / `max_length` | 字符串长度 |
| `pattern` | 正则 |
| `description` | **写给人看，也会进 JSON Schema，LLM 能用上** |

> ⚠️ pydantic **v2** 的 API 是 `model_dump()` / `model_validate()`；v1 是 `dict()` / `parse_obj()`。网上教程很多是 v1，**认准 v2**。

### 9.3 从 JSON 字符串解析（LLM 场景的核心）

```python
from pydantic import ValidationError

raw = '{"category":"refund","priority":3,"summary":"要退货"}'

try:
    t = Ticket.model_validate_json(raw)      # ← 直接解析 + 校验
except ValidationError as e:
    print(e.errors())                        # 结构化错误列表
```

### 9.4 自定义校验器

```python
from pydantic import field_validator

class Order(BaseModel):
    order_id: str
    amount: float

    @field_validator("order_id")
    @classmethod
    def check_prefix(cls, v: str) -> str:
        if not v.startswith("ORD-"):
            raise ValueError("order_id 必须以 ORD- 开头")
        return v

    @field_validator("amount")
    @classmethod
    def check_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("金额不能为负")
        return v
```

### 9.5 配置管理（pydantic-settings）

```bash
pip install pydantic-settings
```

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout_seconds: int = 60

    model_config = {"env_file": ".env", "env_prefix": ""}

settings = Settings()        # 自动读 .env / 环境变量
print(settings.model)
```

> **Java 对照**：≈ `@ConfigurationProperties`。**这是 Python 项目读配置的标准做法**，比 `os.environ` 散落各处好得多。

### 9.6 结构化输出 + 校验 + 重试（完整实战）

```python
import json
from pydantic import BaseModel, ValidationError
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

class Ticket(BaseModel):
    category: str
    priority: int
    summary: str

def extract(text: str, max_retries: int = 2) -> Ticket:
    schema = json.dumps(Ticket.model_json_schema(), ensure_ascii=False)
    messages = [
        {"role": "system", "content": f"把用户输入抽取成 JSON，严格符合 schema：{schema}"},
        {"role": "user", "content": text},
    ]

    last_err = None
    for attempt in range(max_retries + 1):
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=500,
        )

        # 1. 先看是不是被截断
        if resp.choices[0].finish_reason == "length":
            last_err = "输出被截断"
            continue

        raw = resp.choices[0].message.content or ""

        # 2. 解析 + 校验
        try:
            return Ticket.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError) as e:
            last_err = str(e)
            # 3. 把错误回灌给模型（这是关键技巧）
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"上面的输出不合法：{e}。请只输出修正后的 JSON，不要解释。",
            })

    raise RuntimeError(f"抽取失败，重试 {max_retries} 次仍不合法：{last_err}")
```

**这三步（校验 → 截断检查 → 错误回灌）就是 W3 的核心内容，你现在可以先跑起来建立感觉。**

---

## 10. async/await：并发调模型

### 10.1 先理解本质

| Java | Python asyncio |
|---|---|
| 多线程 / 线程池 | **单线程事件循环** |
| 阻塞时线程被占住 | 遇到 IO 让出控制权，切去干别的 |
| `CompletableFuture<T>` | `Task` |
| `future.get()` | `await task` |
| `CompletableFuture.allOf(...)` | `asyncio.gather(...)` |
| `ExecutorService(10)` | `asyncio.Semaphore(10)` |
| 适合 CPU 密集 → 多线程/多进程 | 适合 **IO 密集**（调 API 就是） |

> **为什么 LLM 场景必须用 async**：调一次模型要 1~30 秒，**99% 时间在等网络**。用同步串行调 10 个请求要 100 秒，用 async 并发只要 10 秒——**而且不占线程**。

> ⚠️ **GIL 说明**：Python 有全局解释器锁，多线程对 CPU 密集任务无效。但 **IO 密集（网络请求）用 asyncio 完全没问题**，因为等待时会释放 GIL。

### 10.2 基本语法

```python
import asyncio

async def fetch(name: str) -> str:
    print(f"开始 {name}")
    await asyncio.sleep(1)          # 模拟 IO 等待
    print(f"结束 {name}")
    return f"{name}-result"

async def main():
    result = await fetch("A")       # 单个等待
    print(result)

asyncio.run(main())                 # ← 入口，只调用一次
```

**三条铁律**：

1. `async def` 定义协程函数，**调用它不会执行**，返回协程对象，必须 `await` 或交给事件循环。
2. `await` 只能在 `async def` 里面用。
3. 程序入口用 `asyncio.run(main())`。

```python
# ❌ 常见错误
async def f():
    return 1
x = f()              # 这是协程对象，不是 1
print(x)             # <coroutine object ...>
```

### 10.3 并发：`asyncio.gather`

```python
async def main():
    results = await asyncio.gather(
        fetch("A"),
        fetch("B"),
        fetch("C"),
    )
    print(results)          # ['A-result', 'B-result', 'C-result']
```

**耗时**：串行 3 秒 → 并发 1 秒。

**`return_exceptions=True`**（一个失败不影响其他）：

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        print("失败:", r)
    else:
        print("成功:", r)
```

**动态任务列表**：

```python
tasks = [fetch(name) for name in ["A", "B", "C"]]
results = await asyncio.gather(*tasks)      # ← 注意 * 解包
```

### 10.4 限流：`Semaphore`（生产必备）

并发 100 个请求会触发 API 限流或把内存打爆。**必须限流**：

```python
import asyncio

async def main():
    sem = asyncio.Semaphore(5)          # 最多 5 个同时进行

    async def bounded(name):
        async with sem:                 # 拿到信号量才能进
            return await fetch(name)

    results = await asyncio.gather(*[bounded(f"q{i}") for i in range(100)])
```

> **Java 对照**：`Semaphore` 在 Java 里是 `java.util.concurrent.Semaphore`，概念完全一样。

### 10.5 超时控制（Python 3.12）

```python
# 推荐：asyncio.timeout（3.11+）
try:
    async with asyncio.timeout(5):
        result = await fetch("A")
except TimeoutError:
    print("超时")

# 兼容旧环境：wait_for
# result = await asyncio.wait_for(fetch("A"), timeout=5)
```

> **你的环境是 3.12，用 `asyncio.timeout`；3.10 及以下才用 `wait_for`。**

### 10.6 不要在 async 里调阻塞代码

```python
import time, httpx

async def bad():
    time.sleep(1)              # ❌ 阻塞整个事件循环，所有并发全卡住
    requests.get(url)          # ❌ 同上

async def good():
    await asyncio.sleep(1)     # ✅
    # 同步库必须丢到线程池
    result = await asyncio.to_thread(requests.get, url)   # ✅
```

**结论**：
- async 代码里 → 用 `httpx.AsyncClient` / `AsyncOpenAI`
- 必须用同步库 → `asyncio.to_thread()`
- **绝对不要 `time.sleep()`**

### 10.7 完整实战：并发调用 LLM（限流 + 超时 + 容错）

```python
import asyncio
import os

from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

async def ask(question: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        for attempt in range(3):
            try:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": question}],
                        temperature=0,
                        max_tokens=300,
                    ),
                    timeout=30,
                )
                return {"q": question, "a": resp.choices[0].message.content}
            except asyncio.TimeoutError:
                if attempt == 2:
                    return {"q": question, "error": "超时"}
                await asyncio.sleep(2 ** attempt)          # 指数退避
            except Exception as e:
                if attempt == 2:
                    return {"q": question, "error": str(e)}
                await asyncio.sleep(2 ** attempt)

async def batch(questions: list[str], concurrency: int = 5) -> list[dict]:
    sem = asyncio.Semaphore(concurrency)
    return await asyncio.gather(*[ask(q, sem) for q in questions])

if __name__ == "__main__":
    qs = ["什么是 token", "什么是 RAG", "什么是 Agent"]
    results = asyncio.run(batch(qs))
    for r in results:
        print(r)
```

**这个脚本包含了：限流、超时、重试、指数退避、错误隔离。** 这就是「生产级」和「demo 级」的区别，**也是你后面评测脚本的骨架**。

---

## 11. requests vs httpx（含流式）

### 11.1 对比

| | `requests` | `httpx` |
|---|---|---|
| 同步 | ✅ | ✅ |
| 异步 | ❌ | ✅ `AsyncClient` |
| HTTP/2 | ❌ | ✅ |
| 现状 | 事实标准，但停更中 | **新项目首选** |

**结论**：**新代码用 httpx**，需要异步时只能用 httpx。`requests` 看懂即可（老项目到处都是）。

### 11.2 同步请求

```python
import httpx

# 短脚本
r = httpx.get("https://api.example.com/items", params={"page": 1}, timeout=10)
print(r.status_code)
print(r.json())               # 自动 JSON 解析

# 推荐：复用 client（连接池，性能好）
with httpx.Client(timeout=10) as client:
    r = client.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": "deepseek-chat", "messages": [...]},
    )
    r.raise_for_status()      # ← 4xx/5xx 抛异常，别忘了
    data = r.json()
```

### 11.3 手写流式（理解 SSE 协议，**强烈建议做一次**）

```python
import httpx, json

with httpx.Client(timeout=60) as client:
    with client.stream(
        "POST",
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={... , "stream": True},
    ) as resp:
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[6:]                  # 去掉 "data: "
            if payload == "[DONE]":
                break
            chunk = json.loads(payload)
            delta = chunk["choices"][0]["delta"].get("content")
            if delta:
                print(delta, end="", flush=True)
```

> **为什么一定要手写一次**：等你用 SDK 的 `stream=True` 时，你就知道它在帮你做什么。**面试问「流式怎么实现」，你答得出 SSE 帧格式，而不是「调个参数」。**

### 11.4 异步请求

```python
import httpx, asyncio

async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:      # 复用 client
        tasks = [client.get(u) for u in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

### 11.5 异步流式

```python
async with httpx.AsyncClient(timeout=60) as client:
    async with client.stream("POST", url, json=payload, headers=headers) as resp:
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                ...
```

### 11.6 SDK 的异步流式（你实际会用的写法）

```python
from openai import AsyncOpenAI

async_client = AsyncOpenAI(api_key=..., base_url=...)

async def chat_stream(q: str):
    stream = await async_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": q}],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
```

---

## 12. 综合实战：把你的 hello-ai 重构成包

### 12.1 目标结构

```
hello-ai/
├── .env
├── pyproject.toml         # 或 requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py          # pydantic-settings 管配置
│   ├── client.py          # 同步/异步/流式封装
│   ├── schemas.py         # pydantic 模型
│   └── batch.py           # 并发批量调用
└── hello.py               # 保留，作为入口
```

### 12.2 `config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout: int = 60

    model_config = {"env_file": ".env"}

settings = Settings()
```

### 12.3 `client.py`

```python
from openai import OpenAI, AsyncOpenAI

from .config import settings

_sync = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
_async = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)

def chat(messages: list[dict], **kwargs) -> str:
    resp = _sync.chat.completions.create(
        model=settings.model, messages=messages, **kwargs
    )
    if resp.choices[0].finish_reason == "length":
        raise RuntimeError("输出被截断，请增大 max_tokens")
    return resp.choices[0].message.content or ""

def chat_stream(messages: list[dict], **kwargs):
    stream = _sync.chat.completions.create(
        model=settings.model, messages=messages, stream=True, **kwargs
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

async def chat_async(messages: list[dict], **kwargs) -> str:
    resp = await _async.chat.completions.create(
        model=settings.model, messages=messages, **kwargs
    )
    return resp.choices[0].message.content or ""
```

### 12.4 使用

```python
from src.client import chat, chat_stream

print(chat([{"role": "user", "content": "你好"}]))

for piece in chat_stream([{"role": "user", "content": "写首诗"}]):
    print(piece, end="", flush=True)
```

> **这就是 W1–W2 要的「可复用工具包」的雏形**。你现在做的每一步，后面都会复用。

---

## 13. 十二个新手坑（Java 人高发）

| # | 坑 | 症状 | 正确做法 |
|---|---|---|---|
| 1 | 可变默认参数 | 调用之间数据累积 | `def f(x=None)` + 内部创建 |
| 2 | `b = a` 以为是拷贝 | 改 b 影响了 a | `a.copy()` / `deepcopy` |
| 3 | `is` 和 `==` 混用 | 字符串比较偶发失败 | 值比较用 `==`，`None` 用 `is None` |
| 4 | `except:` 裸捕获 | 吞掉 Ctrl+C、隐藏 bug | `except Exception as e:` |
| 5 | `async def` 忘了 `await` | 拿到协程对象不执行 | 检查是否 `await` |
| 6 | async 里用 `time.sleep` | 所有并发卡死 | `await asyncio.sleep()` |
| 7 | 循环里 `s += x` | 大字符串性能崩 | `"".join(list)` |
| 8 | `for i in range(len(xs))` | 不像 Python | `for x in xs:` / `enumerate` |
| 9 | 给每个字段写 getter/setter | 代码臃肿 | 直接访问属性 |
| 10 | 用 typing 期待运行时校验 | 脏数据静默通过 | 用 **pydantic** |
| 11 | 缩进混用 tab/空格 | `IndentationError` | 统一 4 空格 |
| 12 | 把 API Key 写进代码 | 提交泄露、被盗刷 | `.env` + `.gitignore` |

**额外两个**：

- **`{}` 是空 dict 不是空 set** —— 空集合写 `set()`。
- **函数名/变量名遮蔽内置** —— 别用 `list` / `dict` / `str` / `id` / `type` 当变量名。

---

## 14. 自测 20 题

> 这一节是**简答题**；要动手写代码，做配套的 [W1-Python够用线-练习题.md](./W1-Python够用线-练习题.md)（30 题，含验收标准，答案在 [这里](./W1-Python够用线-练习题-答案.md)）。

**容器**
1. `[]`、`{}`、`set()` 分别是什么？
2. `a = [1,2]; b = a; b.append(3)`，`a` 是什么？
3. 如何保序去重一个 list？
4. `d.get("k")` 和 `d["k"]` 区别？
5. 切片 `xs[-3:]` 是什么意思？

**函数**
6. 为什么 `def f(x, lst=[])` 是危险的？
7. `*args` 和 `**kwargs` 分别是什么类型？
8. 下面输出什么？
   ```python
   funcs = [lambda: i for i in range(3)]
   print([f() for f in funcs])
   ```
9. `if __name__ == "__main__":` 有什么用？

**类与类型**
10. `@dataclass` 自动生成哪些方法？
11. 为什么可变字段必须写 `field(default_factory=list)`？
12. typing 的类型注解在运行时生效吗？
13. `self` 是什么？必须叫 `self` 吗？

**pydantic**
14. pydantic 和 typing 的分工是什么？
15. `model_validate_json` 和 `json.loads` 的区别？
16. 校验失败如何拿到结构化错误？如何把错误回灌给模型？

**async**
17. `async def` 定义的函数，直接调用会发生什么？
18. `asyncio.gather` 相当于 Java 的什么？
19. 为什么要用 `Semaphore`？
20. 在 async 函数里调用 `requests.get()` 会怎样？

<details>
<summary>参考答案</summary>

1. 空 list / 空 dict / 空 set。
2. `[1,2,3]`（引用同一个对象）。
3. `list(dict.fromkeys(items))`。
4. 前者不存在返回 `None`，后者抛 `KeyError`。
5. 最后三个元素。
6. 默认 list 在定义时只创建一次，所有调用共享。
7. tuple / dict。
8. `[2,2,2]`（闭包晚绑定）。
9. 文件被 import 时不执行 main，直接运行时执行。
10. `__init__`、`__repr__`、`__eq__`。
11. 同 6，避免所有实例共享同一个 list。
12. 不生效，只是给 IDE / 静态检查用。
13. 实例引用；不必叫 self，但是强约定。
14. typing 是写代码时的提示，pydantic 是运行时真实校验。
15. 后者只解析 JSON，前者解析 + 按模型校验/转换。
16. 捕获 `ValidationError`，用 `e.errors()`；把 `str(e)` 追加进 messages 让模型修正。
17. 返回协程对象，不执行。
18. `CompletableFuture.allOf`。
19. 限制并发数，避免触发限流/打爆内存。
20. 阻塞事件循环，所有并发任务一起卡住；应该用 `httpx.AsyncClient` 或 `asyncio.to_thread`。

</details>

---

## 15. 命令速查

```bash
# ---- venv ----
python3 -m venv .venv
source .venv/bin/activate
deactivate

# ---- pip ----
pip install openai httpx pydantic pydantic-settings python-dotenv
pip install -r requirements.txt
pip freeze > requirements.txt
pip list

# ---- uv（装了之后） ----
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv && source .venv/bin/activate
uv pip install openai
uv add openai
uv run script.py

# ---- 运行 ----
python hello.py
python -m src.batch
python -i hello.py          # 跑完进交互式，方便调试

# ---- 检查 ----
python --version
which python
pip show openai
```

---

## 附：给你的执行清单

**W1 Day 2（2h）**
- [ ] 用 `uv` 建环境并装依赖：`uv venv && uv pip install openai httpx pydantic pydantic-settings python-dotenv`
- [ ] 敲一遍 §3 的容器操作（不要复制）
- [ ] 敲一遍 §4.2 的可变默认参数坑，亲眼看到 `[1, 2]`

**W1 Day 3（2h）**
- [ ] 写一个 `@dataclass Message`，把你的 `hello-ai` 对话脚本里的 dict 换掉
- [ ] 用 pydantic 定义 `Ticket`，写 `extract()` + 校验 + 重试
- [ ] 跑一遍 §10.7 的并发脚本，观察串行 vs 并发的耗时差
- [ ] 手写一次 §11.3 的 `httpx` 流式解析

**做完的标志**：你能不看文档写出「带 pydantic 校验的 LLM 调用 + 并发批量 + 错误重试」，且能解释每一步为什么这么写。

> 卡住了把代码和报错贴进 `ERRORS.md`，对照 [`10`](../10-分阶段知识清单与学习资源.md) P0 的自测题查漏。
