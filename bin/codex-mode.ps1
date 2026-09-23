param(
  [Parameter(Position=0, Mandatory=$true)]
  [ValidateSet("on","off","fast")]
  [string]$Mode,
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$CodexArgs
)

$Profile = switch ($Mode) {
  "on"   { "sol-luna" }
  "off"  { "sol-only" }
  "fast" { "sol-luna-fast" }
}

& codex --profile $Profile @CodexArgs
exit $LASTEXITCODE
