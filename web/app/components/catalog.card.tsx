
type CatalogItem = {
  available: boolean,
  visible: boolean,
  position: number,
  catalog_id: string,
  id: string
}

export default function ({ position, available, visible, catalog_id, id }: CatalogItem) {
  return (
    <div key={id}>
      <h1>Catalog Item - {id}</h1>

      <h1>CatalogId: {catalog_id}</h1>
      <h1>Position: {position}</h1>
      <h1>Available: {available ? "Available" : "not available"}</h1>
      <h1>visible: {visible ? "Visible" : "not visible"}</h1>
    </div>
  )
}
