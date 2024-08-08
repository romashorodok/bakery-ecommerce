import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { AspectRatio } from "~/components/ui/aspect-ratio"

type Product = { id: string, name: string }

export default function ({ id, name }: Product) {
  return (
    <Card x-chunk="dashboard-01-chunk-0 z-10">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-medium">
          {name}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">$45</div>

        <AspectRatio ratio={16 / 9} className="bg-muted">
          <img src='/sample.webp' className="rounded-md object-cover w-full h-full" />
        </AspectRatio>

        <p className="text-xs text-muted-foreground">
          {id}
        </p>
      </CardContent>
    </Card>
  )
  // return (
  //   <Card maxW='sm'>
  //     <CardBody>
  //       <Image
  //         src='/sample.webp'
  //         alt='Green double couch with wooden legs'
  //         borderRadius='lg'
  //       />
  //       <Stack mt='4' spacing='2'>
  //         <Heading size='md'>{name}</Heading>
  //         <Text>{id}</Text>
  //         <Text color='blue.600' fontSize='2xl'>
  //           $450
  //         </Text>
  //       </Stack>
  //     </CardBody>
  //     <CardFooter>
  //       <ButtonGroup>
  //         <Button variant='ghost' colorScheme='blue'>
  //           Add to cart
  //         </Button>
  //       </ButtonGroup>
  //     </CardFooter>
  //   </Card>
  // )
}
