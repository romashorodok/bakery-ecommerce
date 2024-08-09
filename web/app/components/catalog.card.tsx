import ProductCard from "./product.card"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { AspectRatio } from "~/components/ui/aspect-ratio"

type Product = { id: string, name: string }

type CatalogItem = {
  available: boolean,
  visible: boolean,
  position: number,
  catalog_id: string,
  product_id: string | null,
  id: string
  product: Product | null
}

export default function ({ position, available, visible, catalog_id, id, product_id, product, debug }: CatalogItem & { debug: boolean }) {
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
        ? <ProductCard debug={debug} {...product} />
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
