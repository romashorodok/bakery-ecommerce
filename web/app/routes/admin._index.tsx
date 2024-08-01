import { isRouteErrorResponse, useRouteError } from "@remix-run/react";
import { LoaderFunctionArgs, redirect } from '@remix-run/cloudflare';
import * as React from "react";
import { getSession, destroySession } from "~/session.server";


export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  const refreshToken = session.get("refreshToken")

  console.log("Admin index trigger")

  if (!refreshToken) {
    return redirect("/", {
      headers: {
        "Set-Cookie": await destroySession(session),
      }
    })
  }

  return {}
};


export default function AdminIndex() {
  return (
    <>
      <div>
        <div>
          <p>Here's what you missed while you were away.</p>
        </div>
      </div>
      <section>
        <div>Content</div>
      </section>
    </>
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


export function ErrorBoundary({ error }: { error: Error }) {
  React.useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div>
      <div>
        <h1>PM Camp</h1>
        <div>Crap</div>
      </div>
    </div>
  );
}
