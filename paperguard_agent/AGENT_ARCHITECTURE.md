# PaperGuard Multi-Agent Architecture

## 🤖 真正的Agent系统 vs Workflow

### 为什么这是Multi-Agent System而不是Workflow？

#### ✅ Agent的核心特征（PaperGuard已具备）

1. **自主性 (Autonomy)**
   ```python
   class CitationVerifierAgent(BaseAgent):
       def reason(self, observation):
           # Agent自主决定验证策略
           # 优先级：有DOI > 最近论文 > 旧论文
           priority_refs = self._prioritize(references)
           return {"strategy": "parallel_search"}
   ```

2. **反应性 (Reactivity)**
   ```python
   # 根据观察动态调整
   if ref.doi:
       strategy = "direct_doi_lookup"
   else:
       strategy = "fuzzy_title_search"
   ```

3. **社交性 (Social Ability)**
   ```python
   class AgentMessage:
       sender: str      # 发送Agent
       receiver: str    # 接收Agent
       content: Any     # 结构化消息
   
   # Agent间通信
   parser.send_message("citation_verifier", "PARSED_DATA", result)
   ```

4. **目标导向 (Goal-oriented)**
   - **ParserAgent**: 目标是正确解析论文结构
   - **CitationVerifierAgent**: 目标是验证引用真实性
   - **SupervisorAgent**: 目标是协调完成整体审查

#### ❌ Workflow的特点（旧版有这些问题）

- 预定义执行顺序
- 无自主决策能力
- 函数式调用链
- 没有Agent间通信

## 🏗️ 系统架构

### Agent层次结构

```
┌─────────────────────────────────────────────────────────────┐
│                    SupervisorAgent                          │
│  - 协调整体流程                                              │
│  - 决定执行哪些子Agent                                       │
│  - 聚合结果                                                  │
│  - 管理Agent间通信                                           │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ↓                    ↓                    ↓
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  ParserAgent     │ │CitationVerifier  │ │ ClaimVerifier    │
│                  │ │     Agent        │ │     Agent        │
│  感知: 论文文本   │ │ 感知: 引用列表   │ │ 感知: 论断+引用  │
│  推理: 选择策略   │ │ 推理: 优先级排序 │ │ 推理: LLM验证    │
│  行动: 解析结构   │ │ 行动: 查询DB     │ │ 行动: 判断支持性 │
│  记忆: 解析轨迹   │ │ 记忆: 验证缓存   │ │ 记忆: 验证历史   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### Agent通信协议

```python
# 消息格式
AgentMessage(
    sender="parser_agent",
    receiver="citation_verifier",
    msg_type="PARSED_DATA",
    content={
        "citations": [...],
        "references": [...]
    },
    timestamp="2026-06-12T..."
)
```

## 🧠 Agent内部架构

### BaseAgent（所有Agent的基类）

```python
class BaseAgent(ABC):
    """每个Agent的BDI架构（Belief-Desire-Intention）"""
    
    # Perception（感知）
    def perceive(self, observation) -> Dict:
        """从环境或其他Agent接收输入"""
        
    # Reasoning（推理/决策）
    @abstractmethod
    def reason(self, observation) -> Dict:
        """基于观察做出决策"""
        
    # Action（行动）
    @abstractmethod
    def act(self, decision) -> Any:
        """执行决策"""
        
    # Memory（记忆）
    self.memory: List[Dict]  # 维护状态和历史
    
    # Communication（通信）
    def send_message(self, receiver, content):
        """向其他Agent发送消息"""
```

### 执行循环

```
输入 → Perceive → Reason → Act → 输出
         ↑          ↓        ↓
         └─────── Memory ────┘
```

## 📊 与Workflow的对比

| 特性 | Workflow (旧版) | Multi-Agent System (新版) |
|-----|----------------|--------------------------|
| **执行模式** | 固定顺序 | 动态协调 |
| **决策能力** | 无，预定义 | 每个Agent自主决策 |
| **通信方式** | 函数返回值 | 结构化消息传递 |
| **状态管理** | 全局变量 | 每个Agent独立memory |
| **可追溯性** | 日志 | Agent轨迹（trace） |
| **扩展性** | 修改pipeline | 添加新Agent |
| **容错性** | 一个失败全失败 | Agent独立失败 |

## 🎯 Agent特性展示

### 1. 自主决策示例

```python
class CitationVerifierAgent:
    def reason(self, observation):
        references = observation["raw"]["references"]
        
        # Agent自主决定优先级
        for ref in references:
            priority = 0
            if ref.doi:
                priority += 3  # DOI最可靠
            if ref.year >= 2020:
                priority += 2  # 最近论文
            if ref.title:
                priority += 1  # 有标题
        
        # 自主选择验证策略
        return {
            "references_to_verify": top_priority_refs,
            "strategy": "parallel_search"  # Agent决定并行还是串行
        }
