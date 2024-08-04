import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { FormEvent, useEffect, useState } from "react"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { hasDifferentValue, useModel } from "~/hooks/useModel"
import { sessionProtectedLoader } from "~/session.server"

export const loader = async (loader: LoaderFunctionArgs) => {
  await sessionProtectedLoader(loader)
  const { params, context: { cloudflare } } = loader

  return json({
    catalogId: params.id,
    catalogRoute: cloudflare.env.CATALOGS_ROUTE
  })
}

type Catalog = { headline: string, id: string }

export default function AdminCatalogsById() {
  const loaderData = useLoaderData<typeof loader>()
  if (!loaderData.catalogId || !loaderData.catalogRoute) {
    return <div>Not found catalog id or route</div>
  }

  const { fetch } = useAuthFetch()
  const { model, updater } = useModel<Catalog>({
    id: loaderData.catalogId,
    key: ["catalog", { id: loaderData.catalogId }],
    route: loaderData.catalogRoute,
    fetch,
  })

  const [data, setData] = useState<{ catalog: Catalog } | null>(null)

  useEffect(() => {
    if (!model.data) return

    (async () => {
      const result = await model.data.json<{ catalog: Catalog }>()

      if (data != null && (!hasDifferentValue(data.catalog, result.catalog)))
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

  if (data && data.catalog) {

    function submit(evt: FormEvent<HTMLFormElement>) {
      evt.preventDefault()

      // @ts-ignore
      const headline = evt.target["headline"].value

      if (!data?.catalog) {
        throw new Error("Original product newer must be null")
      }

      updater.mutate({
        model: data.catalog,
        mutated: {
          headline: headline,
        }
      })

      console.log("Submit")
    }

    return (
      <div>
        <form onSubmit={submit} autoComplete="off">
          <h1>From state: {data.catalog.headline}</h1>

          <h1>Edit catalog</h1>
          {updater.error &&
            <h1 onClick={() => updater.reset()}>
              {updater.error.message}
            </h1>
          }

          <h1>{data.catalog.id}</h1>

          <input defaultValue={data.catalog.headline} name="headline" />

          <button type="submit">Update</button>
          <button type="reset">Reset</button>
        </form>
      </div>
    )
  }
}

