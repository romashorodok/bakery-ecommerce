import { useLoaderData } from '@remix-run/react';
import { LoaderFunctionArgs, json } from '@remix-run/cloudflare';
import { loadStripe } from '@stripe/stripe-js';
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthFetch } from '~/hooks/useAuthFetch';

import { Label } from "~/components/ui/label"
import { RadioGroup, RadioGroupItem } from "~/components/ui/radio-group"

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

type Order = {
  id: string,
  payment_detail_id: string,
  user_id: string,
  order_status: string,
  payment_detail: PaymentDetail,
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
    onSuccess: () => client.invalidateQueries({ queryKey: [ORDER_DRAFT_SESSION] })
  })

  return { model, mutatePaymentMethod }
}

export default function CheckoutIndex() {
  const { stripePubkey, paymentRoute, orderRoute } = useLoaderData<typeof loader>()

  const { model, mutatePaymentMethod } = useOrderSession({ orderRoute })

  const [provider, setProvider] = useState<PAYMENT_PROVIDER_KEY | undefined>()

  useEffect(() => {
    if (!provider) return
    mutatePaymentMethod.mutate(provider)
  }, [provider])

  useEffect(() => {
    console.log("order model", model.data)
  }, [model.data])

  // const { } = useStripeSession({ paymentRoute })
  //

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
        <RadioGroup value={model.data?.order.payment_detail.payment_provider} onValueChange={(e) => setProvider(e as PAYMENT_PROVIDER_KEY)} >
          {Object.keys(PAYMENT_PROVIDER).map(item =>
            <div key={`radio-group-${item}`} className="flex items-center space-x-2">
              <RadioGroupItem value={item} id={item} />
              <Label htmlFor={item}>{item}</Label>
            </div>
          )}
        </RadioGroup>
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
