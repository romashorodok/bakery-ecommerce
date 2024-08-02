import { Card, CardBody, CardFooter, Image, Stack, Heading, Text, Divider, ButtonGroup, Button } from '@chakra-ui/react'

type Product = { id: string, name: string }

export default function({ id, name }: Product) {
  return (
    <Card maxW='sm'>
      <CardBody>
        <Image
          src='/sample.webp'
          alt='Green double couch with wooden legs'
          borderRadius='lg'
        />
        <Stack mt='4' spacing='2'>
          <Heading size='md'>{name}</Heading>
          <Text>{id}</Text>
          <Text color='blue.600' fontSize='2xl'>
            $450
          </Text>
        </Stack>
      </CardBody>
      <CardFooter>
        <ButtonGroup>
          <Button variant='ghost' colorScheme='blue'>
            Add to cart
          </Button>
        </ButtonGroup>
      </CardFooter>
    </Card>
  )
}
