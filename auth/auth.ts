import { betterAuth } from 'better-auth'
import { Database } from 'bun:sqlite'
import { BunSQLiteDialect } from 'kysely'

export const sqlite = new Database('./auth.db', { create: true })

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL ?? 'http://localhost:3001',
  secret: process.env.BETTER_AUTH_SECRET!,
  database: {
    dialect: new BunSQLiteDialect({ database: sqlite }),
    type: 'sqlite',
  },
  socialProviders: {
    gitlab: {
      clientId: process.env.GITLAB_CLIENT_ID!,
      clientSecret: process.env.GITLAB_CLIENT_SECRET!,
      // For self-hosted GitLab, set GITLAB_URL and uncomment:
      // issuer: process.env.GITLAB_URL ?? 'https://gitlab.com',
    },
  },
})
