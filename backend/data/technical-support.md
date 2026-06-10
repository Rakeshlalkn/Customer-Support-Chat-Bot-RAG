# Technical Support

## Common issues

### The app won't load
- Hard-refresh the page (Ctrl/Cmd + Shift + R) to bypass cached resources.
- Try a different browser to isolate the issue.
- Disable browser extensions, especially ad blockers and privacy tools.

### Login keeps failing
- Make sure Caps Lock is off — passwords are case-sensitive.
- Try the **Forgot password** flow.
- If you use SSO (Google/Microsoft), sign in with that provider rather than a password.

### Performance is slow
- Large workspaces (10k+ items) can be slow on older machines. Try filtering to a smaller view.
- Check status.example-status.com for any ongoing incidents.

### API errors (for developers)
| Code | Meaning            | What to do |
|------|--------------------|------------|
| 401  | Invalid/missing key | Rotate your API key from the dashboard. |
| 429  | Rate limit hit      | Back off and respect the `Retry-After` header. |
| 500  | Server error        | Retry with exponential backoff; contact us if persistent. |

## Contacting human support
- **Free plan**: Community forum, response in 2–3 days.
- **Pro plan**: Email support, response in 24 hours on business days.
- **Team plan**: Priority email + dedicated Slack channel, response in 4 hours.
