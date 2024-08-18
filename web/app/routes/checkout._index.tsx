import { useLoaderData } from '@remix-run/react';
import { LoaderFunctionArgs, json } from '@remix-run/cloudflare';
import { loadStripe } from '@stripe/stripe-js';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthFetch } from '~/hooks/useAuthFetch';

import { Label } from "~/components/ui/label"
import { RadioGroup, RadioGroupItem } from "~/components/ui/radio-group"
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
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import {
  MoreHorizontal,
  PlusCircle,
} from "lucide-react"

export const loader = async ({ context: { cloudflare: { env } } }: LoaderFunctionArgs) => {
  return json({
    stripePubkey: env.STRIPE_PUBLIC_KEY,
    paymentRoute: env.PAYMENT_ROUTE,
    orderRoute: env.ORDER_ROUTE,
  })
}

function useStripeSession({ paymentRoute }: { paymentRoute: string }) {
  const { fetch } = useAuthFetch()

  const model = useQuery({
    queryKey: ["stripe-client-secret"],
    queryFn: async () => {
      const response = await fetch(`${paymentRoute}/stripe/payment-intent`, {
        method: "POST",
      })
    }
  })

  return {}
}

function StripeCheckout({ paymentRoute, stripePubkey }: { stripePubkey: string, paymentRoute: string }) {
  // const { } = useStripeSession({ paymentRoute })

  // const stripe = useMemo(() => loadStripe(stripePubkey), [stripePubkey])

  return <div>Stripe checkout</div>
}


const PAYMENT_PROVIDER = {
  STRIPE: "STRIPE",
  PAYPAL: "PAYPAL"
} as const

type PAYMENT_PROVIDER_KEY = keyof typeof PAYMENT_PROVIDER

type PaymentDetail = {
  id: string,
  payment_provider: PAYMENT_PROVIDER_KEY
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

function OrderItemView({ id, quantity, price, product: { name } }: OrderItem) {
  return (
    <Card key={id} className="w-[400px]">
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
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

const ORDER_DRAFT_SESSION = "order-draft-session"

function useOrderSession({ orderRoute }: { orderRoute: string }) {
  const { fetch } = useAuthFetch()
  const client = useQueryClient()

  const model = useQuery({
    queryKey: [ORDER_DRAFT_SESSION],
    queryFn: async () => {
      const response = await fetch(`${orderRoute}/draft`, {
        method: "GET",
      })
      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }
      return await response.json<{ order: Order }>()
    }
  })

  const cartConversationToOrder = useMutation({
    mutationKey: ["order-draft-cart-conversation-to-order"],
    mutationFn: async () => {
      const response = await fetch(`${orderRoute}/draft/convert-cart-to-order`, {
        method: "PUT",
        headers: {
          "content-type": "application/json",
        },
      })
      if (!response || !response.ok) {
        throw new Error('Something goes wrong at cart conversation...')
      }
      return response.json()
    },
    onSuccess: () => client.invalidateQueries({ queryKey: [ORDER_DRAFT_SESSION] })
  })

  const mutatePaymentMethod = useMutation({
    mutationKey: ["order-draft-payment-method"],
    mutationFn: async (provider: PAYMENT_PROVIDER_KEY) => {
      const response = await fetch(`${orderRoute}/draft/payment-method`, {
        method: "PUT",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({ provider })
      })
      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }
      return response.json<{ payment_detail: string }>()
    },
    onSuccess: () => cartConversationToOrder.mutate()
  })


  return { model, mutatePaymentMethod }
}
// convert-cart-to-order

export default function CheckoutIndex() {
  const { stripePubkey, paymentRoute, orderRoute } = useLoaderData<typeof loader>()

  const { model, mutatePaymentMethod } = useOrderSession({ orderRoute })

  const [provider, setProvider] = useState<PAYMENT_PROVIDER_KEY | undefined>()

  useEffect(() => {
    if (!provider) return
    mutatePaymentMethod.mutate(provider)
  }, [provider])

  if (model.isLoading) {
    return (
      <div>
        <h1>Loading...</h1>
      </div>
    )
  }

  if (model.data?.order) {
    return (
      <div>
        <h1>{JSON.stringify(model.data?.order)}</h1>
        <RadioGroup onValueChange={(e) => setProvider(e as PAYMENT_PROVIDER_KEY)} >
          {Object.keys(PAYMENT_PROVIDER).map(item =>
            <div key={`radio-group-${item}`} className="flex items-center space-x-1">
              <RadioGroupItem className="w-[24px] h-[24px]" value={item} id={item} />
              <Label htmlFor={item}>{item}</Label>
            </div>
          )}
        </RadioGroup>
        {provider &&
          <section>
            {model.data.order.order_items && model.data.order.order_items.length > 0
              ? <div>{model.data.order.order_items.map(OrderItemView)}</div>
              : <h1>Not found items. Add items to cart first!</h1>
            }
          </section>
        }
      </div>
    )
  }
}

// {PAYMENT_PROVIDER.STRIPE == provider &&
//   <StripeCheckout stripePubkey={stripePubkey} paymentRoute={paymentRoute} />
// }
// {PAYMENT_PROVIDER.PAYPAL == provider &&
//   <div>paypal not supported</div>
// }
