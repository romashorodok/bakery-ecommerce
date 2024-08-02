import { LoaderFunctionArgs, redirect, json } from "@remix-run/cloudflare";
import { isRouteErrorResponse, Outlet, useRouteError } from "@remix-run/react";
import * as React from "react";
import { destroySession, getSession, commitSession } from "~/session.server";

export const loader = async ({ request, context }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  const refreshToken = session.get("refreshToken")

  console.log("Admin layout trigger")

  if (!refreshToken) {
    return redirect("/", {
      headers: {
        "Set-Cookie": await destroySession(session),
      }
    })
  }

  try {
    const response = await fetch(context.IDENTITY_SERVER_REFRESH_TOKEN_ROUTE, {
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
};

function Layout({
  children,
}: React.PropsWithChildren<{}>) {
  return (
    <div>
      <header>
        <nav>
        </nav>
      </header>

      <main className="dashboard-layout__main">
        <section>{children}</section>
      </main>

      <footer className="dashboard-layout__footer">
        <div className="dashboard-layout__copyright">
          &copy; 2024 Remix Software
        </div>
      </footer>
    </div>
  );
}

export default function AdminLayout() {
  return (
    <Layout>
      <Outlet />
    </Layout>
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
