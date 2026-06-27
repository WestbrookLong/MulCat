# Placeholder example. Save a profile in MulCat to generate a real script.
$ErrorActionPreference = 'Stop'
Set-Location 'D:\AIWorkspace'

$env:ANTHROPIC_BASE_URL = 'https://example.com/anthropic'
$env:ANTHROPIC_AUTH_TOKEN = 'YOUR_ANTHROPIC_TOKEN_HERE'
$env:ANTHROPIC_MODEL = 'sonnet'

claude '--dangerously-skip-permissions'
