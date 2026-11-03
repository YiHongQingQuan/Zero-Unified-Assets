# 从旧版本迁移

这份文档面向**已经有一份旧版场景**的使用者：把旧版工程升级到当前脚本，需要替换哪些组件、改哪些字段。

如果是从零开始搭场景，直接看 [README](README.md) 的「脚本索引」即可，本文件可以忽略。

> 旧组件被删除后，场景里对应的位置会显示 **Missing Script**。按下面的表逐个替换即可。

## 1. 按钮：从「按名字判断」改为「显式绑定」

**这是变化最大的一处。** 旧脚本在 `Update` 里拿鼠标点击去比对按钮名字，现在改为由按钮直接调用方法，
因此**按钮名字不再有约束**，但**需要在 Inspector 里手动绑一次**。

| 旧写法 | 新做法 |
| --- | --- |
| 脚本内判断 `name == "MoveButton"` | 按钮的 `On Click ()` → 拖入挂脚本的物体 → 选方法 |
| 按钮名必须叫 `Button (Legacy)` / `ESCButton` / … | 名字随意，只认绑定关系 |
| 按键由脚本每帧轮询 | 由 UGUI 事件触发 |

各个按钮该绑哪个方法：

| 按钮用途 | 目标组件 | 方法 |
| --- | --- | --- |
| 语音提问 | `VoiceToText` | `StartListening` |
| 播放 / 暂停视频 | `PlayVideo` | `TogglePlayback` |
| 进入拼图 | `ToPuzzle` | `EnterPuzzle` |
| 退出拼图 | `Back` | `BackToRoaming` |
| 关闭图片画布 | `BackFromPicture` | `ClosePicture` |
| 打开 AI 面板 | `FunctionCanvas` | `OpenAiPanel` |
| 收起 AI 面板 | `FunctionCanvas` | `CloseAiPanel` |
| 返回启动页 | `FunctionCanvas` / `ToStart` | `BackToStartUI` |
| 拆解演示 | `KJZMove` | `Disassemble` |
| 舱段复位 | `KJZMove` | `Reassemble` |
| 切回主相机 | `KJZMove` | `BackToMainCamera` |
| 进入展厅 | `ToShowRoom` | `EnterShowRoom` |
| 讲解翻页 | `StationNext` | `ShowNext` |
| 讲解 / 拆解 / 返回 | `StationStart` | `OpenIntroduction`、`StartDisassembly`、`RestoreModules`、`BackToRoaming` |
| 讲解文字进出 | `Movetext1` | `PlayIn`、`PlayOut` |

`UI/UiPointer.cs` 已删除，用它做的名字匹配一并去掉。

## 2. 拼图

| 旧脚本 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `CE5PP` / `MainCPP` / `SatellitePP` | `PuzzlePiece` | 逐块替换；`m_Camera` / `camera` → `pickupCamera`，`maxLen` → `snapDistance`；`group` 留空会自动向父节点查找 `PuzzleGroup` |
| `CE5PA` / `MainCPA` / `SatellitePA` | `PuzzleGroup` | 挂在承载拼图块的父节点上，`gameOverPanel` → `completePanel` |

替换后每组拼图由「一个 `PuzzleGroup` + 若干 `PuzzlePiece`」构成，同一场景可以放多组，互不干扰。

## 3. 自动门

| 旧脚本 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `DoorMove`（类名 `TriggerMove`） | `SlidingDoor` | `onEnter` 设为 `Open`；`door1` / `door2` → `leftPanel` / `rightPanel` |
| `DoorBack` | `SlidingDoor` | `onEnter` 设为 `Close`，其余同上 |

打开位置从**世界坐标**改成了**相对关闭位置的偏移**（`leftOpenOffset` / `rightOpenOffset`），
默认值取自原工程的坐标差，换场景或挪门都不用重新量。想让门在触发器离开时自动关回，勾上 `toggleOnExit`。

## 4. 对话显示

排版和打字机效果已抽到独立组件里，场景中需要补两个新组件：

| 旧写法 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `TalkManager.dialogueText` / `typingSpeed` | `DialogueView` | 在对话文本对象上挂 `DialogueView`，把 `output` 指到同一个 `Text`；`TalkManager` / `VoiceToText` 的 `dialogueView` 字段拖入这个组件 |
| `VoiceToText.dialogueText` | 同上 | 同时改名字段：`deepseekAPI` → `deepSeek`，`voiceImage` → `recordingHint`，`waitImage` → `waitingHint` |

折行宽度和缩进量改到 `DialogueView` 上调整（`lineWidth`、`indentSpaces`），不再散落在两个脚本里。

## 5. 空间站舱段

| 旧写法 | 新组件 | 需要做的事 |
| --- | --- | --- |
| `KJZMove` 的 `tianhe` / `tianzhou` / … 五个字段 | `modules[]` 数组 | 数组里加 5 项，每项填「舱段对象 + 拆解位置」；合拢位置仍由脚本在 Start 时自动记录 |
| `KJZMove` 的 Update 轮询 | 按钮绑定 | 三个按钮分别绑到 `Disassemble`、`Reassemble`、`BackToMainCamera` |

以后要加第六个舱段，只需在数组里追加一项，不用改代码。

## 6. 摇杆

| 旧字段 | 新字段 | 说明 |
| --- | --- | --- |
| `centerPoint`（`Transform`） | `background`（`RectTransform`） | 摇杆底盘，决定活动范围 |
| — | `handle`（`RectTransform`） | 摇杆头，跟随拖动移动 |
| `maxLen` | `radius` | 语义不变，仍是可移动半径（像素） |
| `inputVector` 字段 | `InputVector` 属性 | `MyJoystickBoxMove` 已同步改为读取该属性 |

换算方式改为 `RectTransformUtility.ScreenPointToLocalPointInRectangle`，
在不同分辨率、任意 Canvas 位置下都能得到正确方向。

## 7. 展品点击

`PictureClickManager` 删掉了 `listLen` 字段：现在按 `canvas` 与 `transforms` 的**较短长度**遍历，
并跳过空引用，不会再越界。新增可选字段 `rayCamera`，留空则用 `Camera.main`。

## 8. 脚本改名

| 旧文件（类名） | 新文件（类名） | 影响 |
| --- | --- | --- |
| `Station/Start.cs`（`Start`） | `Station/StationStart.cs`（`StationStart`） | 类名变了，需重新挂组件 |
| `Station/Next.cs`（`Next`） | `Station/StationNext.cs`（`StationNext`） | 类名变了，需重新挂组件 |
| `Interaction/VideoPlay.cs`（`PlayVideo`） | `Interaction/PlayVideo.cs`（`PlayVideo`） | 仅文件名，类名不变 |
| `Station/UnitMove.cs`（`AnimationController`） | `Station/AnimationController.cs`（`AnimationController`） | 仅文件名，类名不变 |
| `UI/UiPointer.cs`（`UiPointer`） | 已删除 | 见第 1 节 |

## 迁移检查清单

- [ ] 场景里搜 `Missing Script`，按上表替换组件
- [ ] 给每个按钮绑好 `onClick`（第 1 节的方法对照表）
- [ ] 各组件重新拖引用（拼图组、对话视图、舱段数组、摇杆底盘与摇杆头）
- [ ] 跑一次完整流程：进场景 → 语音/文字提问 → 拼图 → 舱段拆解复位 → 展厅
