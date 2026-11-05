# Git 与 GitHub 入门

> 如何从零把本地代码推上 GitHub，以及一些常见问题。

## 流程概览

```
改文件  →  git add  →  git commit  →  git push
          挑要提交的   打包成一次快照   传到 GitHub
```

- **add**：选出这次要提交的文件（不选的不进快照）
- **commit**：把这些改动打包成一个永久快照，附一句说明
- **push**：把本地快照传上去

---

## 1. 安装 Git（Windows）

在Git官网（<https://git-scm.com/download/win>）下载：

![Git 安装组件选择](images/git-install-components.png)

运行，中途有以下几处需要留意：

| 屏幕 | 选什么 | 为什么 |
| --- | --- | --- |
| Select Components | 确保勾 **`Windows Explorer integration → Open Git Bash here`** | 以后右键文件夹就能开终端，不用每次 `cd` |
| Default editor | **Visual Studio Code** 或 **Notepad** | 用默认的 Vim 进去容易出不来 |
| Initial branch name | 选 `Override`，填 **`main`** | GitHub 默认分支现在都叫 main，不一致会多一步麻烦 |
| Adjusting your PATH | 中间那项（`Git from the command line and also from 3rd-party software`） | 这样 PowerShell、VS Code 里也能用 git |
| Credential Manager | 保持 **`Git Credential Manager`** | 推送时能弹浏览器登录，靠它 |
| 其余屏幕 | 全部默认，一路 Next | — |

装完**关掉所有已打开的命令行窗口**（PATH 要重开才生效），验证：

```bash
git --version
```

### 怎么打开命令行

在仓库文件夹的**空白处右键** → `Git Bash Here`（Win11 需要先点「显示更多选项」）。

打开的窗口**已经在正确目录**里，省去 `cd` 的麻烦。

---

## 2. 配置你的身份

每次提交都会记录「谁改的」，所以要先设置：

```bash
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱"
```

### ⚠️ 注意：邮箱会公开在提交里

任何人 `git log` 都能看到，**还可能被爬虫抓走**。有三种方案：

| 方案 | 提交里显示 | 贡献图 | 适用于 |
| --- | --- | --- | --- |
| 真实邮箱 | `名字 <1234@qq.com>` | ✅ 计入 | 不在意邮箱公开 |
| GitHub 专用邮箱 | `名字 <ID+用户名@users.noreply.github.com>` | ✅ 计入 | 不暴露真实地址 |
| 随便编一个 | `名字 <name@localhost>` | ❌ 不计入 | 完全不想被关联 |

GitHub 专用邮箱在 **Settings → Emails → Keep my email addresses private** 里能看到。

![GitHub 隐私邮箱设置](images/github-private-email.png)

> 只想在当前仓库用某个身份，就去掉 `--global`，配置只写进这个仓库的 `.git/config`。
> 看当前生效的值：`git config user.name` / `git config user.email`

---

## 3. 准备远程仓库

先对号入座，三种情况走不同的路。

