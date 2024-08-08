import { json, LoaderFunctionArgs, type MetaFunction } from "@remix-run/cloudflare";
import { useLoaderData, useOutletContext } from "@remix-run/react";
import { useCallback } from "react";
import { useAuthFetch } from "~/hooks/useAuthFetch";
import { AppContext } from "~/root";
import CatalogCard from "~/components/catalog.card";

export const meta: MetaFunction = () => {
  return [
    { title: "New Remix App" },
    {
      name: "description",
      content: "Welcome to Remix on Cloudflare Workers!",
    },
  ];
};

type FrontPage = { id: number, catalog_id: string }

type Product = { id: string, name: string }

type CatalogItem = {
  available: boolean,
  visible: boolean,
  position: number,
  catalog_id: string,
  product_id: string | null,
  id: string
  product: Product | null
}

export const loader = async (loader: LoaderFunctionArgs) => {
  const { context: { cloudflare } } = loader

  const response = await fetch(cloudflare.env.FRONT_PAGE_ROUTE)
  if (!response || !response.ok)
    throw new Error('Something goes wrong...')

  const data = await response.json<{
    front_page: FrontPage,
    catalog_items: Array<CatalogItem>
  }>()
  return json({ catalog_items: data.catalog_items.sort((a, b) => a.position - b.position) })
}

export default function Index() {
  const { fetch } = useAuthFetch()
  const { accessToken } = useOutletContext<AppContext>()
  const { catalog_items } = useLoaderData<typeof loader>()

  const tokenInfo = useCallback(async () => {
    const result = await fetch(`http://localhost:9000/api/identity/token-info`, {
      method: "POST",
    })
    if (!result) return
    console.log(await result.json())
  }, [accessToken])

  return (
    <div>
      <section className="grid grid-cols-2 gap-4">
        {catalog_items.map(item => <CatalogCard key={item.id} debug={false} {...item} />)}
      </section>

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
