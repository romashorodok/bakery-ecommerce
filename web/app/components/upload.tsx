import { createRef, FormEvent, useCallback, useState } from "react";

import PNG from "~/lib/blockhash/third_party/png_js/png"
import { decode as JPEGDecoder } from "~/lib/blockhash/third_party/jpeg_js/decoder"
import { blockhashData } from "~/lib/blockhash/blockhash"

import { Button } from "~/components/ui/button"
import { useAuthFetch } from "~/hooks/useAuthFetch";
import { useMutation } from "@tanstack/react-query";

type ImageData = { width: number, height: number, data: Uint8Array }

async function imageHash(image: File) {
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
  return blockhashData(imageData, 16, 2);
}

// async function sha256FromFile(file: File) {
//   const arrayBuffer = await file.arrayBuffer();
//   const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
//   const hashArray = Array.from(new Uint8Array(hashBuffer));
//   const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
//   return hashHex;
// }

export function FileUploader({ product_id, imageRoute }: { product_id: string, imageRoute: string }) {
  const imageRef = createRef<HTMLImageElement>()
  const [image, setImage] = useState<File | undefined>()
  const { fetch } = useAuthFetch()

  const mutationUpload = useMutation({
    mutationKey: ["file-uploader"],
    mutationFn: async (image_hash: string) => {
      let response = await fetch(imageRoute, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          image_hash,
        })
      })
      if (!response || !response.ok)
        throw new Error("Something goes wrong...")
      const result = await response.json<{ image: { upload_url: string, id: string } }>()
      await window.fetch(result.image.upload_url, {
        method: "PUT",
        body: image,
      })
      response = await fetch(`${imageRoute}/${result.image.id}/submit`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          image_hash,
          product_id,
        })
      })
      return { success: true }
    }
  })

  async function uploadImage(evt: FormEvent<HTMLFormElement>) {
    evt.preventDefault()
    try {
      if (!image) throw new Error("Select image first")
      const image_hash = await imageHash(image)
      if (!image_hash) throw new Error("Unable get image hash")
      await mutationUpload.mutateAsync(image_hash)
      console.log("successfully uploaded image")
    } catch (e) {
      console.error("Unable get image hash. Use png or jpeg image", e)
    }
  }

  function onChange(evt: FormEvent<HTMLFormElement>) {
    evt.preventDefault()
    if (!imageRef.current) return
    const input = evt.target as HTMLInputElement
    if (!input.files) return
    const image = input.files[0]
    if (!image) return
    imageRef.current.src = URL.createObjectURL(image)
    setImage(image)
  }

  return (
    <form onSubmit={uploadImage} onChange={onChange}>
      <img className="w-[300px] h-[300px]" ref={imageRef} />

      <input type="file" name="image" accept="image/png,image/jpeg" />
      <Button type="submit">
        Change image
      </Button>
    </form>
  )
}
