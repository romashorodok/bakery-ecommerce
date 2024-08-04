import { useLoaderData, Link } from "@remix-run/react"
import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@chakra-ui/react"
import { useEffect } from "react"

export const loader = async ({ context: { cloudflare } }: LoaderFunctionArgs) => {
  return json({
    catalogsRoute: cloudflare.env.CATALOGS_ROUTE
  })
}

export type Catalog = { headline: string, id: string }

export function useCatalogsFetcher() {
  const loaderData = useLoaderData<typeof loader>()
  const { fetch } = useAuthFetch()

  const model = useQuery({
    queryKey: ['catalogs'],
    queryFn: async () => {
      const { catalogsRoute = null } = loaderData
      if (!catalogsRoute) {
        console.log("Not found catalogs route")
        return null
      }

      const response = await fetch(catalogsRoute)
      if (!response || !response.ok)
        throw new Error('Something goes wrong...')

      return response.json<{ catalogs: Array<Catalog> }>()
    }
  })

  return { model }
}

function Catalog(catalog: Catalog) {
  return <div key={catalog.id}>
    <Link to={`/admin/catalogs/${catalog.id}`}>
      <h1>{catalog.headline}</h1>
      <h1>{catalog.id}</h1>
    </Link>
  </div>
}

export default function AdminCatalogsIndex() {
  const { model } = useCatalogsFetcher()

  useEffect(() => {
    console.log(model)
  }, [model])

  return (
    <div className={`flex flex-col gap-4`}>
      <div>
        <Button variant="ghost" colorScheme="blue">
          <Link to="/admin/catalogs-create">Create Catalog</Link>
        </Button>
      </div>

      {model.isLoading && <h1>Loading...</h1>}

      {model.error && <h1>Error {model.error.message}</h1>}

      <div className="flex flex-col flex-wrap gap-4">
        {model.data?.catalogs && model.data.catalogs.map(Catalog)}
      </div>
    </div>
  )
}
