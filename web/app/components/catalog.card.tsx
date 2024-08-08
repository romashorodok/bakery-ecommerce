import ProductCard from "./product.card"

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

export default function({ position, available, visible, catalog_id, id, product_id, product }: CatalogItem) {
  return (
    <div key={id}>
      <h1>Catalog Item - {id}</h1>

      <h1>CatalogId: {catalog_id}</h1>
      <h1>ProductId: {product_id ? product_id : 'null'}</h1>
      <h1>Position: {position}</h1>
      <h1>Available: {available ? "Available" : "not available"}</h1>
      <h1>visible: {visible ? "Visible" : "not visible"}</h1>

      {product && <ProductCard {...product} />}
    </div>
  )
}
