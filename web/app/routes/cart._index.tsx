import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { useQuery } from "@tanstack/react-query"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { sessionProtectedLoader } from "~/session.server"

export const loader = async (loader: LoaderFunctionArgs) => {
  await sessionProtectedLoader(loader)
  const { CART_ROUTE } = loader.context.cloudflare.env

  return json({
    cartsRoute: CART_ROUTE,
  })
}

type Cart = {}

export default function CartIndex() {
  const { fetch } = useAuthFetch()
  const { cartsRoute } = useLoaderData<typeof loader>()

  const model = useQuery({
    queryKey: ["cart"],
    queryFn: async () => {
      const response = await fetch(cartsRoute, {
        method: "GET",
      })

      if (!response || !response.ok) {
        throw new Error("Cart request error")
      }

      return response.json<{ cart: Cart }>()
    }
  })

  return (
    <div>
      {model.isLoading && <h1>Loading...</h1>}

      {model.error && <h1>Error {model.error.message}</h1>}

      {model.data &&
        <div>
          {JSON.stringify(model.data)}
        </div>
      }
    </div>
  )
}
