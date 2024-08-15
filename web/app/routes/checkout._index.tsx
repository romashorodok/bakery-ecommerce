import { useLoaderData } from '@remix-run/react';
import { LoaderFunctionArgs, json } from '@remix-run/cloudflare';
import { loadStripe } from '@stripe/stripe-js';
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthFetch } from '~/hooks/useAuthFetch';

export const loader = async ({ context: { cloudflare: { env } } }: LoaderFunctionArgs) => {
  return json({
    stripePubkey: env.STRIPE_PUBLIC_KEY,
    paymentRoute: env.PAYMENT_ROUTE,
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

export default function CheckoutIndex() {
  const { stripePubkey, paymentRoute } = useLoaderData<typeof loader>()
  const { } = useStripeSession({ paymentRoute })

  const stripe = useMemo(() => loadStripe(stripePubkey), [stripePubkey])

  return (
    <div>
      Checkout index
    </div>
  )
}
