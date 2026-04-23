# Security

## Secrets handling

- Do not commit API keys, tokens, or PATs.
- Use environment variables or local credential managers.
- Keep `.env` files out of Git.

## Recommended practice

- `FRED_API_KEY`, `ALPHAVANTAGE_API_KEY`, `ZYLA_METALS_API_KEY`, `TUSHARE_TOKEN`, and GitHub PATs should exist only in local runtime configuration.
- Generated documentation should never print raw secrets.
- Any token that was pasted into chat or another shared surface should be rotated before production use.

## GitHub authentication

For the eventual GitHub push step:

- prefer `gh auth login` or a local environment variable
- avoid embedding PATs in remotes or scripts
- rotate any token that has been exposed or pasted into insecure locations

## Data provenance

- tariff monitoring should favor official sources such as Federal Register and USTR
- commodity data should clearly identify which provider produced each result
- scenario outputs should preserve assumptions and provider transparency
