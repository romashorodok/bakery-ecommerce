import { LoaderFunctionArgs } from "@remix-run/cloudflare";
import { isRouteErrorResponse, Link, Outlet, useLoaderData, useRouteError } from "@remix-run/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";
import { sessionProtectedLoader } from "~/session.server";

export const loader = async (loader: LoaderFunctionArgs) => sessionProtectedLoader(loader)


const navItems = [
  { label: "Main", to: "/admin" },
  { label: "Products", to: "/admin/products" },
  { label: "Frontpage", to: "/admin/frontpage" },
  { label: "Catalogs", to: "/admin/catalogs" }
];


function Layout({
  children,
}: React.PropsWithChildren<{}>) {
  return (
    <div className="flex h-full">
      <nav>
        {navItems.map(({ label, to }) => {
          return (
            <Link to={to} key={to}>
              <h1>{label}</h1>
            </Link>
          );
        })}
      </nav>
      <section className="w-full overflow-scroll">
        <main className="">
          <section>{children}</section>
        </main>
      </section>
    </div>
  );
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
