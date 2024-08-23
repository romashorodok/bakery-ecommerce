import ProductCard from "./product.card"

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

type CatalogItem = {
  available: boolean,
  visible: boolean,
  position: number,
  catalog_id: string,
  product_id: string | null,
  id: string
  product: Product | null
}

export default function({ position, available, visible, catalog_id, id, product_id, product, debug, children, objectStoreRoute }: PropsWithChildren<CatalogItem & { debug: boolean, objectStoreRoute: string }>) {
  return (
    <div key={id}>
      {debug &&
        <div>
          <h1>Catalog Item - {id}</h1>
          <h1>CatalogId: {catalog_id}</h1>
          <h1>ProductId: {product_id ? product_id : 'null'}</h1>
          <h1>Position: {position}</h1>
          <h1>Available: {available ? "Available" : "not available"}</h1>
          <h1>visible: {visible ? "Visible" : "not visible"}</h1>
        </div>
      }
      {product
        ? (
          <ProductCard debug={debug} objectStoreRoute={objectStoreRoute}  {...product}>{children}</ProductCard>
        )
        : <Card x-chunk="dashboard-01-chunk-0 z-10">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xl font-medium">
              Placeholder
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$0</div>

            <AspectRatio ratio={16 / 9} className="bg-muted" />

            {debug &&
              <p className="text-xs text-muted-foreground">
                {id}
              </p>
            }
          </CardContent>
        </Card>
      }
    </div>
  )
}
