import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { useMutation, useQueries, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { Catalog, useCatalogsFetcher } from "./admin.catalogs._index"
import { Button, Input } from "@chakra-ui/react"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import CatalogCard from "~/components/catalog.card"
import { FormEvent, useEffect, useMemo, useState } from "react"
import * as Popover from '@radix-ui/react-popover';

export const loader = async (loader: LoaderFunctionArgs) => {
  const { context: { cloudflare } } = loader
  return json({
    frontPageRoute: cloudflare.env.FRONT_PAGE_ROUTE,
    catalogsRoute: cloudflare.env.CATALOGS_ROUTE,
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
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
  return (
    <div>
      {JSON.stringify(frontPage)}
    </div>
  )
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

type Product = { id: string, name: string }

function useModelSelector({ productsRoute, catalogsRoute, catalogId, catalogItemId }: { productsRoute: string, catalogsRoute: string, catalogId: string, catalogItemId: string }) {
  const { fetch } = useAuthFetch()

  // TODO: May be better than my own
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

    const onChange = async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      // @ts-ignore
      const value = e.target.value
      mutateSelectors.mutateAsync(value)
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
        <Popover.Trigger asChild>
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
              <Input name="value" value={name} onChange={(e) => setName(e.target.value)} />
              <Button type="submit">Change</Button>
              <Button onClick={() => setOpen(false)}>Close</Button>
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

function CatalogItem({ productsRoute, catalogsRoute, ...props }: CatalogItem & { catalogsRoute: string, productsRoute: string }) {
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
    <div className="flex gap-4">
      <Button onClick={deleteItem}>Delete</Button>
      <Selector />
    </div>
    <CatalogCard debug={true}  {...props} />
  </div>
}

function FrontPageCatalogItems({ catalog_items, catalogsRoute, productsRoute }: { productsRoute: string, catalogsRoute: string, catalog_items: Array<CatalogItem> }) {
  const items = useMemo(() =>
    catalog_items.sort((a, b) => a.position - b.position),
    [catalog_items])

  return (
    <div className="grid grid-cols-2 gap-4">
      {items.map(i => <CatalogItem key={i.id} productsRoute={productsRoute} catalogsRoute={catalogsRoute} {...i} />)}
    </div>
  )
}

export default function AdminFrontpageIndex() {
  const { catalogsRoute, productsRoute, frontPageRoute } = useLoaderData<typeof loader>()
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
              <FrontPageCatalogItems productsRoute={productsRoute} catalogsRoute={catalogsRoute} catalog_items={model.data.catalog_items} />
            </div>
          }

          <Catalogs catalogId={model.data.front_page.catalog_id} frontPageId={model.data.front_page.id} />
        </div>
      }
    </div>
  )
}
