param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("on","off","fast")]
  [string]$Mode,
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$CodexArgs
)

if ($Mode -eq "on" -or $Mode -eq "off") {
  $Installer = Join-Path $PSScriptRoot "install.py"
  & python $Installer $Mode
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  & codex @CodexArgs
} else {
  # Fast is an explicit whole-session Advanced profile.
  & codex --profile sol-luna-fast @CodexArgs
}
exit $LASTEXITCODE
