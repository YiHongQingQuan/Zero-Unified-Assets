# =============================================================================
#  picker.ps1 - choose the Python interpreter used by LaTeX2Word
#
#  Called by scripts\find-python.cmd. Two modes:
#     select   : several candidates, let the user pick one
#     missing  : nothing usable was found, offer to browse / download
#
#  Contract with the batch caller:
#     -List <file>   UTF-8, lines: path|version|bits|source
#     -Out  <file>   written as UTF-8 (no BOM): line1 = path or CANCEL,
#                    line2 = remember=1|0
#     exit 0 = chosen, 1 = cancelled, 2 = GUI unavailable
#
#  Must stay UTF-8 **with BOM**: Windows PowerShell 5.1 reads BOM-less .ps1
#  files as ANSI and the Chinese strings below would turn into garbage.
# =============================================================================
param(
    [Parameter(Mandatory = $true)][string]$List,
    [Parameter(Mandatory = $true)][string]$Out,
    [ValidateSet('select', 'missing')][string]$Mode = 'select',
    [string]$Capture = ''
)

$ErrorActionPreference = 'Stop'

try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()
} catch {
    exit 2
}

# ---------------------------------------------------------------- helpers

function Get-SourceLabel([string]$tag) {
    switch ($tag) {
        'env'      { return '环境变量' }
        'cfg'      { return '配置文件' }
        'venv'     { return '现有环境' }
        'py'       { return 'py 启动器' }
        'path'     { return 'PATH' }
        'registry' { return '注册表' }
        'dirs'     { return '常见目录' }
        'browse'   { return '手动选择' }
        'chosen'   { return '已选择' }
        default    { return $tag }
    }
}

function Get-SortKey($version, $bits) {
    $parts = @('0', '0', '0')
    $v = $version -split '\.'
    for ($i = 0; $i -lt 3 -and $i -lt $v.Count; $i++) { $parts[$i] = $v[$i] }
    $flag = '0'
    if ($bits -eq '64') { $flag = '1' }
    $a = 0; $b = 0; $c = 0
    [void][int]::TryParse($parts[0], [ref]$a)
    [void][int]::TryParse($parts[1], [ref]$b)
    [void][int]::TryParse($parts[2], [ref]$c)
    return ('{0:D3}{1:D3}{2:D3}{3}' -f $a, $b, $c, $flag)
}

function Read-Candidates([string]$path) {
    $rows = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $path)) { return $rows }
    foreach ($line in (Get-Content -LiteralPath $path -Encoding UTF8)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line.Split('|')
        if ($parts.Count -lt 3) { continue }
        $item = New-Object psobject
        $item | Add-Member NoteProperty Path $parts[0]
        $item | Add-Member NoteProperty Version $parts[1]
        $item | Add-Member NoteProperty Bits $parts[2]
        $src = ''
        if ($parts.Count -ge 4) { $src = $parts[3] }
        $item | Add-Member NoteProperty Source $src
        $item | Add-Member NoteProperty SortKey (Get-SortKey $parts[1] $parts[2])
        [void]$rows.Add($item)
    }
    return $rows
}

function Test-PythonExe([string]$exe) {
    if (-not (Test-Path -LiteralPath $exe)) { return $null }
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $exe
        $psi.Arguments = '-X utf8 -c "import sys,venv,ensurepip;print(sys.version_info[0],sys.version_info[1],sys.version_info[2],sys.executable)"'
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        if (-not $proc.WaitForExit(8000)) {
            try { $proc.Kill() } catch { }
            return $null
        }
        $text = $proc.StandardOutput.ReadToEnd().Trim()
        if ([string]::IsNullOrWhiteSpace($text)) { return $null }
        $bits = $text.Split(' ')
        if ($bits.Count -lt 3) { return $null }
        $major = 0
        $minor = 0
        [void][int]::TryParse($bits[0], [ref]$major)
        [void][int]::TryParse($bits[1], [ref]$minor)
        if ($major -lt 3) { return $null }
        if ($major -eq 3 -and $minor -lt 10) { return $null }
        return $text
    } catch {
        return $null
    }
}

function Write-Result([string]$text) {
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Out, $text, $utf8)
}

function Show-Error([string]$message) {
    [void][System.Windows.Forms.MessageBox]::Show($message, 'LaTeX2Word', 'OK', 'Warning')
}

# ---------------------------------------------------------------- data

