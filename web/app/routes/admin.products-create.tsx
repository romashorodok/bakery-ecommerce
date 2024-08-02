import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { FormEvent } from "react"
import { useAuthFetch } from "~/hooks/useAuthFetch"

export const loader = async ({ context: { cloudflare } }: LoaderFunctionArgs) => {
  return json({
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
  })
}

export default function AdminProductsCreate() {
  const loaderData = useLoaderData<typeof loader>()
  const { fetch } = useAuthFetch()

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    // @ts-ignore
    const field = e.target["name"].value

    const result = await fetch(loaderData.productsRoute, {
      headers: {
        "content-type": "application/json",
      },
      method: "POST",
      body: JSON.stringify({ name: field })

    })

    console.log(result)
  }

  return (
    <div>
      <form onSubmit={submit} autoComplete="off">
        <input name="name" />

        <button type="submit">Create</button>
      </form>
    </div>
  )
}
