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
| **拼图游戏** | 鼠标拖拽吸附式拼图：`PuzzlePiece` 管单块、`PuzzleGroup` 管分组判定，可复用于任意套数 |
| **自由漫游** | 虚拟摇杆 + 相机朝向移动 |
| **展馆交互** | 双开自动门、视频播放/暂停、展品点击查看图片、触发区显隐面板 |
| **场景路由** | 启动页 → 航天 / AR，ESC 返回，退出程序 |

## 目录结构

```
Assets/
├── Scripts/
│   ├── AI/            6      ApiConfig · DeepSeekAPI · DialogueLayout · DialogueView
│   │                         TalkManager · VoiceToText
│   ├── Interaction/   5      SlidingDoor · PlayVideo · VideoTrigger
│   │                         PictureClickManager · ToPuzzleTrigger
│   ├── Puzzle/        3      PuzzlePiece · PuzzleGroup · ToPuzzle
│   ├── Roaming/       2      MyJoystick · MyJoystickBoxMove
│   ├── Station/       6      KJZMove · Movetext1 · StationNext · StationStart
│   │                         ToShowRoom · AnimationController
│   └── UI/            5      Back · BackFromPicture · FunctionCanvas
│                             StartUIButtonManager · ToStart
└── StreamingAssets/
    └── api-config.example.json   密钥模板（真实的 api-config.json 被 .gitignore 排除）
```

## 脚本索引

> - **关键引用**：需要在 Inspector 里手动拖进去的字段。
> - **公开方法**：按钮的 `onClick` 应该绑到哪个方法。脚本不再按按钮名字判断，全部靠显式绑定。

### AI

| 脚本 | 类名 | 职责 | 关键引用 | 公开方法 |
| --- | --- | --- | --- | --- |
| `AI/ApiConfig.cs` | `ApiConfig` | 读取 `StreamingAssets/api-config.json`，全局静态访问 | — | — |
| `AI/DeepSeekAPI.cs` | `DeepSeekAPI` | 调用 DeepSeek `/chat/completions`，用回调把回答交给 UI；失败时给兜底文案 | `loadingImage`、`aiCharacter` | `SendToDeepSeek(message, callback)` |
| `AI/DialogueLayout.cs` | `DialogueLayout` | 纯文本工具：按显示宽度折行（全角 1、半角 0.5） | — | — |
| `AI/DialogueView.cs` | `DialogueView` | 对话区排版：分隔线、缩进、说话人标签、打字机输出 | `output` | `AppendPlayerLine`、`PlayReply` |
| `AI/TalkManager.cs` | `TalkManager` | 文字输入版对话：回车提交 → 显示发言 → 请求 AI → 逐字显示 | `deepSeek`、`dialogueView`、`inputField` | 由 `InputField` 的提交事件驱动 |
| `AI/VoiceToText.cs` | `VoiceToText` | 录音 → 百度语音识别 → 提问 → 逐字显示 | `deepSeek`、`dialogueView`、`recordingHint`、`waitingHint` | `StartListening` |

### Interaction

| 脚本 | 类名 | 职责 | 关键引用 | 公开方法 |
| --- | --- | --- | --- | --- |
| `Interaction/SlidingDoor.cs` | `SlidingDoor` | 触发器进入时双开门滑开或合上 | `leftPanel`/`rightPanel`、`leftOpenOffset`/`rightOpenOffset` | `Open`、`Close` |
| `Interaction/PlayVideo.cs` | `PlayVideo` | 播放 / 暂停视频 | `vPlayer` | `TogglePlayback` |
| `Interaction/VideoTrigger.cs` | `VideoTrigger` | 进出触发区时显隐视频面板 | `gamObject` | — |
| `Interaction/PictureClickManager.cs` | `PictureClickManager` | 射线拾取展品，打开对应图片画布 | `rayCamera`、`canvas[]`、`transforms[]` | — |
| `Interaction/ToPuzzleTrigger.cs` | `ToPuzzleTrigger` | 进出触发区时显隐拼图面板 | `mgameObject` | — |

### Puzzle

