/**
 * By default, Remix will handle generating the HTTP Response for you.
 * You are free to delete this file if you'd like to, but if you ever want it revealed again, you can run `npx remix reveal` ✨
 * For more information, see https://remix.run/file-conventions/entry.server
 */

import type { AppLoadContext, EntryContext, Session } from "@remix-run/cloudflare";
import { RemixServer } from "@remix-run/react";
import { isbot } from "isbot";
import { renderToReadableStream } from "react-dom/server";
import { commitSession, getSession } from "./session.server";

async function handleProtectedRequest(request: Request, { cloudflare }: AppLoadContext) {
  const session = await getSession(request.headers.get("Cookie"))

  const refreshToken = session.get('refreshToken')
  if (!refreshToken) {
    throw Error("Unauthorized user access protected route")
  }

  const response = await fetch(cloudflare.env.IDENTITY_SERVER_REFRESH_TOKEN_ROUTE, {
    headers: {
      "authorization": `Bearer ${refreshToken}`
    },
    method: "POST"
  })

  const result = await response.json<{
    refresh_token: { value: string, expires_at: number },
    access_token: { value: string, expires_at: number },
  }>()

  session.set('refreshToken', result.refresh_token.value)
  session.set('accessToken', result.access_token.value)

  return session
}

const protectedRoutes: Array<string> = [
  'admin'
]

export default async function handleRequest(
  request: Request,
  responseStatusCode: number,
  responseHeaders: Headers,
  remixContext: EntryContext,
  // This is ignored so we can keep it in the template for visibility.  Feel
  // free to delete this parameter in your app if you're not using it!
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  loadContext: AppLoadContext
) {
  const urlPath = (new URL(request.url)).pathname
  const routes = urlPath.split("/")

  let session: Session | undefined

  const isProtectedRoute = protectedRoutes.some(protectedRoute => routes.includes(protectedRoute, 0));
  try {
    if (isProtectedRoute) {
      console.log("protected route")
      session = await handleProtectedRequest(request, loadContext)
    }
  } catch (e) {
    if (e instanceof Error) {
      console.log(e)
      return new Response(JSON.stringify({
        message: { detail: [e.message] }
      }), { status: 401 })
    }
    return
  }

  const body = await renderToReadableStream(
    <RemixServer context={remixContext} url={request.url} />,
    {
      signal: request.signal,
      onError(error: unknown) {
        // Log streaming rendering errors from inside the shell
        console.error(error);
        responseStatusCode = 500;
      },
    }
  );

  if (isbot(request.headers.get("user-agent") || "")) {
    await body.allReady;
  }


  responseHeaders.set("Content-Type", "text/html");

  if (session) {
    responseHeaders.set("Set-Cookie", await commitSession(session))
  }

  return new Response(body, {
    headers: responseHeaders,
    status: responseStatusCode,
  });
}