$rows = Read-Candidates $List
$script:chosen = $null
$script:remember = '1'

# ---------------------------------------------------------------- form

$form = New-Object System.Windows.Forms.Form
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true

$font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
$form.Font = $font

$listView = New-Object System.Windows.Forms.ListView
$listView.View = 'Details'
$listView.FullRowSelect = $true
$listView.MultiSelect = $false
$listView.HideSelection = $false
$listView.GridLines = $false
$listView.Location = New-Object System.Drawing.Point(14, 48)
$listView.Size = New-Object System.Drawing.Size(742, 232)
[void]$listView.Columns.Add('版本', 90)
[void]$listView.Columns.Add('位数', 60)
[void]$listView.Columns.Add('来源', 100)
[void]$listView.Columns.Add('路径', 470)

$browseButton = New-Object System.Windows.Forms.Button
$browseButton.Text = '浏览其他 python.exe…'
$browseButton.Location = New-Object System.Drawing.Point(14, 316)
$browseButton.Size = New-Object System.Drawing.Size(170, 30)

$refreshButton = New-Object System.Windows.Forms.Button
$refreshButton.Text = '重新检测'
$refreshButton.Location = New-Object System.Drawing.Point(192, 316)
$refreshButton.Size = New-Object System.Drawing.Size(96, 30)

$okButton = New-Object System.Windows.Forms.Button
$okButton.Text = '使用这个'
$okButton.Location = New-Object System.Drawing.Point(560, 316)
$okButton.Size = New-Object System.Drawing.Size(96, 30)

$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Text = '取消'
$cancelButton.Location = New-Object System.Drawing.Point(664, 316)
$cancelButton.Size = New-Object System.Drawing.Size(92, 30)
$cancelButton.DialogResult = 'Cancel'

function Fill-List {
    param($items)
    $listView.BeginUpdate()
    $listView.Items.Clear()
    $sorted = $items | Sort-Object -Property SortKey -Descending
    foreach ($item in $sorted) {
        $row = New-Object System.Windows.Forms.ListViewItem($item.Version)
        [void]$row.SubItems.Add($item.Bits + ' 位')
        [void]$row.SubItems.Add((Get-SourceLabel $item.Source))
        [void]$row.SubItems.Add($item.Path)
        $row.Tag = $item
        [void]$listView.Items.Add($row)
    }
    if ($listView.Items.Count -gt 0) {
        $listView.Items[0].Selected = $true
        $listView.Items[0].Focused = $true
    }
    $listView.EndUpdate()
}

function Accept-Current {
    if ($listView.SelectedItems.Count -eq 0) {
        Show-Error '请先选择一个解释器。'
        return
    }
    $item = $listView.SelectedItems[0].Tag
    $script:chosen = $item.Path
    $form.DialogResult = 'OK'
    $form.Close()
}

function Invoke-Browse {
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = '选择 python.exe'
    $dialog.Filter = 'python.exe|python.exe|可执行文件 (*.exe)|*.exe'
    $dialog.InitialDirectory = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if ($dialog.ShowDialog() -ne 'OK') { return }
    $exe = $dialog.FileName
    $probe = Test-PythonExe $exe
    if ($null -eq $probe) {
        Show-Error "这个文件不是可用的 Python 3.10+：`r`n$exe`r`n`r`n（需要 64/32 位 CPython 3.10 以上，且自带 venv 模块）"
        return
    }
    $fields = $probe.Split(' ')
    $ver = $fields[0] + '.' + $fields[1] + '.' + $fields[2]
    $item = New-Object psobject
    $item | Add-Member NoteProperty Path $exe
    $item | Add-Member NoteProperty Version $ver
    $item | Add-Member NoteProperty Bits '64'
    $item | Add-Member NoteProperty Source 'browse'
    $item | Add-Member NoteProperty SortKey (Get-SortKey $ver '64')
    $listView.BeginUpdate()
    $row = New-Object System.Windows.Forms.ListViewItem($ver)
    [void]$row.SubItems.Add('64 位')
    [void]$row.SubItems.Add('手动选择')
    [void]$row.SubItems.Add($exe)
    $row.Tag = $item
    [void]$listView.Items.Insert(0, $row)
    $listView.Items[0].Selected = $true
    $listView.Items[0].Focused = $true
    $listView.EndUpdate()
}

