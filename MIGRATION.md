# 从旧版本迁移

这份文档面向**已经有一份旧版场景**的使用者：把旧版工程升级到当前脚本，需要替换哪些组件、改哪些字段。

如果是从零开始搭场景，直接看 [README](README.md) 的「脚本索引」即可，本文件可以忽略。

> 旧组件被删除后，场景里对应的位置会显示 **Missing Script**。按下面的表逐个替换即可。

## 拼图

| 旧脚本 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `CE5PP` / `MainCPP` / `SatellitePP` | `PuzzlePiece` | 逐块替换；`m_Camera` / `camera` → `pickupCamera`，`maxLen` → `snapDistance`；`group` 留空会自动向父节点查找 `PuzzleGroup` |
| `CE5PA` / `MainCPA` / `SatellitePA` | `PuzzleGroup` | 挂在原来承载拼图块的父节点上，`gameOverPanel` → `completePanel` |

替换后每组拼图由「一个 `PuzzleGroup` + 若干 `PuzzlePiece`」构成，同一场景可以放多组，互不干扰。

## 自动门

| 旧脚本 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `DoorMove`（类名 `TriggerMove`） | `SlidingDoor` | `onEnter` 设为 `Open`；`door1` / `door2` → `leftPanel` / `rightPanel`，`target1Pos` / `target2Pos` → `leftOpenPosition` / `rightOpenPosition` |
| `DoorBack` | `SlidingDoor` | `onEnter` 设为 `Close`，其余同上 |

想让门在触发器离开时自动关回去，勾上 `toggleOnExit`（旧版没有这个行为）。

## 按钮点击

新增了 `UI/UiPointer.cs`，所有脚本里原来判断

```csharp
EventSystem.current.currentSelectedGameObject.name == "X"
```

的地方，现在都改成

```csharp
UiPointer.IsClickOn("X")
```

**按钮名不需要改**，Inspector 里也不需要额外连线。

## 对话显示

排版和打字机效果已抽到独立组件里，场景中需要补两个新组件：

| 旧写法 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `TalkManager.dialogueText` / `typingSpeed` | `DialogueView` | 在对话文本对象上挂 `DialogueView`，把 `output` 指到同一个 `Text`；`TalkManager` / `VoiceToText` 的 `dialogueView` 字段拖入这个组件 |
| `VoiceToText.dialogueText` | 同上 | 同时改名字段：`deepseekAPI` → `deepSeek`，`voiceImage` → `recordingHint`，`waitImage` → `waitingHint` |

折行宽度和缩进量改到 `DialogueView` 上调整（`lineWidth`、`indentSpaces`），不再散落在两个脚本里。

## 空间站舱段

| 旧写法 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `KJZMove` 的 `tianhe` / `tianzhou` / … 五个字段 | `modules[]` 数组 | 数组里加 5 项，每项填「舱段对象 + 拆解位置」；合拢位置仍由脚本在 Start 时自动记录 |

以后要加第六个舱段，只需在数组里追加一项，不用改代码。

## 迁移检查清单

- [ ] 场景里搜 `Missing Script`，按上表替换组件
- [ ] 各组件重新拖引用（拼图组、对话视图、舱段数组）
- [ ] 确认按钮名未被改动（`UiPointer` 仍按名字匹配）
- [ ] 跑一次完整流程：进场景 → 语音/文字提问 → 拼图 → 舱段拆解复位
