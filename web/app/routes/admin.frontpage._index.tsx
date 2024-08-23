import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Catalog, useCatalogsFetcher } from "./admin.catalogs._index"
import { Input } from "~/components/ui/input"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import CatalogCard from "~/components/catalog.card"
import { FormEvent, useState, useMemo } from "react"
import * as Popover from '@radix-ui/react-popover';
import { Button } from "~/components/ui/button"
import { CircleX } from "lucide-react"
import { debounce } from "~/lib/debounce"

export const loader = async (loader: LoaderFunctionArgs) => {
  const { context: { cloudflare } } = loader
  return json({
    frontPageRoute: cloudflare.env.FRONT_PAGE_ROUTE,
    catalogsRoute: cloudflare.env.CATALOGS_ROUTE,
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
    objectStoreRoute: cloudflare.env.OBJECT_STORE_ROUTE,
  })
}

type FrontPage = { id: number, catalog_id: string }

type CatalogItem = {
  available: boolean,
  visible: boolean,
  position: number,
  catalog_id: string,
  product_id: string | null,
  id: string
  product: Product | null
}

export function useFrontPage({ frontPageRoute }: { frontPageRoute: string }) {

  const model = useQuery({
    queryKey: ['front-page'],
    queryFn: async () => {
      if (!frontPageRoute) {
        console.log("Not found front page route")
        return null
      }

      const response = await fetch(frontPageRoute)
      if (!response || !response.ok)
        throw new Error('Something goes wrong...')

      return response.json<{ front_page: FrontPage, catalog_items: Array<CatalogItem> }>()
    }
  })

  return { model }
}

function FrontPage(frontPage: FrontPage) {
  // return (
  // <div>
  //   {JSON.stringify(frontPage)}
  // </div>
  // )
  return <></>
}

function CatalogSelect({ id, headline, frontPageRoute, frontPageId }: Catalog & { frontPageId: number, frontPageRoute: string }) {
  const { fetch } = useAuthFetch()
  const client = useQueryClient()

  async function selectAsFrontPage() {
    const response = await fetch(frontPageRoute, {
      method: "PUT",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        catalog_id: id,
        front_page_id: frontPageId,
      })
    })
    if (!response || !response.ok) {
      throw new Error('Something goes wrong...')
    }
    await client.invalidateQueries({ queryKey: ["front-page"] })
  }

  return <div key={id} className="flex items-center gap-2">
    <Button onClick={selectAsFrontPage}>Select</Button>
    <h1>{headline} - {id}</h1>
  </div>
}

function Catalogs({ frontPageId, catalogId }: { catalogId: string, frontPageId: number }) {
  const { model } = useCatalogsFetcher()
  const { frontPageRoute, catalogsRoute } = useLoaderData<typeof loader>()
  const { fetch } = useAuthFetch()
  const client = useQueryClient()

  async function newCatalogItem() {
    const response = await fetch(`${catalogsRoute}/${catalogId}/catalog-item`, {
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
    })
    if (!response || !response.ok) {
      throw new Error('Something goes wrong...')
    }
    await client.invalidateQueries({ queryKey: ["front-page"] })
  }

  return <div className={`flex flex-col gap-4`}>
    {model.isLoading && <h1>Loading...</h1>}

    {model.error && <h1>Error {model.error.message}</h1>}

    <div className="flex flex-col flex-wrap gap-4">
      {model.data?.catalogs &&
        <div>
          <Button onClick={newCatalogItem}>New catalog item</Button>

          {model.data.catalogs.map(catalog =>
            <div key={catalog.id}>
              <CatalogSelect key={catalog.id} frontPageId={frontPageId} frontPageRoute={frontPageRoute}  {...catalog} />
            </div>
          )}
        </div>
      }
    </div>
  </div>
}

type Image = { bucket: string, original_file: string, transcoded_file_mime: string, original_file_hash: string, transcoded_file: string, id: string }
type ProductImage = { product_id: string, image_id: string, featured: boolean, id: string, image: Image }
type Product = { id: string, name: string, price: number, product_images: Array<ProductImage> }

