import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Catalog, useCatalogsFetcher } from "./admin.catalogs._index"
import { Button } from "@chakra-ui/react"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import CatalogCard from "~/components/catalog.card"
import { useEffect, useMemo } from "react"

export const loader = async (loader: LoaderFunctionArgs) => {
  const { context: { cloudflare } } = loader
  return json({
    frontPageRoute: cloudflare.env.FRONT_PAGE_ROUTE,
    catalogsRoute: cloudflare.env.CATALOGS_ROUTE
  })
}

type FrontPage = { id: number, catalog_id: string }

type CatalogItem = {
  available: boolean,
  visible: boolean,
  position: number,
  catalog_id: string,
  id: string
}

function useFrontPage() {
  const loaderData = useLoaderData<typeof loader>()

  const model = useQuery({
    queryKey: ['front-page'],
    queryFn: async () => {
      const { frontPageRoute = null } = loaderData
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

function CatalogItem({ catalogsRoute, ...props }: CatalogItem & { catalogsRoute: string }) {
  const { fetch } = useAuthFetch()
  const client = useQueryClient()

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
    <Button onClick={deleteItem}>Delete</Button>
    <CatalogCard {...props} />
  </div>
}

function FrontPageCatalogItems({ catalog_items, catalogsRoute }: { catalogsRoute: string, catalog_items: Array<CatalogItem> }) {
  const items = useMemo(() =>
    catalog_items.sort((a, b) => a.position - b.position),
    [catalog_items])

  return (
    <div className="grid grid-cols-2 gap-4">
      {items.map(i => <CatalogItem key={i.id} catalogsRoute={catalogsRoute} {...i} />)}
    </div>
  )
}

export default function AdminFrontpageIndex() {
  const { model } = useFrontPage()
  const { catalogsRoute } = useLoaderData<typeof loader>()

  return (
    <div>
      {model.isLoading && <h1>Loading...</h1>}

      {model.error && <h1>Error {model.error.message}</h1>}

      <div className="flex flex-col flex-wrap gap-4">
        {model.data?.front_page &&
          <div>
            <FrontPage {...model.data.front_page} />

            {model.data?.catalog_items &&
              <div>
                <FrontPageCatalogItems catalogsRoute={catalogsRoute} catalog_items={model.data.catalog_items} />
              </div>
            }

            <Catalogs catalogId={model.data.front_page.catalog_id} frontPageId={model.data.front_page.id} />
          </div>
        }
      </div>
    </div>
  )
}
