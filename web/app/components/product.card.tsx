import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { AspectRatio } from "~/components/ui/aspect-ratio"
import { PropsWithChildren } from "react"

type Image = { bucket: string, original_file: string, transcoded_file_mime: string, original_file_hash: string, transcoded_file: string, id: string }
type ProductImage = { product_id: string, image_id: string, featured: boolean, id: string, image: Image }
type Product = { id: string, name: string, price: number, product_images: Array<ProductImage> }

export default function({ id, name, debug, children, price, product_images, objectStoreRoute }: PropsWithChildren<Product & { debug: boolean, objectStoreRoute: string }>) {
  const featuredImage = product_images.find(image => image.featured);

  return (
    <Card x-chunk="dashboard-01-chunk-0 z-10">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-medium">
          {name}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <div className="text-2xl font-bold">{price}</div>

        <AspectRatio ratio={16 / 9} className="bg-muted">
          {featuredImage ?
            <img src={`${objectStoreRoute}/${featuredImage.image.bucket}/${featuredImage?.image.transcoded_file || featuredImage?.image.original_file}`} className="rounded-md object-cover w-full h-full" />
            : null
          }

        </AspectRatio>

        {debug &&
          <p className="text-xs text-muted-foreground">
            {id}
          </p>
        }
        <section className="self-end">
          {children}
        </section>
      </CardContent>
    </Card>
  )
}
