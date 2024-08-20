import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { Link, useLoaderData, useNavigate } from "@remix-run/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { sessionProtectedLoader } from "~/session.server"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"
import {
  ChevronLeft,
  ChevronRight,
  Copy,
  CreditCard,
  File,
  Home,
  LineChart,
  ListFilter,
  MoreVertical,
  Package,
  Package2,
  PanelLeft,
  Search,
  Settings,
  ShoppingCart,
  Truck,
  Users2,
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"
import { AspectRatio } from "~/components/ui/aspect-ratio"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"
import {
  MoreHorizontal,
  PlusCircle,
} from "lucide-react"
import { Separator } from "~/components/ui/separator"
import { useResponsive } from "~/hooks/useResponsive"
import { cn } from "~/lib/utils"


export const loader = async (loader: LoaderFunctionArgs) => {
  await sessionProtectedLoader(loader)
  const { CART_ROUTE } = loader.context.cloudflare.env

  return json({
    cartsRoute: CART_ROUTE,
  })
}

type Product = { price: number, name: string, updated_at: string, created_at: string, id: string }
type CartItem = { cart_id: string, product_id: string, quantity: number, id: string, product: Product }
type Cart = { user_id: string, id: string, cart_items: Array<CartItem>, total_price: number }

function CartItemView({ cartsRoute, id, quantity, product_id, product: { name, price } }: CartItem & { cartsRoute: string }) {
  const { fetch } = useAuthFetch()
  const client = useQueryClient()

  const mutationDeleteCartItem = useMutation({
    mutationKey: ["cart-delete-item", product_id],
    mutationFn: async () => {
      const response = await fetch(`${cartsRoute}/cart-item/${product_id}`, {
        method: "DELETE",
      })
      if (!response || !response.ok) {
        throw new Error("Cart request error")
      }
      return response.json()
    },
    onSuccess: () => client.invalidateQueries({ queryKey: ["cart"] })
  })

  return (
    <Card key={id}>
      <CardHeader className="cursor-pointer">
        <CardTitle>{name}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableBody>
            <TableRow className="flex place-items-center hover:bg-transparent focus:outline-none">
              <TableCell className="flex-[1]">
                <AspectRatio ratio={16 / 9} className="bg-muted">
                  <img src='/sample.webp' className="rounded-md object-cover w-full h-full" />
                </AspectRatio>
              </TableCell>
              <TableCell className="flex-[1] sm:table-cell">
                <div className="flex gap-1 justify-end font-semibold">
                  <h1>{quantity}</h1>
                  <h1>x</h1>
                  <h1>${price}</h1>
                </div>
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      aria-haspopup="true"
                      size="icon"
                      variant="ghost"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">Toggle menu</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />

                    <DropdownMenuItem>Increase</DropdownMenuItem>
                    <DropdownMenuItem>Decrease</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => mutationDeleteCartItem.mutate()}>
                      Remove
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

export default function CartIndex() {
  const { mobile } = useResponsive()

  const { fetch } = useAuthFetch()
  const { cartsRoute } = useLoaderData<typeof loader>()

  const model = useQuery({
    queryKey: ["cart"],
    queryFn: async () => {
      const response = await fetch(cartsRoute, {
        method: "GET",
      })

      if (!response || !response.ok) {
        throw new Error("Cart request error")
      }

      return response.json<{ cart: Cart }>()
    }
  })

  if (model.data?.cart) {
    return (
      <div className={cn(
        "flex h-full min-h-full",
        `${mobile ? 'flex-col-reverse' : 'flex-row'}`
      )}>
        <div className={"flex-[2] flex flex-col gap-2 px-2 overflow-scroll"}>
          {model.data.cart.cart_items.map(i => <CartItemView key={i.id} cartsRoute={cartsRoute}  {...i} />)}
        </div>
        <div className="flex-[1]">
          <Card
            className="overflow-hidden" x-chunk="dashboard-05-chunk-4"
          >
            <CardHeader className="flex flex-row items-start bg-muted/50">
              <div className="grid gap-0.5">
                <CardTitle className="group flex items-center gap-2 text-lg"></CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-6 text-sm">
              <div className="grid gap-3">
                <div className="font-semibold">Order Details</div>
                <ul className="grid gap-3">
                  {model.data.cart.cart_items.map(item =>
                    <li key={item.id} className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        {item.product.name}
                      </span>
                      <span className="font-semibold"><span>{item.quantity}</span> x ${item.product.price}</span>
                    </li>
                  )}
                </ul>
                <Separator className="my-2" />
                <ul className="grid gap-3">
                  <li className="flex items-center justify-between">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>$0</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span className="text-muted-foreground">Shipping</span>
                    <span>$0</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span className="text-muted-foreground">Tax</span>
                    <span>$0</span>
                  </li>
                  <li className="flex items-center justify-between font-semibold">
                    <span className="text-muted-foreground">Total</span>
                    <span>${model.data.cart.total_price}</span>
                  </li>
                </ul>
              </div>
            </CardContent>
            <CardFooter className="flex flex-row border-t bg-muted/50 px-6 py-3">
              <Link to="/checkout">
                <Button className="w-full">Submit</Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    )
  }
}
