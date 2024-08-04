import { Button } from "@chakra-ui/react"
import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { Link, useLoaderData } from "@remix-run/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import ProductCard from "~/components/product.card"
import { useAuthFetch } from "~/hooks/useAuthFetch"


export const loader = async ({ context: { cloudflare } }: LoaderFunctionArgs) => {
  return json({
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
  })
}

type Product = { id: string, name: string }

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

function Product(product: Product) {
  return <div key={product.id} className={"relative"}>
    <ProductCard {...product} />
    <Link to={`/admin/products/${product.id}`}>
      <Button variant="ghost" colorScheme="blue" className={`!absolute !bg-white top-[10px] right-[10px]`}>
        Edit
      </Button>
    </Link>
  </div>
}

export default function AdminProducts() {
  const { products } = useProductFetcher()

  useEffect(() => {
    console.log(products)
  }, [products])

  return (
    <div className={`flex flex-col gap-4`}>
      <div>
        <Button variant="ghost" colorScheme="blue">
          <Link to="/admin/products-create">Create Product</Link>
        </Button>
      </div>


      {products.isLoading && <h1>Loading...</h1>}

      {products.error && <h1>Error {products.error.message}</h1>}

      <div className="flex flex-wrap gap-4">
        {products.data?.products && products.data.products.map(Product)}
      </div>
    </div>
  )
}
