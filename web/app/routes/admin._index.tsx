import { isRouteErrorResponse, useRouteError } from "@remix-run/react";
import { LoaderFunctionArgs } from '@remix-run/cloudflare';
import { sessionProtectedLoader } from "~/session.server";
import { useEffect } from "react";


export const loader = async (loader: LoaderFunctionArgs) => {
  const resp = await sessionProtectedLoader(loader)

  return resp
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
  useEffect(() => {
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
