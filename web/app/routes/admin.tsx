import { LoaderFunctionArgs } from "@remix-run/cloudflare";
import { isRouteErrorResponse, Link, Outlet, useLoaderData, useLocation, useRouteError } from "@remix-run/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";
import { sessionProtectedLoader } from "~/session.server";

import {
  Package,
  PanelLeft,
  Settings,
  User,
  LayoutTemplateIcon,
  Layers3,
  ListOrdered
} from "lucide-react"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "~/components/ui/breadcrumb"
import { Button } from "~/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "~/components/ui/dropdown-menu"
import { Sheet, SheetContent, SheetTrigger } from "~/components/ui/sheet"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "~/components/ui/tooltip"

export const loader = async (loader: LoaderFunctionArgs) => sessionProtectedLoader(loader)


const navItems = [
  { label: "Main", to: "/admin", Icon: User },
  { label: "Products", to: "/admin/products", Icon: Package },
  { label: "Frontpage", to: "/admin/frontpage", Icon: LayoutTemplateIcon },
  { label: "Catalogs", to: "/admin/catalogs", Icon: Layers3 },
  { label: "Orders", to: "/admin/orders", Icon: ListOrdered }
];


function Layout({
  children,
}: React.PropsWithChildren<{}>) {
  const { pathname } = useLocation()
  const pathSegments = pathname.split('/').filter(segment => segment);

  const breadcrumbs = pathSegments.map((segment, index) => {
    const path = `/${pathSegments.slice(0, index + 1).join('/')}`;
    return {
      name: segment.charAt(0).toUpperCase() + segment.slice(1),
      path
    };
  });

  return (
    <TooltipProvider>
      <div className="relative flex w-full flex-col bg-muted/40">
        <aside className="fixed top-[62px] bottom-[0px] left-0 z-10 hidden w-14 flex-col border-r border-t bg-background sm:flex">
          <nav className="flex flex-col items-center gap-4 px-2 py-4">
            {navItems.map(({ label, to, Icon }) => (
              <Tooltip key={to}>
                <TooltipTrigger asChild key={label}>
                  <Link to={to}
                    className={`flex h-9 w-9 ${pathname == to ? 'items-center justify-center rounded-lg bg-accent text-accent-foreground transition-colors hover:text-foreground md:h-8 md:w-8' : 'items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground md:h-8 md:w-8'}`}>
                    <Icon className="h-5 w-5" />
                    <span className="sr-only">{label}</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">{label}</TooltipContent>
              </Tooltip>
            ))}
          </nav>

          <nav className="mt-auto flex flex-col items-center gap-4 px-2 py-4">
            <Tooltip>
              <TooltipTrigger asChild>
                <Link
                  to="#"
                  className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <Settings className="h-5 w-5" />
                  <span className="sr-only">Settings</span>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right">Settings</TooltipContent>
            </Tooltip>
          </nav>
        </aside>

        <div className="relative flex flex-col sm:gap-4 sm:py-4 sm:pl-16">
          <header className="z-30 w-full flex h-14 items-center gap-4 border-b bg-background px-4 sm:h-auto sm:border-0 sm:bg-transparent sm:px-6">
            <Sheet>
              <SheetTrigger asChild>
                <Button size="icon" variant="outline" className="sm:hidden">
                  <PanelLeft className="h-5 w-5" />
                  <span className="sr-only">Toggle Menu</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="sm:max-w-xs">
                <nav className="grid gap-6 text-lg font-medium">
                  {navItems.map(({ label, to, Icon }) => (
                    <Link to={to}
                      className={`transition-colors hover:text-foreground ${pathname == to ? 'text-foreground' : 'text-muted-foreground'}`}
                    >
                      <span>{label}</span>
                    </Link>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>

            <Breadcrumb className="hidden md:flex">
              <BreadcrumbList>
                {breadcrumbs.map((breadcrumb, index) =>
                  <React.Fragment key={breadcrumb.path}>
                    <BreadcrumbItem>
                      <BreadcrumbLink asChild>
                        <Link to={breadcrumb.path}>{breadcrumb.name}</Link>
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                    {index < breadcrumbs.length - 1 &&
                      <BreadcrumbSeparator />
                    }
                  </React.Fragment>
                )}
              </BreadcrumbList>
            </Breadcrumb>

            <DropdownMenu>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuItem>Support</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Logout</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </header>
          <main>
            {children}
          </main>
        </div>
      </div>
    </TooltipProvider >
  )
}

export type AdminContext = { accessToken: string | null, setAccessToken: React.Dispatch<React.SetStateAction<string | null>> }

export default function AdminLayout() {
  const [queryClient,] = React.useState(() => new QueryClient())
  const loaderData = useLoaderData<typeof loader>()
  const [accessToken, setAccessToken] = React.useState<string | null>(loaderData?.accessToken || null)

  React.useEffect(() => {
    console.log("Admin context", accessToken)
  }, [accessToken])

  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Outlet context={{ accessToken, setAccessToken }} />
      </Layout>
    </QueryClientProvider>
  );
}

export function CatchBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>
          {error.status} {error.statusText}
        </h1>
        <p>{error.data}</p>
      </div>
    );
  } else if (error instanceof Error) {
    return (
      <div>
        <h1>Error</h1>
        <p>{error.message}</p>
        <p>The stack trace is:</p>
        <pre>{error.stack}</pre>
      </div>
    );
  } else {
    return <h1>Unknown Error</h1>;
  }
}

export function ErrorBoundary() {
  return (
    <Layout>
      <p>Layout error boundary</p>
    </Layout>
  );
}