| 脚本 | 类名 | 职责 | 关键引用 | 公开方法 |
| --- | --- | --- | --- | --- |
| `Puzzle/PuzzlePiece.cs` | `PuzzlePiece` | 单块拼图：鼠标拖拽 + 距离吸附，归位后通知所属组 | `targetPosition`、`snapDistance`、`pickupCamera`、`group` | — |
| `Puzzle/PuzzleGroup.cs` | `PuzzleGroup` | 分组判定：组内全部归位后显示通关面板 | `completePanel` | — |
| `Puzzle/ToPuzzle.cs` | `ToPuzzle` | 切到拼图相机与画布 | `joystick`、`canva`、`canva2`、`NowCamera`、`NextCamera` | `EnterPuzzle` |

一套 `PuzzlePiece` + `PuzzleGroup` 可以重复使用任意多次，各套之间互不干扰。

### Roaming

| 脚本 | 类名 | 职责 | 关键引用 | 公开方法 |
| --- | --- | --- | --- | --- |
| `Roaming/MyJoystick.cs` | `MyJoystick` | 虚拟摇杆，把拖动换算成归一化方向 | `background`、`handle`、`radius` | 输出 `InputVector` |
| `Roaming/MyJoystickBoxMove.cs` | `MyJoystickBoxMove` | 按摇杆输入沿相机水平朝向平移目标 | `myJoystick`、`target`、`gameCamera` | — |

### Station

| 脚本 | 类名 | 职责 | 关键引用 | 公开方法 |
| --- | --- | --- | --- | --- |
| `Station/KJZMove.cs` | `KJZMove` | 舱段拆解 / 复位动画，相机切换 | `modules[]`（舱段 + 拆解位置）、三个按钮、两个相机 | `Disassemble`、`Reassemble`、`BackToMainCamera` |
| `Station/Movetext1.cs` | `Movetext1` | 用 Animator 的 bool 参数驱动讲解文字动画 | `targetAnimator`、`boolParameter` | `PlayIn`、`PlayOut` |
| `Station/StationNext.cs` | `StationNext` | 讲解画布翻页 | `NowCanva`/`NextCanva`、`NowObject`/`NextObject` | `ShowNext` |
| `Station/StationStart.cs` | `StationStart` | 空间站内按钮总控 | 画布、按钮、相机、摇杆 | `OpenIntroduction`、`StartDisassembly`、`RestoreModules`、`BackToRoaming` |
| `Station/ToShowRoom.cs` | `ToShowRoom` | 切到展厅相机与展厅画布 | `showRoomCanvas`、`showRoomCamera` | `EnterShowRoom` |
| `Station/AnimationController.cs` | `AnimationController` | 点击播放指定名称的 Animator 状态 | `targetAnimator`、`triggerButton`、`animationName` | `PlayAnimation`（在 Start 中自动绑定按钮） |

### UI

| 脚本 | 类名 | 职责 | 关键引用 | 公开方法 |
| --- | --- | --- | --- | --- |
| `UI/Back.cs` | `Back` | 退出拼图，恢复漫游相机 / 摇杆 / 界面 | `joystick`、`NowCamera`/`NextCamera`、`canva` | `BackToRoaming` |
| `UI/BackFromPicture.cs` | `BackFromPicture` | 关闭图片查看画布 | `canvas` | `ClosePicture` |
| `UI/FunctionCanvas.cs` | `FunctionCanvas` | 功能面板：返回启动页、AI 面板开合 | `ai`、`ESCButton`、`AIButton`、`joystick` | `BackToStartUI`、`OpenAiPanel`、`CloseAiPanel` |
| `UI/StartUIButtonManager.cs` | `StartUIButtonManager` | 启动页按钮 → 航天 / AR / 退出 | `buttons[]` | 在 Start 中自动绑定 |
| `UI/ToStart.cs` | `ToStart` | 返回启动页 | — | `BackToStartUI` |

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

> ⚠️ **场景文件里残留的密钥**
> 如果你曾经把 Key 直接填在 Inspector 的字段里，那么改脚本、删字段都**不会**清掉
> `.unity` / `.prefab` 里已经存下的值 —— 它们还在 YAML 文本中。
> 提交前先在 Inspector 里清空这些字段并保存，或直接搜索场景文件：
>
> ```bash
> git grep -n -i -E 'apiKey|client_secret|"secret"' -- '*.unity' '*.prefab' '*.asset'
> ```
>
> 结果为空再提交。已经误传过的密钥，请到服务商后台**吊销并重新生成**。