| 实际情况 | 对应方案 |
| --- | --- |
| 全新的项目，要把本地代码传上去 | [情况 A](#情况-a新建一个空仓库) |
| 仓库已经在 GitHub 上，本地还没有 | [情况 B](#情况-b克隆一个已有仓库) |
| 本地有代码，要推到**已有内容**的仓库 | [情况 C](#情况-c推到已有内容的仓库) |

### 情况 A：新建一个空仓库

打开 <https://github.com/new>：

| 字段 | 填什么 |
| --- | --- |
| Repository name | 和本地文件夹同名，最省心 |
| Public / Private | 想给别人看就 Public |
| Add a README file | ⚠️ **不勾** |
| Add .gitignore | ⚠️ **None** |
| Choose a license | ⚠️ **None** |

> **为什么都不勾**：本地已经有这些文件了。两边各初始化一份，历史互不相关，`push` 会被拒绝，
> 得先处理冲突——新手最容易卡在这里。

建完仓库，跳转到[第 4 章](#4-关联远程并推送)。

### 情况 B：克隆一个已有仓库

代码在 GitHub 上、你本地还没有，**不要手动建文件夹再复制**：

```bash
git clone https://github.com/用户名/仓库名.git
cd 仓库名
```

克隆会自动完成三件事：下载全部代码和历史、把 `origin` 指向该地址、检查出 `main` 分支。

之后直接改 → `git add` → `git commit` → `git push` 就行，**不需要再 `git remote add`**。

> **别人的仓库**：需要仓库所有者在 Settings → Collaborators 里邀请你，接受后才有推送权限。
> 没被邀请会报 `403 Permission denied`。想参与开源项目但没有权限，就走 Fork：
> 在自己账号下复制一份 → 推到你的 fork → 发起 Pull Request。

### 情况 C：推到已有内容的仓库

典型场景：GitHub 上建仓库时勾了 README，或者仓库里已经有别人的提交，而你在本地也写了一套代码。

两边**各有各的提交历史**，直接推会被拒绝：

```
! [rejected]  main -> main (non-fast-forward)
error: failed to push some refs
```

先建立关联，再把两条历史接起来：

```bash
# 1. 指向远程（已配置过就跳过，或改用 set-url 换地址）
git remote add origin https://github.com/用户名/仓库名.git

# 2. 把远程的提交拉下来
git fetch origin

# 3. 变基：把你的提交挪到远程提交的后面
git pull --rebase origin main --allow-unrelated-histories

# 4. 现在可以正常推送了
git push -u origin main
```

几个要点：

- **`--allow-unrelated-histories`**：默认 Git 拒绝合并两条无共同祖先的历史，加这个参数才放行。
  只有"新建仓库时勾了 README"这类情况才需要；
- **用 `--rebase` 而不是默认的 merge**：变基后历史是一条直线，不会多出"合并远程分支"这种噪音提交；
- **可能遇到冲突**：同一个文件两边都改过时，Git 会停下来让你手动合并，
  解决后 `git add 文件` → `git rebase --continue`。乱掉了就 `git rebase --abort` 重来；
- 推送前可以 `git log --oneline -5` 看一眼，确认顺序是「远程的提交 → 你的提交」。

---

## 4. 关联远程并推送

适用情况 A（本地有代码、远程是空的）。

```bash
# 如果是全新的空文件夹，先初始化（已有 .git 就跳过）
git init -b main

# 告诉本地仓库「远程在哪」，这条不联网、不上传
git remote add origin https://github.com/用户名/仓库名.git

# 推上去
git push -u origin main
```

`-u` 的作用是记住对应关系，**以后只要 `git push` / `git pull`**，不用再写 `origin main`。

### 首次推送会要求认证

会弹出 **Git Credential Manager** 窗口，通常是浏览器登录。如果它直接问你账号密码：

- 用户名：你的 GitHub 用户名
- 密码：⚠️ **不是账号密码**，必须是 **Personal Access Token**

### 生成 Token

**GitHub → 头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token**

- Note：随便写，如 `push-assets`
- Expiration：30 / 90 天
- Scopes：勾 **`repo`**（整个大项）
- 生成后复制 `ghp_...`，**只显示一次**

用户名密码框里：用户名填账号，密码粘这串 token。

### 成功的标志

```
Writing objects: 100% (136/136), 63.42 KiB | 1.29 MiB/s, done.
To https://github.com/用户名/仓库名.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

---

## 5. 日常三件套

```bash
git status              # 看改了什么
git add -A              # 全部加入（或 git add 具体文件）
git commit -m "改了什么"  # 打包，写说明
git push                # 上传
```

### 提交说明怎么写

一条提交只有一个说明，**动词开头，说清改了什么**：

| ❌ | ✅ |
| --- | --- |
| `Update README.md` | `README：更新目录结构说明` |
| `修改` | `修复登录页按钮无响应` |
| `123` | `课程资料：习题归入 习题/ 子目录` |

半年后你自己看历史，能一眼找到就是好说明。

### 改之前先拉取

如果这个仓库**你在网页上也编辑过**，本地就落后了。养成习惯：

```bash
git pull        # 先同步，再改
```

---

## 6. 常见问题

按报错关键词查，左侧第一列是终端里显示的内容。

| 报错 / 现象 | 原因 | 解决 |
| --- | --- | --- |
| `Password authentication is not supported` | 用了账号密码，GitHub 早已废弃 | 改用 **Token** 当密码 |
| `Invalid username or token` | 同上，或 token 过期/被吊销 | 重新生成 token |
| `Connection was reset` | 连接被中途掐断（网络受限） | 开代理，见 [6.1](#61-连不上-github) |
| `CRYPT_E_NO_REVOCATION_CHECK` | 证书吊销检查失败（代理转发导致） | 见 [6.2](#62-证书报错) |
| `remote origin already exists` | 远程已经配置过 | `git remote set-url origin <新地址>` |
| `src refspec main does not match any` | 本地分支不叫 main | `git branch` 看真实名字，改成 `git push -u origin 那个名字` |
| `! [rejected] ... (non-fast-forward)` | 远程有本地没有的提交（如建仓库时勾了 README） | 见 [情况 C](#情况-c推到已有内容的仓库) |
| `Filename too long` | Windows 路径长度限制 | `git config --global core.longpaths true` |
| 中文文件夹显示成 `\350\257\276` | Git 默认转义非 ASCII | `git config --global core.quotepath false` |
| 网页上传后本地推不上去 | 两边历史分叉 | 见 [情况 C](#情况-c推到已有内容的仓库) |
| `Modified` 里一堆没改过的文件 | 换行符被全局配置来回转换 | 别动 `core.autocrlf`，交给 `.gitattributes` |

### 6.1 连不上 GitHub

通过下面的命令先确认连接到哪了：

```bash
curl -I https://github.com
```

如果能连通但 `git push` 失败，看详细握手过程：

```bash
GIT_CURL_VERBOSE=1 git push 2>&1 | head -30
```

重点看以下两行：

- `Trying 20.205.243.x:443` → 直连公网，正常
- `Trying 127.0.0.1:443` → ⚠️ **请求被劫持到本机了**，继续看 6.3

**需要一个代理**。有代理软件的话，让 Git 走它（端口按你的软件改，Clash 常见 7890）：

```bash
git config --global http.proxy  http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

取消：

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 6.2 证书报错

```
schannel: next InitializeSecurityContext failed: CRYPT_E_NO_REVOCATION_CHECK
```

Windows 的 TLS 实现（schannel）要去查证书有没有被吊销，查不到就拒绝连接——
走代理时几乎必现。

```bash
git config --global http.schannelCheckRevoke false
```

还不行就换 OpenSSL 后端：

```bash
git config --global http.sslBackend openssl
```

> 代价是少了一层安全校验。不用代理之后建议改回来：
> `git config --global http.schannelCheckRevoke true`

### 6.3 加速器/代理劫持了 hosts

有些加速工具（如 Steam++ 的「GitHub 加速」）会改写 `C:\Windows\System32\drivers\etc\hosts`，
把 `github.com` 指向 `127.0.0.1`，再由本机进程转发。

**症状**：`GIT_CURL_VERBOSE` 显示 `Trying 127.0.0.1:443`，或明明密码对却一直 `Invalid username or token`。

**原因**：这类工具不保证原样转发响应头，GitHub 的认证挑战头被吃掉，Git 走不完认证流程。

**解决**：在加速器里关掉 GitHub 加速（或彻底退出进程，注意不是关窗口），
让它把 hosts 恢复。验证：

```bash
grep -c github /c/Windows/System32/drivers/etc/hosts   # 期望 0
netstat -ano | grep ':443 .*LISTENING'                 # 期望无输出
```

**别手动改 hosts**：加速器下次启动会再写回去。要在它自己的设置里关。

### 6.4 token 泄露了怎么办

**吊销token**：在<https://github.com/settings/tokens> ，找到那个 token ，点击 `Delete`。

然后重新生成一个。如果 token 曾经写进过 URL（`https://用户名:ghp_xxx@github.com/...`），
它还会留在两个地方：

```bash
grep -r "ghp_" .git/config          # 1. 仓库配置
history | grep ghp_                 # 2. 终端历史
```

配置里残留就改回来：

```bash
git remote set-url origin https://github.com/用户名/仓库名.git
```

---

## 7. 紧急措施

### 提交说明写错了（还没推送）

```bash
git commit --amend -m "正确的说明"
```

### 提交了不该提交的文件（还没推送）

```bash
git reset --soft HEAD~1     # 撤销这次提交，改动保留在暂存区
# 调整文件后重新提交
```

### 误把大文件或 `.venv` 提交了（还没推送）

```bash
git rm -r --cached 路径/.venv     # 从版本控制里移除，本地文件保留
echo ".venv/" >> .gitignore
git commit -m "移除误提交的虚拟环境"
```

> 如果**已经推送**，这样做只是让它不出现在最新版本里，**历史中仍然存在**，
> 仓库体积不会变小。彻底清理要用 `git filter-repo` 或 BFG，代价是改写全部历史。

### 已推送的提交要撤销

用 `revert`（生成一个反向提交，安全）：

```bash
git revert <提交号>
```

别对已经被别人拉过的分支用 `reset` + `--force`。

### 提交的作者信息不对

```bash
git config user.name  "新名字"
git config user.email "新邮箱"

# 把全部提交的作者重置成上面配置的身份
GIT_SEQUENCE_EDITOR=: git rebase --root --exec "git commit --amend --no-edit --reset-author"

# 覆盖远程
git push --force-with-lease
```

> 优先用 `--force-with-lease` 而不是 `--force`：远程如果在此期间被别人改过，它会拒绝，而不是覆盖掉。

### 手滑 force push 覆盖了东西

本地 `reflog` 会保留约 90 天的历史：

```bash
git reflog                  # 找到被覆盖前的提交号
git reset --hard <提交号>
git push --force-with-lease
```

---

## 8. 安全习惯

1. **密钥、token、密码不进代码**。写进配置文件的，那个文件必须加进 `.gitignore`；
2. **token 不要塞进远程地址**，用完记得 `git remote set-url` 改回去；
3. 提交前自查一遍：

   ```bash
   git grep -n -i -E 'apiKey|client_secret|sk-[a-zA-Z0-9]{16,}|"secret"' -- . ':!*example*'
   ```

4. 已经泄露的密钥，**去服务商后台吊销重建**——删文件救不回 git 历史。

---

## 常用命令

```bash
git status                          # 现在改了什么
git diff                            # 具体改了哪几行
git add -A && git commit -m "说明"   # 打包
git push                            # 上传
git pull                            # 同步远程
git log --oneline -10               # 最近 10 次提交
git remote -v                       # 远程地址
```
