import {
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useFetcher,
  useLoaderData,
} from "@remix-run/react";
import "./tailwind.css";
import { ActionFunctionArgs, LoaderFunctionArgs, redirect } from "@remix-run/server-runtime";
import { destroySession, getSession } from "./session.server";
import { createContext, Dispatch, PropsWithChildren, SetStateAction, useContext, useEffect, useState } from "react";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))

  return { accessToken: session.get("accessToken") }
}

export const action = async ({ request }: ActionFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  session.unset('refreshToken')

  return redirect("/", {
    headers: {
      "Set-Cookie": await destroySession(session),
    },
  })
}

export const AccessTokenContext = createContext<{
  accessToken?: string,
  setAccessToken: Dispatch<SetStateAction<string | undefined>>
}>({
  setAccessToken: () => null,
})

function AccessTokenProvider({ children }: PropsWithChildren) {
  const { accessToken: _accessToken } = useLoaderData<typeof loader>()
  const [accessToken, setAccessToken] = useState<string | undefined>(_accessToken)

  useEffect(() => {
    console.log("change access token", accessToken)
  }, [accessToken])

  return <AccessTokenContext.Provider value={{ accessToken, setAccessToken }}>
    {children}
  </AccessTokenContext.Provider>
}

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <AccessTokenProvider>
          {children}
          <ScrollRestoration />
          <Scripts />
        </AccessTokenProvider >
      </body>
    </html>
  );
}

export default function App() {
  const fetcher = useFetcher()
  const { accessToken, setAccessToken } = useContext(AccessTokenContext)

  useEffect(() => {
    console.log(accessToken)
  }, [accessToken])

  return <main>
    <nav>
      <ul className={"flex gap-4"}>
        <li>
          <Link to={"/"}>Home</Link>
        </li>
        <li style={{ visibility: accessToken ? 'visible' : 'hidden', position: accessToken ? 'inherit' : 'absolute' }} >
          <fetcher.Form method="POST">
            <button type="submit" onClick={() => setAccessToken(undefined)}>Log Out</button>
          </fetcher.Form>
        </li>

        {!accessToken && <li> <Link to={"/login"}>Log In</Link> </li>}
      </ul>
    </nav>
    <section className={"font-sans p-4"}>
      <Outlet context={{ setAccessToken }} />
    </section>
  </main >
}
