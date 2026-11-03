# Zero-Unified-Assets

> Unity · 航天文化馆 AI 虚拟展馆 —— 交互脚本库

一套从「航天文化馆」VR 展馆项目里整理出来的 Unity 交互脚本。已按功能分类、统一为 UTF-8、
剥离了对闭源插件（XCSJ）的依赖，可以直接把 `Assets/Scripts` 拖进你自己的工程里复用。

项目不是完整工程，**只包含脚本**：场景、预制体、模型、贴图需自备（见 [快速开始](#快速开始)）。

---

## 项目里有什么

| 模块 | 说明 |
| --- | --- |
| **AI 讲解员** | 语音提问 → 百度语音识别 → DeepSeek 大模型作答 → 打字机效果上屏；另有一套文字输入框版本 |
| **空间站拆解** | 天和 / 天舟 / 梦天 / 神舟 / 问天 五舱段拆解与复位动画、讲解画布翻页、展厅相机切换 |
| **拼图游戏** | 三套鼠标拖拽吸附式拼图，全部归位后弹出通关面板 |
| **自由漫游** | 虚拟摇杆 + 相机朝向移动 |
| **展馆交互** | 双开自动门、视频播放/暂停、展品点击查看图片、触发区显隐面板 |
| **场景路由** | 启动页 → 航天 / AR，ESC 返回，退出程序 |

## 目录结构

```
Assets/
├── Scripts/
│   ├── AI/            3 + 1  ApiConfig · DeepSeekAPI · TalkManager · VoiceToText
│   ├── Interaction/   6      DoorMove · DoorBack · VideoPlay · VideoTrigger
│   │                         PictureClickManager · ToPuzzleTrigger
│   ├── Puzzle/        7      CE5PA · CE5PP · MainCPA · MainCPP
│   │                         SatellitePA · SatellitePP · ToPuzzle
│   ├── Roaming/       2      MyJoystick · MyJoystickBoxMove
│   ├── Station/       6      KJZMove · Movetext1 · Next · Start · ToShowRoom · UnitMove
│   └── UI/            5      Back · BackFromPicture · FunctionCanvas
│                             StartUIButtonManager · ToStart
└── StreamingAssets/
    └── api-config.example.json   密钥模板（真实的 api-config.json 被 .gitignore 排除）
```

## 脚本索引

> 「关键引用」是你需要在 Inspector 里手动拖进去的字段。

### AI

| 脚本 | 类名 | 职责 | 关键引用 |
| --- | --- | --- | --- |
| `AI/ApiConfig.cs` | `ApiConfig` | 读取 `StreamingAssets/api-config.json`，全局静态访问 | — |
| `AI/DeepSeekAPI.cs` | `DeepSeekAPI` | 调用 DeepSeek `/chat/completions`，用回调把回答交给 UI | `loadingImage`、`aiCharacter`（角色名 + 人设） |
| `AI/TalkManager.cs` | `TalkManager` | 文字输入框对话版：回车提交、手动排版、打字机输出 | `deepseekAPI`、`inputField`、`dialogueText` |
| `AI/VoiceToText.cs` | `VoiceToText` | 录音 → 百度语音识别 → 转成提问 → 打字机输出 | `deepseekAPI`、`dialogueText`、`voiceImage`、`waitImage` |

### Interaction

| 脚本 | 类名 | 职责 | 关键引用 |
| --- | --- | --- | --- |
| `Interaction/DoorMove.cs` | `TriggerMove` | 触发器进入后两扇门平滑打开 | `door1`/`door2`、`target1Pos`/`target2Pos` |
| `Interaction/DoorBack.cs` | `DoorBack` | 同上，目标坐标不同（用于复位） | 同上 |
| `Interaction/VideoPlay.cs` | `PlayVideo` | 同一按钮切换视频播放 / 暂停 | `vPlayer`、`button` |
| `Interaction/VideoTrigger.cs` | `VideoTrigger` | 进出触发区时显隐视频面板 | `gamObject` |
| `Interaction/PictureClickManager.cs` | `PictureClickManager` | 鼠标射线拾取展品，打开对应图片画布 | `canvas[]`、`transforms[]` |
| `Interaction/ToPuzzleTrigger.cs` | `ToPuzzleTrigger` | 进出触发区时显隐拼图面板 | `mgameObject` |

### Puzzle

| 脚本 | 类名 | 职责 | 关键引用 |
| --- | --- | --- | --- |
| `Puzzle/CE5PP.cs` 等三个 `*PP` | `CE5PP` / `MainCPP` / `SatellitePP` | 单块拼图：鼠标拖拽 + 距离吸附判定 | `camera`、`targetPosition`、`maxLen` |
| `Puzzle/CE5PA.cs` 等三个 `*PA` | `CE5PA` / `MainCPA` / `SatellitePA` | 汇总检测：所有块归位后显示通关面板 | `gameOverPanel` |
| `Puzzle/ToPuzzle.cs` | `ToPuzzle` | 点按钮切到拼图相机与画布 | `joystick`、`canva`、`NowCamera`、`NextCamera` |

三套 `*P` 脚本逻辑完全同构，只是各自场景独立使用，可按需保留一套。

### Roaming

| 脚本 | 类名 | 职责 | 关键引用 |
| --- | --- | --- | --- |
| `Roaming/MyJoystick.cs` | `MyJoystick` | 实现 `IDragHandler` 等接口的虚拟摇杆，输出 `inputVector` | `centerPoint`、`maxLen` |
| `Roaming/MyJoystickBoxMove.cs` | `MyJoystickBoxMove` | 按摇杆输入沿相机水平朝向平移目标 | `myJoystick`、`target`、`gameCamera` |

### Station

| 脚本 | 类名 | 职责 | 关键引用 |
| --- | --- | --- | --- |
| `Station/KJZMove.cs` | `KJZMove` | 五舱段拆解/复位、按钮互斥、主相机与展厅相机切换 | 五个舱段对象、三个按钮、两个相机 |
| `Station/Movetext1.cs` | `Movetext1` | 用 Animator 的 bool `IsPlay` 驱动讲解文字动画 | 自身 `Animator` |
| `Station/Next.cs` | `Next` | 讲解画布翻页 | `NowCanva`/`NextCanva`、`NowObject`/`NextObject` |
| `Station/Start.cs` | `Start` | 空间站内讲解 / 拆解 / 返回按钮总控 | 画布、按钮、相机、摇杆 |
| `Station/ToShowRoom.cs` | `ToShowRoom` | 切到展厅相机与展厅画布 | `showRoomCanvas`、`showRoomCamera` |
| `Station/UnitMove.cs` | `AnimationController` | 按钮点击播放指定名称的 Animator 状态 | `targetAnimator`、`triggerButton`、`animationName` |

### UI

| 脚本 | 类名 | 职责 | 关键引用 |
| --- | --- | --- | --- |
| `UI/Back.cs` | `Back` | 退出拼图，恢复漫游相机 / 摇杆 / 界面 | `joystick`、`NowCamera`/`NextCamera`、`canva` |
| `UI/BackFromPicture.cs` | `BackFromPicture` | 关闭图片查看画布 | `canvas` |
| `UI/FunctionCanvas.cs` | `FunctionCanvas` | 功能面板：ESC 回启动页、AI 面板开关 | `ai`、`ESCButton`、`AIButton`、`ESCAIButton` |
| `UI/StartUIButtonManager.cs` | `StartUIButtonManager` | 启动页按钮 → 航天 / AR / 退出 | `buttons[]` |
| `UI/ToStart.cs` | `ToStart` | ESC 回启动页 | — |

## 快速开始

### 1. 环境

- **Unity 2021.3 LTS 或更高**（脚本使用 `UnityWebRequest.result`，需 2020.2+）
- 使用**旧版 Input Manager**：`Edit > Project Settings > Player > Active Input Handling` 保持
  `Input Manager (Old)` 或 `Both`，脚本里的 `Input.GetMouseButton` 才能生效
- 使用 **UGUI**（`UnityEngine.UI.Text` / `InputField`），未使用 TextMeshPro
- 需要 `UnityEngine.Video`（随 Unity 安装）

### 2. 导入

把整个 `Assets/Scripts` 目录拖进你工程的 `Assets/` 下即可。目录结构不参与运行，可自由调整。

### 3. 配置 API 密钥

```bash
# 复制模板，填入自己的密钥
cp Assets/StreamingAssets/api-config.example.json Assets/StreamingAssets/api-config.json
```

```json
{
  "deepseekApiKey": "sk-你的DeepSeek密钥",
  "deepseekModel": "deepseek-chat",
  "deepseekApiUrl": "https://api.deepseek.com/chat/completions",
  "baiduApiKey": "百度智能云应用的 API Key",
  "baiduSecretKey": "百度智能云应用的 Secret Key"
}
```

`api-config.json` 已在 `.gitignore` 中排除，不会进仓库。

> **为什么密钥不放在 Inspector 里？**
> Unity 会把 `public` 字段的值序列化进 `.unity` / `.prefab` / `.asset` 文件。
> 只要提交了这些文件，密钥就永久留在 git 历史里，删掉也救不回来。
> 所以现在密钥只在 `StreamingAssets` 的独立 JSON 里，代码通过 `ApiConfig.Current` 读取。

> ⚠️ **从旧工程导入场景时必看**
> 关闭旧脚本的 `apiKey` / `api` / `secret` 字段**不会**清掉场景 YAML 里已存的值。
> 迁移前请先在 Inspector 里清空这几个字段并保存，或直接文本搜索场景文件：
>
> ```bash
> git grep -n -i -E 'apiKey|client_secret|"secret"' -- '*.unity' '*.prefab' '*.asset'
> ```
>
> 结果为空再提交。已经误传过的密钥，请到服务商后台**吊销并重新生成**。

### 4. 场景搭建要点

脚本里有一批**按名字硬编码**的 UI 对象判断，你的按钮命名必须和它们一致：

| 对象名 | 出现次数 | 所属脚本 |
| --- | --- | --- |
| `Button (Legacy)` | 4 | `Back`、`BackFromPicture`、`ToPuzzle`、`PlayVideo` |
| `MoveButton` / `MoveBackButton` | 3 / 3 | `KJZMove`、`Movetext1`、`Start` |
| `ESCButton` | 2 | `FunctionCanvas`、`ToStart` |
| `BackButton` | 2 | `KJZMove`、`Start` |
| `AIButton` / `ESCAIButton` | 1 / 1 | `FunctionCanvas` |
| `VoiceButton` | 1 | `VoiceToText` |
| `IntroduceButton` | 1 | `Start` |
| `ToShowButton` | 1 | `ToShowRoom` |
| `Next` | 1 | `Next` |

场景名同样是硬编码的：`StartUI`、`航天`、`AR`（见 `StartUIButtonManager`、`FunctionCanvas`、`ToStart`）。
想改场景名，记得同步修改这三处，并把场景加入 `File > Build Settings`。

## 外部服务

| 服务 | 用途 | 申请地址 |
| --- | --- | --- |
| DeepSeek 开放平台 | 大模型对话 | <https://platform.deepseek.com> |
| 百度智能云 · 短语音识别 | 语音转文字 | <https://console.bce.baidu.com/ai/#/ai/speech/overview/index> |

百度语音流程：先用 `API Key` / `Secret Key` 换 `access_token`，再把 PCM 音频转 Base64 调 `vop.baidu.com/server_api`。
采样率固定 16000、单声道、5 秒。

## 已知问题

整理时只做了分类和依赖剥离，**逻辑保持原样**。以下问题待后续修复，接手时请留意：

| 级别 | 位置 | 问题 |
| --- | --- | --- |
| 🔴 | `Station/KJZMove.cs:92` | `while (position != target)` 写在 `Update()` 里，单帧死循环；`deltaTime` 为 0 时直接冻结编辑器。且用 `!=` 比较浮点向量 |
| 🔴 | `AI/DeepSeekAPI.cs:61` | `response.choices[0]` 没有任何容错，断网 / 超时 / 限流都会空引用，且 `loadingImage` 不会消失 |
| 🟠 | 12 个文件共 21 处 | `EventSystem.current.currentSelectedGameObject.name` 取的是「当前选中对象」而非「本次点击对象」，点空白处即为 `null` → 空引用 |
| 🟠 | `AI/VoiceToText.cs:45,50` | `Microphone.GetPosition` 忙等之后又 `WaitForSeconds(5)`，实际要等约 10 秒 |
| 🟠 | `AI/VoiceToText.cs:113` | `response.result[0]` 未判空，识别失败时越界 |
| 🟠 | `Puzzle/`、`Interaction/` | 三套拼图、两套门脚本逐行重复，可合并为一个泛型 / 参数化实现 |
| 🟠 | `AI/TalkManager.cs`、`AI/VoiceToText.cs` | 排版与打字机逻辑各一份（手写 28 全角宽度换行，用 `goto`），应抽成公共组件 |
| 🟡 | `Roaming/MyJoystick.cs:13` | 用屏幕坐标 `eventData.position` 减世界坐标 `startPosition`，拖拽手感漂移 |
| 🟡 | `Roaming/MyJoystickBoxMove.cs:15` | `FixedUpdate` 里用 `Time.deltaTime`，应为 `Time.fixedDeltaTime` |
| 🟡 | 多处 | 世界坐标作为字段默认值硬编码，换场景即失效 |
| 🟡 | `AI/*` | 逐字符 `Debug.Log`，且每写一个字就重设 `Text.text`，触发整块 UI 重建 |
| 🟡 | `Interaction/PictureClickManager.cs` | `listLen` 未与 `canvas` / `transforms` 实际长度校验，越界即崩 |

**文件名与类名不一致**（Unity 允许，但检索时容易找不到）：

| 文件 | 类名 |
| --- | --- |
| `Interaction/VideoPlay.cs` | `PlayVideo` |
| `Interaction/DoorMove.cs` | `TriggerMove` |
| `Station/UnitMove.cs` | `AnimationController` |
| `Station/Start.cs` | `Start`（通用词，建议改 `StationStart`） |
| `Station/Next.cs` | `Next`（通用词，建议改 `StationNext`） |

## 后续计划

- [ ] 合并三套拼图、两套门脚本
- [ ] 修复 `KJZMove` 死循环与全局空引用问题
- [ ] 把按钮监听改为 `IPointerClickHandler` / `EventTrigger`，去掉按名字硬编码
- [ ] 抽出对话排版与打字机组件
- [ ] UI 迁移到 TextMeshPro
- [ ] 补一份可运行的示例场景

## 关于 XCSJ 插件

原工程基于 **XCSJ**（国产 Unity 虚拟仿真 / XR 快速开发框架，商业插件）搭建，但**本仓库代码并不依赖它**。

XCSJ 只出现在 4 个文件的 `using` 里，而这 4 个文件**没有用到任何一个 XCSJ 的符号** —— 属于 IDE 自动补全、或从 XCSJ 模板新建脚本时留下的无效引用。为了让大家不用安装付费插件就能编译，这些 `using` 已删除。

原始引用完整记录如下，便于回溯：

| 文件 | 原 `using` | 该文件实际用到的类型 |
| --- | --- | --- |
| `UI/BackFromPicture.cs` | `XCSJ.Interfaces` | `Transform`、`GameObject`、`Input`、`EventSystem` |
| `Interaction/VideoPlay.cs` | `XCSJ.Interfaces` | `VideoPlayer`、`GameObject`、`Input`、`EventSystem` |
| `Station/ToShowRoom.cs` | `XCSJ.PluginXXR.Interaction.Toolkit.Base` | `GameObject`、`Input`、`EventSystem` |
| `Station/KJZMove.cs` | `XCSJ.PluginXXR.Interaction.Toolkit.Base` | `GameObject`、`Transform`、`Vector3`、`Action`、`IEnumerator`、`WaitForEndOfFrame` |

### 如果你确实要接入 XCSJ

1. 在 Unity 中通过 Package Manager 或 `.unitypackage` 安装对应版本的 XCSJ；
2. 把上表中的 `using` 行加回对应文件；
3. 在本节补充你的 **XCSJ 版本号**与使用范围，方便下一个人对齐环境。

> ⚠️ XCSJ 是商业插件。请先确认你的授权允许再分发相关代码或资源；
> 不具备授权时，不要把它生成的 `Plugins/`、示例资源一起提交到公开仓库。

### 现有脚本与 XCSJ 的关系

本仓库的脚本只做 **GameObject 显隐 + 相机切换 + 基础动画驱动**，没有调用 XCSJ 的 XR 交互 API。
所以即便原场景是用 XCSJ 搭的，这些逻辑换成 Unity 原生方案（`EventTrigger`、
`XR Interaction Toolkit`、`Cinemachine`）照样成立。

## 说明

- 脚本已统一为 **UTF-8 + CRLF**，可直接被 Unity / Visual Studio / Rider 正确读取
- 除 Unity 内置模块外无其它第三方依赖；XCSJ 的无效引用已移除，详见上一节
- 本项目仅用于教学传承，请勿将接入的第三方 API 密钥用于生产环境

## 许可证

[MIT](LICENSE)
