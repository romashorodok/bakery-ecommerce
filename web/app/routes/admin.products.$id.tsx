import { useLoaderData } from "@remix-run/react"
import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { sessionProtectedLoader } from "~/session.server"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { hasDifferentValue, useModel } from "~/hooks/useModel"
import { createRef, FormEvent, useEffect, useState } from "react"
import { Button } from "~/components/ui/button"
import PNG from "~/lib/blockhash/third_party/png_js/png"
import { decode as JPEGDecoder } from "~/lib/blockhash/third_party/jpeg_js/decoder"
import { blockhashData } from "~/lib/blockhash/blockhash"

export const loader = async (loader: LoaderFunctionArgs) => {
  await sessionProtectedLoader(loader)
  const { params, context: { cloudflare } } = loader

  return json({
    productId: params.id,
    productsRoute: cloudflare.env.PRODUCTS_ROUTE,
  })
}

type Product = { id: string, name: string, price: number }

type ImageData = { width: number, height: number, data: Uint8Array }

function FileUploader() {

  const imageCanvas = createRef<HTMLCanvasElement>()
  const imageRef = createRef<HTMLImageElement>()

  function uploadImage(evt: FormEvent<HTMLFormElement>) {
    evt.preventDefault()
    console.log(evt)
  }

  async function imageHash(evt: FormEvent<HTMLFormElement>) {
    evt.preventDefault()
    const input = evt.target as HTMLInputElement
    if (!input.files) return
    const image = input.files[0]
    if (!image) return
    const mime = image.type

    const buf = await image.arrayBuffer()
    let imageData: ImageData

    try {
      switch (mime) {
        case "image/png":
          const png = new PNG(new Uint8Array(buf))
          imageData = {
            width: png.width,
            height: png.height,
            data: png.decodePixels(),
          }
          break
        case "image/jpeg":
          imageData = JPEGDecoder(buf, {
            useTArray: true,
            tolerantDecoding: false,
          })
          break
        default:
          throw new Error("Unknown mime type")
      }
    } catch (e) {
      console.error("Unable upload image. Err:", e)
      return
    }

    const hash = blockhashData(imageData, 16, 2);
    console.log(hash)

    // const canvas = imageCanvas.current
    // if (!canvas) throw new Error("Not found canvas element")
    //
    // const context = canvas.getContext('2d');
    // if (context) {
    //   canvas.width = png.width;
    //   canvas.height = png.height;
    //
    //   // Render the PNG onto the canvas
    //   png.render(canvas);
    //
    //   const imageSrc = imageRef.current
    //   if (!imageSrc) return
    //   imageSrc.src = canvas.toDataURL()
    // }

  }

  return (
    <form onChange={imageHash}>
      <img className="w-[300px] h-[300px]" ref={imageRef} />

      <input type="file" name="image" accept="image/png,image/jpeg" />
      <Button type="submit">
        Change image
      </Button>
      <canvas ref={imageCanvas} ></canvas>
    </form>
  )
}

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
        <FileUploader />
      </div>
    )
  }
}
