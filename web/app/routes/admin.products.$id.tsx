import { useLoaderData } from "@remix-run/react"
import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { sessionProtectedLoader } from "~/session.server"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { Update } from "vite"
import { FormEvent, useEffect, useState } from "react"


export const loader = async (loader: LoaderFunctionArgs) => {
  await sessionProtectedLoader(loader)
  const { params, context: { cloudflare } } = loader

  return json({
    productId: params.id,
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
  })
}

type Product = { id: string, name: string }

type PartialProduct = Partial<Product>

function useProductEdit(productId: string) {
  const { fetch, accessToken } = useAuthFetch()
  const loaderData = useLoaderData<typeof loader>()
  const queryClient = useQueryClient()

  if (!loaderData.productsRoute) {
    throw Error("Not found product route")
  }

  const product = useQuery({
    queryKey: ['product', productId],
    queryFn: async () => {
      console.log("fetch product with", accessToken)
      console.log(['product', productId])

      const response = await fetch(`${loaderData.productsRoute}/${productId}`)

      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }

      return response.json<{ product: Product }>()
    },
  })

  const productUpdater = useMutation({
    mutationFn: async ({ original, patched }: { patched: PartialProduct, original: Product }) => {
      const atLeastOneField = Object.keys(patched).length >= 1
      if (!atLeastOneField) {
        throw new Error("Require at least one field to update")
      }

      const hasUpdatedField = Object.keys(patched).some((key) => {
        return original[key as keyof Product] !== patched[key as keyof PartialProduct];
      });

      if (!hasUpdatedField) {
        throw new Error("Require at least one updated field")
      }

      console.log("Run mutation")

      return fetch(`${loaderData.productsRoute}/${productId}`, {
        method: "PATCH",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify(patched)
      })
    },

    onError: (err) => {
      console.log("Mutation error", err)
    },

    async onSuccess(data, _variables, _context) {
      const result = await data?.json<{ product: Product }>()
      if (!result?.product) throw new Error("Product mutation must return mutated object")

      console.log("Is this success???")

      await queryClient.invalidateQueries({ queryKey: ["product", result.product.id] })
      console.log("mutation", ["product", result.product.id])

      return await queryClient.setQueryData(['product', result.product.id], {
        product: result.product
      })
    },
  })

  return { product, productUpdater }
}

export default function AdminProductsById() {
  const loaderData = useLoaderData<typeof loader>()

  if (!loaderData.productId) {
    return (
      <div>Not found product</div>
    )
  }

  const { product, productUpdater } = useProductEdit(loaderData.productId)

  useEffect(() => {
    console.log("Product changed", product.data)
  }, [product.data])

  if (product.isLoading) {
    return <div>
      {product.isLoading && <h1>Loading...</h1>}
    </div>
  }

  if (product.error) {
    return <div>
      <h1>Error {product.error.message}</h1>
    </div>
  }

  if (product.data) {
    const data = product.data.product

    function submit(evt: FormEvent<HTMLFormElement>) {
      evt.preventDefault()

      // @ts-ignore
      const nameField = evt.target["name"].value

      productUpdater.mutate({
        original: data,
        patched: {
          name: nameField
        }
      })
      console.log("Submit")
    }

    return (
      <div>
        <form onSubmit={submit} autoComplete="off">
          <h1>From state: {product.data.product.name}</h1>

          <h1>Edit product</h1>
          {productUpdater.error &&
            <h1 onClick={() => productUpdater.reset()}>
              {productUpdater.error.message}
            </h1>
          }


          <h1>{data.id}</h1>

          <input defaultValue={data.name} name="name" />

          <button type="submit">Update</button>
          <button type="reset">Reset</button>
        </form>
      </div>
    )
  }
}
