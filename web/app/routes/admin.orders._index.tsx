import { json, LoaderFunctionArgs } from "@remix-run/cloudflare"
import { useLoaderData } from "@remix-run/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { useAuthFetch } from "~/hooks/useAuthFetch"
import { sessionProtectedLoader } from "~/session.server"
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
import {
  MoreHorizontal,
  PlusCircle,
} from "lucide-react"
import { Separator } from "~/components/ui/separator"

export const loader = async (params: LoaderFunctionArgs) => {
  await sessionProtectedLoader(params)
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
  order_status: string,
  payment_detail: PaymentDetail,
  order_items: Array<OrderItem>
  amount: number
}

type Customer = { last_name: string, first_name: string, email: string }

type Orders = Array<{ order: Order, customer: Customer }>

function useOrders({ ordersRoute, page }: { page: number, ordersRoute: string }) {
  const { fetch } = useAuthFetch()

  const model = useQuery({
    queryKey: ["orders", page],
    queryFn: async () => {
      const request = await fetch(`${ordersRoute}?page=${page}`)
      if (!request || !request.ok)
        throw new Error("Something goes wrong...")
      return request.json<{ orders: Orders }>()
    }
  })

  return { model }
}

export default function AdminOrders() {
  const { ordersRoute } = useLoaderData<typeof loader>()

  const [page, setPage] = useState<number>(1)

  const { model } = useOrders({ ordersRoute, page })


  if (!model.data?.orders) {
    return <div>Not found orders</div>
  }

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
              <TableHead>Customer</TableHead>
              <TableHead>Items</TableHead>
              <TableHead>
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {model.data.orders.map(({ order, customer }) => (
              <TableRow key={order.id}>
                <TableCell className="hidden sm:table-cell">
                  <h1 className="text-xs">{order.id}</h1>
                </TableCell>
                <TableCell className="sm:table-cell">
                  {order.order_status}
                </TableCell>
                <TableCell>
                  <h1>{customer.first_name}</h1>
                  <h1>{customer.last_name}</h1>
                  <h1>{customer.email}</h1>
                </TableCell>
                <TableCell>
                  {order.order_items.map(item =>
                    <li key={item.id} className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        {item.product.name}
                      </span>
                      <span className="font-semibold">
                        <span>{item.quantity}</span> x ${item.price}</span>
                    </li>
                  )}
                  <div>
                    <Separator />
                    <h2 className="font-semibold flex justify-end">
                      ${order.amount}
                    </h2>
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
