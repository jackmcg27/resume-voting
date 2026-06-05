import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { auth, sqlite } from './auth'

const GITLAB_GROUP = process.env.GITLAB_GROUP!
const GITLAB_BASE = process.env.GITLAB_URL ?? 'https://gitlab.com'

const app = new Hono()

app.use(
  '*',
  cors({
    origin: [process.env.FRONTEND_URL ?? 'http://localhost:5173'],
    credentials: true,
  }),
)

// Better Auth handles all /api/auth/* routes
app.all('/api/auth/*', (c) => auth.handler(c.req.raw))

// FastAPI calls this endpoint to verify admin access.
// It checks both the session validity and GitLab group membership.
app.get('/verify-admin', async (c) => {
  const session = await auth.api.getSession({ headers: c.req.raw.headers })

  if (!session?.user) {
    return c.json({ authorized: false }, 401)
  }

  // Look up the user's GitLab OAuth account to get their access token and GitLab user ID
  const account = sqlite
    .query<{ accountId: string; accessToken: string }, [string, string]>(
      'SELECT accountId, accessToken FROM account WHERE userId = ? AND providerId = ?',
    )
    .get(session.user.id, 'gitlab')

  if (!account?.accessToken) {
    return c.json({ authorized: false, reason: 'no gitlab account linked' }, 403)
  }

  // Verify the user is a member (direct or inherited) of the required GitLab group
  const resp = await fetch(
    `${GITLAB_BASE}/api/v4/groups/${encodeURIComponent(GITLAB_GROUP)}/members/all/${account.accountId}`,
    { headers: { Authorization: `Bearer ${account.accessToken}` } },
  )

  if (!resp.ok) {
    return c.json(
      { authorized: false, reason: resp.status === 404 ? 'not in group' : 'token may be expired — sign out and back in' },
      403,
    )
  }

  return c.json({
    authorized: true,
    user: { name: session.user.name, email: session.user.email },
  })
})

export default {
  port: parseInt(process.env.AUTH_PORT ?? '3001'),
  fetch: app.fetch,
}
