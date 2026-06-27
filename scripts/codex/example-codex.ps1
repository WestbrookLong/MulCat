# Placeholder example. Save a profile in MulCat to generate a real script.
$ErrorActionPreference = 'Stop'
Set-Location 'D:\AIWorkspace'

$env:CUSTOM_API_KEY = 'YOUR_CUSTOM_API_KEY_HERE'

codex `
  '--ignore-user-config' `
  '-c' `
  'model_provider="custom"' `
  '-c' `
  'model="gpt-5"' `
  '-c' `
  'model_providers.custom.base_url="https://example.com"' `
  '-c' `
  'model_providers.custom.env_key="CUSTOM_API_KEY"'
