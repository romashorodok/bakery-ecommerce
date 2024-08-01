import {
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
  useNavigate,
} from "@remix-run/react";
import "./tailwind.css";
import { LoaderFunctionArgs } from "@remix-run/server-runtime";
import { getSession } from "./session.server";
import { createContext, Dispatch, PropsWithChildren, SetStateAction, useContext, useState } from "react";

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))

  return { accessToken: session.get("accessToken") }
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

export type AppContext = {
  accessToken: string | undefined,
  setAccessToken: Dispatch<SetStateAction<string | undefined>>
}

export default function App() {
  const { accessToken, setAccessToken } = useContext(AccessTokenContext)
  const navigate = useNavigate()

  async function logout() {
    await fetch("/session_delete", {
      method: "DELETE",
    }).catch(e => console.error(e))
    setAccessToken(undefined)
    navigate("/")
  }

  return <main>
    <nav>
      <ul className={"flex gap-4"}>
        <li>
          <Link to={"/"}>Home</Link>
        </li>
        {accessToken &&
          <li>
            <button type="button" onClick={() => logout()}>Log Out</button>
          </li>
        }
        {!accessToken && <li> <Link to={"/login"}>Log In</Link> </li>}
      </ul>
    </nav>
    <section className={"font-sans p-4"}>
      <Outlet context={{ setAccessToken, accessToken }} />
    </section>
  </main >
}
