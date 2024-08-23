import { json, LoaderFunctionArgs, type MetaFunction } from "@remix-run/cloudflare";
import { useLoaderData, useOutletContext } from "@remix-run/react";
import { createRef, useCallback } from "react";
import { useAuthFetch } from "~/hooks/useAuthFetch";
import { AppContext } from "~/root";
import CatalogCard from "~/components/catalog.card";
import { useSize } from "~/lib/resize";
import { cn } from "~/lib/utils";
import { Button } from "~/components/ui/button";
import { ShoppingBag } from "lucide-react"
import { useAddToCart } from "~/hooks/useCart";

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

type Image = { bucket: string, original_file: string, transcoded_file_mime: string, original_file_hash: string, transcoded_file: string, id: string }
type ProductImage = { product_id: string, image_id: string, featured: boolean, id: string, image: Image }
type Product = { id: string, name: string, price: number, product_images: Array<ProductImage> }

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
  if (!response || !response.ok) {
    throw new Error('Something goes wrong...')
  }

  const data = await response.json<{
    front_page: FrontPage,
    catalog_items: Array<CatalogItem>
  }>()

  return json({
    catalog_items: data.catalog_items.sort((a, b) => a.position - b.position),
    cartRoute: cloudflare.env.CART_ROUTE,
    objectStoreRoute: cloudflare.env.OBJECT_STORE_ROUTE,
  })
}

export default function Index() {
  const { catalog_items, cartRoute, objectStoreRoute } = useLoaderData<typeof loader>()
  const { addToCartMutation } = useAddToCart({ cartRoute })
  const { fetch } = useAuthFetch()
  const { accessToken } = useOutletContext<AppContext>()

  const rootDivRef = createRef<HTMLDivElement>()
  const { width } = useSize(rootDivRef)

  const tokenInfo = useCallback(async () => {
    const result = await fetch(`http://localhost:9000/api/identity/token-info`, {
      method: "POST",
    })
    if (!result) return
    console.log(await result.json())
  }, [accessToken])

  const addToCart = (productId: string | null) => {
    if (!productId) {
      throw new Error("Unable add product to cart. Not found productId")
    }

    addToCartMutation.mutateAsync({
      quantity: 1,
      productId,
    })
  }

  return (
    <div ref={rootDivRef}>
      <section className={cn(
        "grid gap-4",
        `${width >= 667 ? 'grid-cols-2' : 'grid-cols-1'}`
      )}>
        {catalog_items.map(item =>
          <CatalogCard key={item.id} objectStoreRoute={objectStoreRoute} debug={false} {...item}>
            <Button size="sm" className="top-[5px] right-[10px] h-7 gap-1" onClick={() => addToCart(item.product_id)} >
              <ShoppingBag className="h-3.5 w-3.5" />
              Buy
            </Button>
          </CatalogCard>
        )}
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
    </div >
  );
}
