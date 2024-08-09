import { useLoaderData, Link } from "@remix-run/react"
import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"

import {
  MoreHorizontal,
} from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import { Button } from "~/components/ui/button"

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
        <Button size="sm" className="h-7 gap-1">
          <Link to="/admin/catalogs-create">Create Catalog</Link>
        </Button>
      </div>

      {model.isLoading && <h1>Loading...</h1>}

      {model.error && <h1>Error {model.error.message}</h1>}

      {model.data?.catalogs &&
        <Card x-chunk="dashboard-06-chunk-0 ">
          <CardHeader>
            <CardTitle>Catalogs</CardTitle>
            <CardDescription>
              Manage your catalogs.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="hidden w-[150px] sm:table-cell">
                    <span className="sr-only">id</span>
                  </TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {model.data.catalogs.map(item => (
                  <TableRow key={item.id}>
                    <TableCell className="hidden sm:table-cell">
                      <h1 className="text-xs">{item.id}</h1>
                    </TableCell>
                    <TableCell className="sm:table-cell">
                      {item.headline}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            aria-haspopup="true"
                            size="icon"
                            variant="ghost"
                          >
                            <MoreHorizontal className="h-4 w-4" />
                            <span className="sr-only">Toggle menu</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <Link to={`/admin/catalogs/${item.id}`}>
                            <DropdownMenuItem>
                              Edit
                            </DropdownMenuItem>
                          </Link>
                          <DropdownMenuItem>Delete</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      }
    </div>
  )
}