```

### 2. 反应式行为

```python
def act(self, decision):
    for ref in decision["references_to_verify"]:
        # 根据结果动态调整
        if ref.ref_id in self.verified_cache:
            # 已验证过，跳过
            continue
        
        candidates = search_all_sources(ref)
        
        if not candidates:
            # 未找到，改变策略
            self._try_alternative_search(ref)
```

### 3. Agent通信

```python
# SupervisorAgent协调
supervisor = SupervisorAgent()

# 发送任务给子Agent
parser_msg = supervisor.send_message(
    receiver="parser_agent",
    msg_type="PARSE_REQUEST",
    content={"paper": paper_content}
)

# 接收子Agent结果
parsed_result = parser.receive_message(parser_msg)
```

### 4. 可追溯的验证轨迹

```python
# 每个Agent记录自己的决策过程
agent.memory = [
    {"type": "perception", "data": "Received 40 references", "timestamp": "..."},
    {"type": "reasoning", "data": "Prioritized by DOI presence", "timestamp": "..."},
    {"type": "action", "data": "Verified ref-1 via Crossref", "timestamp": "..."},
    {"type": "action", "data": "Verified ref-2 via S2", "timestamp": "..."},
]

# 导出为验证轨迹
trace = agent.get_trace()
```

## 🚀 如何使用Agent模式

### 在Web界面中

1. 启动应用：`streamlit run app_enhanced.py`
2. 在侧边栏选择 **"Multi-Agent System 🤖"**
3. 上传论文并运行审查
4. 查看 **"Agent Execution Traces"** 部分

### 在代码中

```python
from paperguard.pipeline_agent import run_audit_with_agents

# 使用Multi-Agent系统
report = run_audit_with_agents(
    paper_content=text,
    mode="Full",
    max_claims=10
)

# 查看参与的Agent
for trace in report.agent_traces:
    agent_id = trace[0]["agent"]
    role = trace[0]["role"]
    print(f"Agent: {agent_id} ({role})")
    
    # 查看Agent决策过程
    for step in trace:
        print(f"  {step['type']}: {step['data']}")
```

## 💡 Agent架构的优势

### 1. 可解释性
每个Agent的决策过程可追溯，符合"验证Agent而非仅验证输出"的课程主题

### 2. 可扩展性
添加新功能只需实现新Agent，无需修改现有代码

```python
class TableVerifierAgent(BaseAgent):
    """新增：验证表格数字一致性"""
    def reason(self, observation):
        # 新Agent的独立逻辑
        pass
```

### 3. 容错性
单个Agent失败不影响其他Agent

### 4. 并行执行
多个Agent可以并行工作（未来可用async实现）

## 📚 理论基础

PaperGuard的Agent设计基于：

1. **BDI模型** (Belief-Desire-Intention)
   - Belief: memory中存储的知识
   - Desire: Agent的目标（验证引用、检测论断）
   - Intention: reason()中的决策

2. **消息传递架构**
   - Agent通过AgentMessage通信
   - 异步、解耦、可扩展

3. **多智能体协作**
   - SupervisorAgent作为协调者
   - 子Agent专注各自领域
   - 结果聚合和冲突解决

## 🎓 课程对应

| 课程要求 | PaperGuard实现 |
|---------|---------------|
| Agent自主性 | ✅ 每个Agent自主决策验证策略 |
| Agent反应性 | ✅ 根据验证结果动态调整 |
| Agent通信 | ✅ AgentMessage协议 |
| 验证轨迹 | ✅ 每个Agent的memory记录决策 |
| 多Agent协作 | ✅ SupervisorAgent协调 |

---

**总结：PaperGuard现在是真正的Multi-Agent System！** 🤖✨
