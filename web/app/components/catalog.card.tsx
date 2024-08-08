import ProductCard from "./product.card"

import { Card, CardBody, CardFooter, Image, Stack, Heading, Text, Divider, ButtonGroup, Button } from '@chakra-ui/react'

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

export default function({ position, available, visible, catalog_id, id, product_id, product, debug }: CatalogItem & { debug: boolean }) {
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
        ? <ProductCard {...product} />
        : <Card maxW='sm'>
          <CardBody>
            <Image src='' borderRadius='lg' />
            <Stack mt='4' spacing='2'>
              <Heading size='md'>Placeholder</Heading>
            </Stack>
          </CardBody>
        </Card>
      }
    </div>
  )
}
