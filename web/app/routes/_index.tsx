import { json, LoaderFunctionArgs, type MetaFunction } from "@remix-run/cloudflare";
import { useLoaderData, useOutletContext } from "@remix-run/react";
import { useCallback, useEffect } from "react";
import { useAuthFetch } from "~/hooks/useAuthFetch";
import { AppContext } from "~/root";

export const meta: MetaFunction = () => {
  return [
    { title: "New Remix App" },
    {
      name: "description",
      content: "Welcome to Remix on Cloudflare Workers!",
    },
  ];
};

export const loader = async ({ context }: LoaderFunctionArgs) => {
  console.log(context)
  return json({ test: "test" })
}

export default function Index() {
  const loaderData = useLoaderData<typeof loader>()
  const { fetch } = useAuthFetch()
  const { accessToken } = useOutletContext<AppContext>()

  const tokenInfo = useCallback(async () => {
    const result = await fetch(`http://localhost:9000/api/identity/token-info`, {
      method: "POST",
    })
    if (!result) return
    console.log(await result.json())
  }, [accessToken])

  return (
    <div>
      <button onClick={() => tokenInfo()}>Verify</button>

      <h1 className="text-3xl">Welcome to Remix on Cloudflare Workers</h1>
      <ul className="list-disc mt-4 pl-6 space-y-2">
        <li>
          <a
            className="text-blue-700 underline visited:text-purple-900"
            target="_blank"
            href="https://remix.run/docs"
            rel="noreferrer"
          >
            Remix Docs
          </a>
        </li>
        <li>
          <a
            className="text-blue-700 underline visited:text-purple-900"
            target="_blank"
            href="https://developers.cloudflare.com/workers/"
            rel="noreferrer"
          >
            Cloudflare Workers Docs
          </a>
        </li>
      </ul>
    </div>
  );
}
