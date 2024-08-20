import { LoaderFunctionArgs, json } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { useQuery } from "@tanstack/react-query"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { AspectRatio } from "~/components/ui/aspect-ratio"
import {
  MoreHorizontal,
  PlusCircle,
} from "lucide-react"

import { Button } from "~/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table"

export const loader = async (params: LoaderFunctionArgs) => {
  const { context: { cloudflare: { env } } } = params

  return json({
    ordersRoute: env.ORDER_ROUTE,
  })
}

type PaymentDetail = {
  id: string,
  payment_provider: string
}

type Product = { price: number, name: string, updated_at: string, created_at: string, id: string }

type OrderItem = {
  order_id: string,
  product_id: string,
  quantity: number,
  id: string,
  price: number,
  price_multiplied: number,
  price_multiplier: number,
  product: Product,
}

type Order = {
  id: string,
  payment_detail_id: string,
  user_id: string,
  order_status: string,
  payment_detail: PaymentDetail,
  order_items: Array<OrderItem>
}

function useUserOrders({ ordersRoute }: { ordersRoute: string }) {
  const { fetch } = useAuthFetch()

  const model = useQuery({
    queryKey: ["user-orders"],
    queryFn: async () => {
      const request = await fetch(`${ordersRoute}/user`, {
        method: "GET",
      })
      if (!request || !request.ok)
        throw new Error("Something goes wrong...")
      return await request.json<{ orders: Array<Order> }>()
    }
  })

  return { model }
}

export default function OrdersIndex() {
  const { ordersRoute } = useLoaderData<typeof loader>()
  const { model } = useUserOrders({ ordersRoute })

  if (model.isLoading) {
    return <div>
      {model.isLoading && <h1>Loading...</h1>}
    </div>
  }

  if (model.error) {
    return <div>
      <h1>Error {model.error.message}</h1>
    </div>
  }

  if (model.data?.orders) {
    return (
      <Card x-chunk="dashboard-06-chunk-0">
        <CardHeader>
          <CardTitle>Orders</CardTitle>
          <CardDescription>
            Manage your orders.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="hidden w-[150px] sm:table-cell">
                  <span className="sr-only">id</span>
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>
                  <span className="sr-only">Actions</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {model.data.orders.map(item => (
                <TableRow key={item.id}>
                  <TableCell className="hidden sm:table-cell">
                    <h1 className="text-xs">{item.id}</h1>
                  </TableCell>
                  <TableCell className="sm:table-cell">
                    {item.order_status}
                  </TableCell>
                  <TableCell>
                    {item.order_items.map(item =>
                      <li key={item.id} className="flex items-center justify-between">
                        <span className="text-muted-foreground">
                          {item.product.name}
                        </span>
                        <span className="font-semibold">
                          <span>{item.quantity}</span> x ${item.price}</span>
                      </li>
                    )}
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
                        <DropdownMenuItem>Detail</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}

            </TableBody>
          </Table>
        </CardContent>
      </Card>
    )
  }
}
