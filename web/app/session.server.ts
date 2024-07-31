import { createCookieSessionStorage } from "@remix-run/cloudflare"

type SessionData = { refreshToken: string, accessToken: string }
type SessionFlashData = { error: string }

// NOTE: This must be taken from config file or store
const cookie_secret = "s3cret1"

const { getSession, commitSession, destroySession } = createCookieSessionStorage<SessionData, SessionFlashData>({
  cookie: {
    name: "__session",

    // TODO:
    // domain: ""

    httpOnly: true,
    maxAge: 365 * 24 * 60 * 60,
    path: "/",
    sameSite: "lax",
    secrets: [cookie_secret],
    secure: true,
  }
})

export { getSession, commitSession, destroySession };

