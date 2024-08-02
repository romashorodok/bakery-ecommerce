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
import { createContext, Dispatch, PropsWithChildren, SetStateAction, useContext, useEffect, useState } from "react";
import { ChakraProvider } from '@chakra-ui/react'


export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  return { accessToken: session.get("accessToken") }
}

export const AccessTokenContext = createContext<{
  accessToken?: string,
  setAccessToken: Dispatch<SetStateAction<string | undefined>>
}>({
  accessToken: undefined,
  setAccessToken: () => null,
})

export function AccessTokenProvider({ children }: PropsWithChildren) {
  const loaderData = useLoaderData<typeof loader>()
  const [accessToken, setAccessToken] = useState<string | undefined>(loaderData?.accessToken || undefined)

  useEffect(() => {
    console.log("context provider loader", loaderData)
  }, [loaderData])

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
          <ChakraProvider>
            {children}
          </ChakraProvider>
          <ScrollRestoration />
          <Scripts />
        </AccessTokenProvider >
      </body>
    </html>
  );
}

const navItems = [
  { label: "Home", to: "/" },
  { label: "Admin", to: "/admin" },
];

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

  return <main className="h-screen flex flex-col">
    <nav className="">
      <ul className={"flex gap-4"}>
        {navItems.map(({ label, to }) => {
          return (
            <Link to={to} key={to}>
              <h1>{label}</h1>
            </Link>
          );
        })}

        {accessToken &&
          <li>
            <button type="button" onClick={() => logout()}>Log Out</button>
          </li>
        }
        {!accessToken && <li> <Link to={"/login"}>Log In</Link> </li>}
      </ul>
    </nav>
    <section className={"font-sans max-h-full overflow-scroll"}>
      <Outlet context={{ setAccessToken, accessToken }} />
    </section>
  </main >
}
