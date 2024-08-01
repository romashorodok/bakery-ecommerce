import { ActionFunctionArgs, json } from "@remix-run/server-runtime"
import { commitSession, destroySession, getSession } from "~/session.server"

export const action = async ({ context, request }: ActionFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  const refreshToken = session.get('refreshToken')

  if (!refreshToken) {
    session.unset("refreshToken")
    session.unset("accessToken")

    throw new Response(JSON.stringify({ error: { detail: ["missing refresh token"] } }), {
      headers: {
        "Set-Cookie": await destroySession(session),
      },
    })
  }

  const response = await fetch(context.IDENTITY_SERVER_REFRESH_TOKEN_ROUTE, {
    headers: {
      "authorization": `Bearer ${refreshToken}`
    },
    method: "POST"
  })

  const result = await response.json<{ refresh_token: { value: string, expires_at: number }, access_token: { value: string, expires_at: number } }>()

  session.set('refreshToken', result.refresh_token.value)
  session.set('accessToken', result.access_token.value)

  return json({ access_token: result.access_token.value }, {
    headers: {
      "Set-Cookie": await commitSession(session),
    }
  })
} 
