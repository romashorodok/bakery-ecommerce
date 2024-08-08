import {
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
  useLocation,
  useNavigate,
} from "@remix-run/react";
import "./tailwind.css";
import { LoaderFunctionArgs } from "@remix-run/server-runtime";
import { getSession } from "./session.server";
import { createContext, Dispatch, PropsWithChildren, SetStateAction, useContext, useEffect, useState } from "react";
import { ChakraProvider } from '@chakra-ui/react'

import {
  Package2,
  Search,
  CircleUser,
  LogIn,
  Menu,
} from "lucide-react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"

import { Sheet, SheetContent, SheetTrigger } from "~/components/ui/sheet"
import { Input } from "~/components/ui/input"
import { Button } from "~/components/ui/button"

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
  const { pathname } = useLocation()
  const pathSegments = pathname.split('/').filter(segment => segment);

  async function logout() {
    await fetch("/session_delete", {
      method: "DELETE",
    }).catch(e => console.error(e))
    setAccessToken(undefined)
    navigate("/")
  }

  useEffect(() => {
    console.log(pathSegments)
  }, [])

  return <main className="flex min-h-screen w-full flex-col">
    <header className="z-50 sticky top-0 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
      <nav className="hidden flex-col gap-6 text-lg font-medium md:flex md:flex-row md:items-center md:gap-5 md:text-sm lg:gap-6">
        {navItems.map(({ label, to }) => (
          <Link to={to} key={to}
            className={`transition-colors hover:text-foreground ${`/${pathSegments[0]}` == to || (pathSegments.length == 0 && to == '/') ? 'text-foreground' : 'text-muted-foreground'}`}
          >
            <span>{label}</span>
          </Link>
        ))}

      </nav>
      <Sheet>
        <SheetTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className="shrink-0 md:hidden"
          >
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle navigation menu</span>
          </Button>
        </SheetTrigger>

        <SheetContent side="left">
          <nav className="grid gap-6 text-lg font-medium">
            <Link
              to="#"
              className="flex items-center gap-2 text-lg font-semibold"
            >
              <Package2 className="h-6 w-6" />
              <span className="sr-only">Acme Inc</span>
            </Link>

            {navItems.map(({ label, to }) => (
              <Link to={to} key={to}
                className={`transition-colors hover:text-foreground ${`/${pathSegments[0]}` == to || (pathSegments.length == 0 && to == '/') ? 'text-foreground' : 'text-muted-foreground'}`}
              >
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        </SheetContent>

      </Sheet>
      <div className="flex w-full items-center gap-4 md:ml-auto md:gap-2 lg:gap-4">
        <form className="ml-auto flex-1 sm:flex-initial">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search products..."
              className="pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
            />
          </div>
        </form>
        {accessToken
          ? <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="icon" className="rounded-full">
                <CircleUser className="h-5 w-5" />
                <span className="sr-only">Toggle user menu</span>
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuItem>Support</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => logout()}>Logout</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          : (
            <Link to={"/login"}>
              <Button size="sm" className="h-7 gap-1">
                <LogIn className="h-3.5 w-3.5" />
                <span className="sr-only sm:not-sr-only sm:whitespace-nowrap">
                  Log In
                </span>
              </Button>
            </Link>
          )
        }
      </div>
    </header>
    <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 bg-muted/40 overflow-scroll">
      <Outlet context={{ setAccessToken, accessToken }} />
    </main>
  </main >
}
