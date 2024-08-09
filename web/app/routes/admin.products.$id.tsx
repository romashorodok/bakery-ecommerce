import { useLoaderData } from "@remix-run/react"
import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { sessionProtectedLoader } from "~/session.server"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { hasDifferentValue, useModel } from "~/hooks/useModel"
import { FormEvent, useEffect, useState } from "react"

export const loader = async (loader: LoaderFunctionArgs) => {
  await sessionProtectedLoader(loader)
  const { params, context: { cloudflare } } = loader

  return json({
    productId: params.id,
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
  })
}

type Product = { id: string, name: string, price: number }

export default function AdminProductsById() {
  const loaderData = useLoaderData<typeof loader>()

  if (!loaderData.productId) {
    return (
      <div>Not found product</div>
    )
  }

  const { fetch } = useAuthFetch()

  const { model, updater } = useModel<Product>({
    id: loaderData.productId,
    key: ["product", { id: loaderData.productId }],
    route: loaderData.productsRoute,
    fetch,
  })

  const [data, setData] = useState<{ product: Product } | null>(null)

  useEffect(() => {
    if (!model.data) return

    (async () => {
      const result = await model.data.json<{ product: Product }>()

      if (data != null && (!hasDifferentValue(data.product, result.product)))
        return

      setData(result)
    })()
  }, [model.data])

  if (model.isLoading) {
    return <div>
      {model.isLoading && <h1>Loading...</h1>}
    </div>
  }

  if (model.error) {
    return <div>
      <h1>Error {model.error.message}</h1>
    </div>
  }

  if (data && data.product) {

    function submit(evt: FormEvent<HTMLFormElement>) {
      evt.preventDefault()

      // @ts-ignore
      const nameField = evt.target["name"].value

      // @ts-ignore
      const priceField = evt.target["price"].value

      if (!data?.product) {
        throw new Error("Original product newer must be null")
      }

      updater.mutate({
        model: data.product,
        mutated: {
          name: nameField,
          price: priceField,
        }
      })

      console.log("Submit")
    }

    return (
      <div>
        <form onSubmit={submit} autoComplete="off">
          <h1>From state: {data.product.name}</h1>

          <h1>Edit product</h1>
          {updater.error &&
            <h1 onClick={() => updater.reset()}>
              {updater.error.message}
            </h1>
          }

          <h1>{data.product.id}</h1>

          <input defaultValue={data.product.name} name="name" />
          <input defaultValue={data.product.price} name="price" type="number" />

          <button type="submit">Update</button>
          <button type="reset">Reset</button>
        </form>
      </div>
    )
  }
}