function useModelSelector({ productsRoute, catalogsRoute, catalogId, catalogItemId }: { productsRoute: string, catalogsRoute: string, catalogId: string, catalogItemId: string }) {
  const { fetch } = useAuthFetch()

  // TODO: May be better than my own
  // NOTE: Test it it has bad performance
  // https://ui.shadcn.com/docs/components/combobox
  const Selector = () => {
    const [open, setOpen] = useState<boolean>(false);
    const [product, setProduct] = useState<Product>()
    const [name, setName] = useState<string>("")
    const [error, setError] = useState<string | undefined>(undefined)
    const client = useQueryClient()

    const mutateSelectors = useMutation({
      mutationKey: ["selectors"],
      mutationFn: async (name: string) => {
        const response = await fetch(`${productsRoute}?name=${name}`, {
          headers: {
            "content-type": "application/json",
          }
        })
        if (!response || !response.ok) {
          throw new Error("Request error at model selector candidates")
        }
        return response.json<{ products: Array<Product> }>()
      },
      onSuccess: ({ products }) => {
        if (products.length >= 1) {
          setOpen(true)
        } else {
          setOpen(false)
        }
      }
    })

    const debounceMutate = useMemo(() => debounce((val: string) => mutateSelectors.mutateAsync(val), 300), [])

    const onChange = async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      // @ts-ignore
      const value = e.target.value
      debounceMutate(value)
    }

    const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()

      if (!product) {
        setError("Select product from list")
        return
      }

      const response = await fetch(`${catalogsRoute}/${catalogId}/catalog-item/${catalogItemId}/product`, {
        headers: {
          "content-type": "application/json"
        },
        method: 'PUT',
        body: JSON.stringify({
          product_id: product.id,
        })
      })

      if (!response || !response.ok) {
        setError("Unable change product. Server error")
        return
      }

      await client.invalidateQueries({ queryKey: ["front-page"] })

      console.log("Submit", product)
      setProduct(undefined)
      setName("")
    }

    const selectOnPopUp = (product: Product) => {
      setOpen(false)
      setProduct(product)
      setName(product.name)
      setError(undefined)
    }

    return (
      <Popover.Root open={true}>
        <Popover.Trigger className="pb-4" asChild>
          <div>
            <form method="GET" autoComplete="off" onChange={onChange} onSubmit={onSubmit}>
              <label style={{ visibility: error ? 'visible' : 'hidden' }}>
                Error: {error}
              </label>
              {product &&
                <div className="flex flex-col text-sm">
                  <label>Id: {product.id}</label>
                  <label>Name: {product.name}</label>
                </div>
              }
              <div className="flex flex-col gap-2">
                <div className="relative">
                  <Input name="value" value={name} onChange={(e) => setName(e.target.value)} className="pr-8" placeholder={`Select a new product for the catalog`} />
                  <CircleX className="absolute top-[6px] right-[6px] h-4.5 w-4.5" onClick={() => setOpen(false)} />
                </div>

                <Button type="submit">Change</Button>
              </div>
            </form>
          </div>
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content style={{ visibility: open ? "visible" : "hidden" }}>
            <div className="flex bg-black text-white p-2">
              {mutateSelectors.isPending && <h1>Loading...</h1>}
              {mutateSelectors.data?.products &&
                <div className="flex flex-col">
                  {mutateSelectors.data.products.map(p =>
                    <div key={p.id} onClick={() => selectOnPopUp(p)}>
                      <h1>Name - {p.name}</h1>
                      <h1>Id - {p.id}</h1>
                    </div>
                  )}
                </div>
              }
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    );
  };

  return {
    Selector: () => <Selector />
  };
}

function CatalogItem({ productsRoute, catalogsRoute, objectStoreRoute, ...props }: CatalogItem & { catalogsRoute: string, productsRoute: string, objectStoreRoute: string }) {
  const { fetch } = useAuthFetch()
  const client = useQueryClient()
  const { Selector } = useModelSelector({
    productsRoute: productsRoute,
    catalogsRoute: catalogsRoute,
    catalogId: props.catalog_id,
    catalogItemId: props.id,
  })

  async function deleteItem() {
    const response = await fetch(`${catalogsRoute}/${props.catalog_id}/catalog-item/${props.id}`, {
      method: 'DELETE',
      headers: {
        "content-type": "application/json",
      }
    })

    if (!response || !response.ok) {
      throw new Error('Something goes wrong...')
    }
    await client.invalidateQueries({ queryKey: ["front-page"] })
  }

  return <div key={props.id}>
    <div className="flex flex-col">
      <div className="flex justify-end">
        <Button size="sm" className="h-8 gap-1" onClick={deleteItem}>
          <CircleX className="h-3.5 w-3.5" />
          Delete
        </Button>
      </div>
      <Selector />
    </div>
    <CatalogCard debug={false} objectStoreRoute={objectStoreRoute}  {...props} />
  </div>
}

function FrontPageCatalogItems({ catalog_items, catalogsRoute, productsRoute, objectStoreRoute }: { productsRoute: string, catalogsRoute: string, objectStoreRoute: string, catalog_items: Array<CatalogItem> }) {
  const items = useMemo(() =>
    catalog_items.sort((a, b) => a.position - b.position),
    [catalog_items])

  return (
    <div className="grid grid-cols-2 gap-4">
      {items.map(i => <CatalogItem key={i.id} objectStoreRoute={objectStoreRoute} productsRoute={productsRoute} catalogsRoute={catalogsRoute} {...i} />)}
    </div>
  )
}

export default function AdminFrontpageIndex() {
  const { catalogsRoute, productsRoute, frontPageRoute, objectStoreRoute } = useLoaderData<typeof loader>()
  const { model } = useFrontPage({ frontPageRoute: frontPageRoute })

  return (
    <div className="h-full">
      {model.isLoading && <h1>Loading...</h1>}

      {model.error && <h1>Error {model.error.message}</h1>}

      {model.data?.front_page &&
        <div>
          <FrontPage {...model.data.front_page} />

          {model.data?.catalog_items &&
            <div>
              <FrontPageCatalogItems objectStoreRoute={objectStoreRoute} productsRoute={productsRoute} catalogsRoute={catalogsRoute} catalog_items={model.data.catalog_items} />
            </div>
          }

          <Catalogs catalogId={model.data.front_page.catalog_id} frontPageId={model.data.front_page.id} />
        </div>
      }
    </div>
  )
}
