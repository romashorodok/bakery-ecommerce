import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { Link, useLoaderData } from "@remix-run/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import { useAuthFetch } from "~/hooks/useAuthFetch"

import { AspectRatio } from "~/components/ui/aspect-ratio"
import {
  MoreHorizontal,
  PlusCircle,
} from "lucide-react"

import { Button } from "~/components/ui/button"
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

export const loader = async ({ context: { cloudflare } }: LoaderFunctionArgs) => {
  return json({
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
    objectStoreRoute: cloudflare.env.OBJECT_STORE_ROUTE,
  })
}

type Image = { bucket: string, original_file: string, transcoded_file_mime: string, original_file_hash: string, transcoded_file: string, id: string }
type ProductImage = { product_id: string, image_id: string, featured: boolean, id: string, image: Image }
type Product = { id: string, name: string, price: number, product_images: Array<ProductImage> }

function useProductFetcher() {
  const loaderData = useLoaderData<typeof loader>()
  const { fetch, accessToken } = useAuthFetch()

  const products = useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      console.log("run fetch products with", accessToken)

      const { productsRoute = null } = loaderData
      if (!productsRoute) {
        console.log("Not found products route")
        return null
      }

      const response = await fetch(productsRoute)
      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }

      return response.json<{ products: Array<Product> }>()
    }
  })

  return {
    products
  }
}

export default function AdminProducts() {
  const { products } = useProductFetcher()
  const { objectStoreRoute } = useLoaderData<typeof loader>()

  useEffect(() => {
    console.log(products)
  }, [products])

  return (
    <div className={`flex flex-col gap-4`}>
      <div className="flex justify-end">
        <Link to="/admin/products-create" className="sr-only sm:not-sr-only sm:whitespace-nowrap">
          <Button size="sm" className="h-7 gap-1">
            <PlusCircle className="h-3.5 w-3.5" />
            Create Product
          </Button>
        </Link>
      </div>


      {products.isLoading && <h1>Loading...</h1>}

      {products.error && <h1>Error {products.error.message}</h1>}

      {products.data?.products &&
        <Card x-chunk="dashboard-06-chunk-0">
          <CardHeader>
            <CardTitle>Products</CardTitle>
            <CardDescription>
              Manage your products and view their sales performance.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="hidden w-[150px] sm:table-cell">
                    <span className="sr-only">id</span>
                  </TableHead>
                  <TableHead className="hidden w-[150px] sm:table-cell">
                    <span className="sr-only">img</span>
                  </TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.data.products.map(item => {
                  const featuredImage = item.product_images.find(image => image.featured);
                  return (
                    <TableRow key={item.id}>
                      <TableCell className="hidden sm:table-cell">
                        <h1 className="text-xs">{item.id}</h1>
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        <AspectRatio ratio={16 / 9} className="bg-muted">
                          {featuredImage ?
                            <img src={`${objectStoreRoute}/${featuredImage.image.bucket}/${featuredImage?.image.transcoded_file || featuredImage?.image.original_file}`} className="rounded-md object-cover w-full h-full" />
                            : null
                          }
                        </AspectRatio>
                      </TableCell>
                      <TableCell className="sm:table-cell">
                        {item.name}
                      </TableCell>
                      <TableCell className="sm:table-cell">
                        {item.price}
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
                            <Link to={`/admin/products/${item.id}`}>
                              <DropdownMenuItem>
                                Edit
                              </DropdownMenuItem>
                            </Link>
                            <DropdownMenuItem>Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      }
    </div>
  )
}