### 4. 场景搭建要点

**按钮绑定**：脚本不按对象名判断点击，而是由按钮的 `onClick` 直接调用脚本的公开方法。

操作路径：`Button` 组件 → `On Click ()` → `+` → 把挂脚本的物体拖进去 → 在方法下拉框里选。
每个脚本该用哪个方法，见上面「脚本索引」的 **公开方法** 一列。

常用绑定：

| 按钮 | 目标组件 | 选择的方法 |
| --- | --- | --- |
| 语音提问 | `VoiceToText` | `StartListening` |
| 拆解演示 | `KJZMove` | `Disassemble` |
| 舱段复位 | `KJZMove` | `Reassemble` |
| 进入拼图 | `ToPuzzle` | `EnterPuzzle` |
| 退出拼图 | `Back` | `BackToRoaming` |
| 打开 AI 面板 | `FunctionCanvas` | `OpenAiPanel` |
| 返回启动页 | `FunctionCanvas` / `ToStart` | `BackToStartUI` |

场景名仍是硬编码的：`StartUI`、`航天`、`AR`
（见 `StartUIButtonManager`、`FunctionCanvas`、`ToStart`）。
改场景名要同步改这三处，并把场景加入 `File > Build Settings`。

## 外部服务

| 服务 | 用途 | 申请地址 |
| --- | --- | --- |
| DeepSeek 开放平台 | 大模型对话 | <https://platform.deepseek.com> |
| 百度智能云 · 短语音识别 | 语音转文字 | <https://console.bce.baidu.com/ai/#/ai/speech/overview/index> |

百度语音流程：先用 `API Key` / `Secret Key` 换 `access_token`，再把 PCM 音频转 Base64 调 `vop.baidu.com/server_api`。
采样率固定 16000、单声道、5 秒。

## 已知问题

| 级别 | 位置 | 问题 |
| --- | --- | --- |
| 🟡 | `AI/DialogueView.cs` | 逐字输出时每写一个字就重设一次 `Text.text`，会触发整块 UI 重建；换成 TextMeshPro 可缓解 |

## 后续计划

- [x] 合并三套拼图、两套门脚本
- [x] 修复 `KJZMove` 死循环与全局空引用问题
- [x] 抽出对话排版与打字机组件（`DialogueLayout` + `DialogueView`）
- [x] `DeepSeekAPI` / `VoiceToText` 补网络错误处理
- [x] 按钮改为 `onClick` 显式绑定，去掉按名字硬编码
- [x] 文件名与类名对齐
- [ ] UI 迁移到 TextMeshPro
- [ ] 补一份可运行的示例场景

## 关于 XCSJ 插件

原工程基于 **XCSJ**（国产 Unity 虚拟仿真 / XR 快速开发框架，商业插件）搭建，但**本仓库代码并不依赖它**。

XCSJ 只出现在 4 个文件的 `using` 里，而这 4 个文件**没有用到任何一个 XCSJ 的符号** —— 属于 IDE 自动补全、或从 XCSJ 模板新建脚本时留下的无效引用。为了让大家不用安装付费插件就能编译，这些 `using` 已删除。

原始引用完整记录如下，便于回溯：

| 文件 | 原 `using` |
| --- | --- |
| `UI/BackFromPicture.cs` | `XCSJ.Interfaces` |
| `Interaction/PlayVideo.cs` | `XCSJ.Interfaces` |
| `Station/ToShowRoom.cs` | `XCSJ.PluginXXR.Interaction.Toolkit.Base` |
| `Station/KJZMove.cs` | `XCSJ.PluginXXR.Interaction.Toolkit.Base` |

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

- 脚本统一为 **UTF-8 + LF**（由 `.gitattributes` 保证仓库内一致），Unity / Visual Studio / Rider 均可正确读取
- 除 Unity 内置模块外无其它第三方依赖；XCSJ 的无效引用已移除，详见下一节
- 全部脚本已用 Unity 2021.3.33 的引用程序集做过编译校验，无语法与类型错误
- 本项目仅用于教学传承，请勿将接入的第三方 API 密钥用于生产环境

## 许可证

[MIT](LICENSE)
