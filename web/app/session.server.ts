import { createCookieSessionStorage, LoaderFunctionArgs, redirect, json } from "@remix-run/cloudflare"

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

// TODO: Ref this, need more control
const sessionProtectedLoader = async ({ request, context: { cloudflare } }: LoaderFunctionArgs) => {

  const session = await getSession(request.headers.get("Cookie"))
  const refreshToken = session.get("refreshToken")

  if (!refreshToken) {
    return redirect("/", {
      headers: {
        "Set-Cookie": await destroySession(session),
      }
    })
  }

  try {
    const response = await fetch(cloudflare.env.IDENTITY_SERVER_REFRESH_TOKEN_ROUTE, {
      headers: {
        "authorization": `Bearer ${refreshToken}`
      },
      method: "POST"
    })

    const result = await response.json<{ refresh_token: { value: string, expires_at: number }, access_token: { value: string, expires_at: number } }>()

    session.set('refreshToken', result.refresh_token.value)
    session.set('accessToken', result.access_token.value)

    session.set('refreshToken', result.refresh_token.value)
    session.set('accessToken', result.access_token.value)

    return json({ accessToken: result.access_token.value }, {
      headers: {
        "Set-Cookie": await commitSession(session),
      }
    })
  } catch (e) {
    console.log("admin._index.tsx. Error:", e)
    return redirect("/", {
      headers: {
        "Set-Cookie": await destroySession(session),
      }
    })
  }
}

export { getSession, commitSession, destroySession, sessionProtectedLoader };