function Invoke-Redetect {
    $scriptDir = Split-Path -Parent $PSCommandPath
    $root = Split-Path -Parent $scriptDir
    $cmd = Join-Path $root 'scripts\find-python.cmd'
    if (-not (Test-Path -LiteralPath $cmd)) { return }
    $tmp = Join-Path $env:TEMP ('l2w-redetect-' + [guid]::NewGuid().ToString('N') + '.txt')
    $arguments = '/c ""{0}" --list "{1}""' -f $cmd, $tmp
    try {
        $proc = Start-Process -FilePath $env:ComSpec -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
        if (Test-Path -LiteralPath $tmp) {
            $fresh = Read-Candidates $tmp
            if ($fresh.Count -gt 0) { Fill-List $fresh }
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Show-Error "重新检测失败：$($_.Exception.Message)"
    }
}

# ---------------------------------------------------------------- select mode

if ($Mode -eq 'select' -and $rows.Count -gt 0) {
    $form.Text = '选择 LaTeX2Word 使用的 Python'
    $form.ClientSize = New-Object System.Drawing.Size(770, 360)
    $form.AcceptButton = $okButton

    $label = New-Object System.Windows.Forms.Label
    $label.Text = ('检测到 {0} 个可用的 Python 3.10+ 解释器，请选择要使用的那个：' -f $rows.Count)
    $label.Location = New-Object System.Drawing.Point(14, 16)
    $label.Size = New-Object System.Drawing.Size(742, 24)
    $form.Controls.Add($label)

    $remember = New-Object System.Windows.Forms.CheckBox
    $remember.Text = '记住这次选择（以后不再询问）'
    $remember.Checked = $true
    $remember.Location = New-Object System.Drawing.Point(14, 286)
    $remember.Size = New-Object System.Drawing.Size(300, 24)
    $form.Controls.Add($remember)

    $hint = New-Object System.Windows.Forms.Label
    $hint.Text = '提示：双击列表项可直接使用；按 Esc 取消。'
    $hint.ForeColor = [System.Drawing.Color]::Gray
    $hint.Location = New-Object System.Drawing.Point(330, 288)
    $hint.Size = New-Object System.Drawing.Size(430, 20)
    $hint.TextAlign = 'MiddleRight'
    $form.Controls.Add($hint)

    $form.Controls.Add($listView)
    $form.Controls.Add($browseButton)
    $form.Controls.Add($refreshButton)
    $form.Controls.Add($okButton)
    $form.Controls.Add($cancelButton)

    Fill-List $rows

    $okButton.Add_Click({ Accept-Current })
    $listView.Add_DoubleClick({ Accept-Current })
    $browseButton.Add_Click({ Invoke-Browse })
    $refreshButton.Add_Click({ Invoke-Redetect })
    $remember.Add_CheckedChanged({ if ($remember.Checked) { $script:remember = '1' } else { $script:remember = '0' } })
}
else {
    # ------------------------------------------------------------ missing mode
    $form.Text = '没有找到 Python 3.10 或更高版本'
    $form.ClientSize = New-Object System.Drawing.Size(770, 380)

    $title = New-Object System.Windows.Forms.Label
    $title.Text = '没有找到可用的 Python 3.10+ 解释器，无法启动 LaTeX2Word。'
    $title.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 10, [System.Drawing.FontStyle]::Bold)
    $title.Location = New-Object System.Drawing.Point(14, 14)
    $title.Size = New-Object System.Drawing.Size(742, 26)
    $form.Controls.Add($title)

    $scanned = New-Object System.Windows.Forms.ListView
    $scanned.View = 'Details'
    $scanned.FullRowSelect = $true
    $scanned.MultiSelect = $false
    $scanned.Location = New-Object System.Drawing.Point(14, 46)
    $scanned.Size = New-Object System.Drawing.Size(742, 200)
    [void]$scanned.Columns.Add('版本', 90)
    [void]$scanned.Columns.Add('位数', 60)
    [void]$scanned.Columns.Add('来源', 100)
    [void]$scanned.Columns.Add('路径', 470)
    foreach ($item in ($rows | Sort-Object -Property SortKey -Descending)) {
        $row = New-Object System.Windows.Forms.ListViewItem($item.Version)
        [void]$row.SubItems.Add($item.Bits)
        [void]$row.SubItems.Add((Get-SourceLabel $item.Source))
        [void]$row.SubItems.Add($item.Path)
        [void]$scanned.Items.Add($row)
    }
    if ($scanned.Items.Count -eq 0) {
        $row = New-Object System.Windows.Forms.ListViewItem('—')
        [void]$row.SubItems.Add('—')
        [void]$row.SubItems.Add('所有来源')
        [void]$row.SubItems.Add('未发现任何 Python（py 启动器 / PATH / 注册表 / 常见目录）')
        [void]$scanned.Items.Add($row)
    }
    $form.Controls.Add($scanned)

    $tip = New-Object System.Windows.Forms.Label
    $tip.Text = "解决办法：`r`n  1) 安装 Python 3.10 及以上（安装时勾选 Add python.exe to PATH）`r`n  2) 已经装在别处：点下面的『浏览 python.exe』直接指定`r`n  3) 装完重新双击 start.cmd 即可"
    $tip.Location = New-Object System.Drawing.Point(14, 254)
    $tip.Size = New-Object System.Drawing.Size(742, 66)
    $form.Controls.Add($tip)

    $browse2 = New-Object System.Windows.Forms.Button
    $browse2.Text = '浏览 python.exe…'
    $browse2.Location = New-Object System.Drawing.Point(14, 330)
    $browse2.Size = New-Object System.Drawing.Size(150, 32)

    $download = New-Object System.Windows.Forms.Button
    $download.Text = '打开下载页'
    $download.Location = New-Object System.Drawing.Point(172, 330)
    $download.Size = New-Object System.Drawing.Size(110, 32)

    $copy = New-Object System.Windows.Forms.Button
    $copy.Text = '复制诊断信息'
    $copy.Location = New-Object System.Drawing.Point(290, 330)
    $copy.Size = New-Object System.Drawing.Size(120, 32)

    $quit = New-Object System.Windows.Forms.Button
    $quit.Text = '退出'
    $quit.Location = New-Object System.Drawing.Point(664, 330)
    $quit.Size = New-Object System.Drawing.Size(92, 32)
    $quit.DialogResult = 'Cancel'

    $form.Controls.Add($browse2)
    $form.Controls.Add($download)
    $form.Controls.Add($copy)
    $form.Controls.Add($quit)
    $form.CancelButton = $quit

    $browse2.Add_Click({
        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Title = '选择 python.exe'
        $dialog.Filter = 'python.exe|python.exe|可执行文件 (*.exe)|*.exe'
        if ($dialog.ShowDialog() -ne 'OK') { return }
        $probe = Test-PythonExe $dialog.FileName
        if ($null -eq $probe) {
            Show-Error "这个文件不是可用的 Python 3.10+：`r`n$($dialog.FileName)"
            return
        }
        $script:chosen = $dialog.FileName
        $form.DialogResult = 'OK'
        $form.Close()
    })

    $download.Add_Click({ Start-Process 'https://www.python.org/downloads/' })

    $copy.Add_Click({
        $lines = @()
        foreach ($item in $rows) {
            $lines += ('{0}  {1} 位  {2}  {3}' -f $item.Version, $item.Bits, $item.Source, $item.Path)
        }
        if ($lines.Count -eq 0) { $lines = @('未发现任何 Python 解释器') }
        $text = "LaTeX2Word 环境诊断`r`n扫描结果：`r`n" + ($lines -join "`r`n")
        try {
            Set-Clipboard -Value $text
            Show-Error '诊断信息已复制到剪贴板。'
        } catch {
            Show-Error $text
        }
    })
}

# ---------------------------------------------------------------- capture / show

if ($Capture -ne '') {
    $form.StartPosition = 'Manual'
    $form.Location = New-Object System.Drawing.Point(0, 0)
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 900
    $timer.Add_Tick({
        $timer.Stop()
        try {
            $bounds = New-Object System.Drawing.Rectangle(0, 0, 1300, 700)
            $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
            $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
            $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
            $bitmap.Save($Capture, [System.Drawing.Imaging.ImageFormat]::Png)
            $graphics.Dispose()
            $bitmap.Dispose()
        } catch {
        }
        $form.Close()
    })
    $form.Add_Shown({ $form.Activate(); $timer.Start() })
}

$form.Add_Shown({ $form.Activate() })
$result = $form.ShowDialog()

if ($result -eq 'OK' -and $null -ne $script:chosen) {
    Write-Result ($script:chosen + "`r`n" + 'remember=' + $script:remember)
    exit 0
}

Write-Result 'CANCEL'
exit 1
